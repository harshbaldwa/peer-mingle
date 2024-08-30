from django.contrib.auth.models import (AbstractUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .scripts import names, submissions, feedbacks, roster, gradebook
import os

SEMESTER_CHOICES = (
    ("Fall", "Fall"),
    ("Spring", "Spring"),
    ("Summer", "Summer"),
)


# GT User Manager
class GTUserManager(BaseUserManager):
    def create_user(self, username, email, first_name, last_name,
                    is_student, assign_feedbacks, gt_id, password):
        if not username:
            raise ValueError("Users must have a username")
        if not email:
            raise ValueError("Users must have an email address")
        if not first_name:
            raise ValueError("Users must have a first name")
        if not last_name:
            raise ValueError("Users must have a last name")
        if not gt_id:
            raise ValueError("Users must have a GT ID")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            is_student=is_student,
            assign_feedbacks=assign_feedbacks,
            gt_id=gt_id,
            password=password,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, username, email, first_name, last_name,
                         is_student, gt_id, password):
        user = self.create_user(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            is_student=is_student,
            assign_feedbacks=False,
            gt_id=gt_id,
            password=password,
        )
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, first_name, last_name,
                         is_student, gt_id, password):
        user = self.create_user(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            is_student=is_student,
            assign_feedbacks=False,
            gt_id=gt_id,
            password=password,
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class GTUser(AbstractUser, PermissionsMixin):
    username = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    is_student = models.BooleanField(default=True)
    assign_feedbacks = models.BooleanField(default=False)
    gt_id = models.CharField(max_length=9, unique=True)
    should_change_password = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = GTUserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email", "first_name",
                       "last_name", "is_student", "gt_id"]

    def __str__(self):
        return self.username

    def get_random_name(self):
        return names.get_random_name()


class Course(models.Model):
    slug = models.SlugField(max_length=100, unique=True, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    year = models.IntegerField()
    instructor = models.ManyToManyField(
        GTUser, related_name="course-instructor+", blank=True)
    teaching_assistants = models.ManyToManyField(
        GTUser, related_name="course-teaching-assistant+", blank=True)
    students = models.ManyToManyField(
        GTUser, related_name="course-students+", blank=True)

    roster = models.FileField(upload_to="")
    gradebook = models.FileField(upload_to="")

    def save(self, *args, **kwargs):
        self.slug = slugify(f"{self.code}-{self.semester}-{self.year}")
        path = f"courses/{self.slug}/"
        # only do the following steps if the course is being created
        if self.roster and not os.path.exists(self.roster.path):
            roster_path = path + f"roster-{os.urandom(12).hex()}/"
            self.roster.name = roster_path + "roster.xlsx"
        if self.gradebook and not os.path.exists(self.gradebook.path):
            gradebook_path = path + f"gradebook-{os.urandom(12).hex()}/"
            self.gradebook.name = gradebook_path + "gradebook.csv"
        super().save(*args, **kwargs)

    def create_roster_gradebook(self):
        if self.roster:
            roster.create_roster(self.roster.path, GTUser, self)
        if self.gradebook:
            gradebook.create_gradebook(self.gradebook.path)

    @property
    def get_absolute_url(self):
        return reverse("course", kwargs={"slug": self.slug})

    def who_has_access(self, user):
        return user in self.instructor.all() or \
            user in self.teaching_assistants.all() or \
            user in self.students.all() or \
            user.is_superuser

    def __str__(self):
        return f"{self.code} - {self.semester} {self.year} - {self.name}"

    class Meta:
        ordering = ["name"]


class Assignment(models.Model):
    slug = models.SlugField(max_length=100, unique=False, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    course = models.ForeignKey(
        "Course", on_delete=models.CASCADE, related_name="assignments"
    )
    num_reviewers = models.IntegerField(default=3)
    out_of = models.IntegerField(default=4)
    reviewing_type_anonymous = models.BooleanField(default=False)
    gradescope_submissions = models.FileField(upload_to="", blank=True)
    due_date = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(default=False, editable=False)
    gradebook = models.FileField(
        upload_to="", blank=True, max_length=200)

    def __str__(self):
        return self.name + " - " + self.course.code

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        path = f"courses/{self.course.slug}/assignments/{self.slug}/"
        if self.gradescope_submissions:
            self.gradescope_submissions.name = path + "gradescope.zip"
        super().save(*args, **kwargs)

    def make_submissions(self):
        submissions.create_submissions(
            self.gradescope_submissions.path, GTUser, self, Submission
        )

    def create_feedbacks(self):
        feedbacks.create_feedbacks(self, GTUser, Submission, Feedback)

    def create_gradebook(self):
        if self.feedback.filter(graded=False).exists():
            return False
        gradebook.create_assignment_gradebook(self)
        return True

    def who_has_access(self, user):
        return self.course.who_has_access(user)

    class Meta:
        ordering = ["-due_date"]

    @property
    def get_absolute_url(self):
        return reverse("assignment", kwargs={
            "slug": self.course.slug, "id": self.id
        })


class Submission(models.Model):
    assignment = models.ForeignKey(
        "Assignment", on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        GTUser, on_delete=models.CASCADE, related_name="submissions"
    )
    file = models.FileField(upload_to="", blank=True)
    date = models.DateTimeField(blank=True, null=True)
    is_late = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        path = f"courses/{self.assignment.course.slug}/" \
            f"assignments/{self.assignment.slug}/"
        self.file.name = path + self.student.username + ".zip"
        super().save(*args, **kwargs)

    def assign_submissions(self):
        if self.student.feedback.filter(assignment=self.assignment).exists():
            return

        assignments_review = Submission.objects.filter(
            assignment=self.assignment, is_late=False
        ).exclude(student=self.student)
        reviewees = assignments_review.order_by(
            "?")[:self.assignment.num_reviewers]

        for reviewee in reviewees:
            Feedback.objects.create(
                assignment=self.assignment,
                submission=reviewee,
                reviewer=self.student
            )

    def __str__(self):
        return f"{self.student.username} - {self.assignment}"

    class Meta:
        ordering = ["assignment"]


class Feedback(models.Model):
    assignment = models.ForeignKey(
        "Assignment", on_delete=models.CASCADE, related_name="feedback"
    )
    submission = models.ForeignKey(
        "Submission", on_delete=models.CASCADE, related_name="feedback"
    )
    reviewer = models.ForeignKey(
        GTUser, on_delete=models.CASCADE, related_name="feedback"
    )
    issued = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    comment_TA = models.TextField(blank=True, null=True, default="")
    grade = models.IntegerField(blank=True, null=True, default=0)
    graded = models.BooleanField(default=False)
    created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.submission}"

    @property
    def get_absolute_url(self):
        return reverse("feedback", kwargs={
            "id": self.id
        })

    @property
    def student(self):
        return self.submission.student

    def who_has_access(self, user):
        return user == self.reviewer
