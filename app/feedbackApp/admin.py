import os
from datetime import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .forms import (CustomUserChangeForm,
                    CustomUserCreationForm, ExtendDeadlineForm)
from .models import Assignment, Course, Feedback, GTUser, Submission, Extension


class GTUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = GTUser
    list_display = ["email", "first_name", "gt_id",
                    "is_staff", "should_change_password"]
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("is_student", "gt_id")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("is_student", "gt_id")}),
    )
    ordering = ["email"]
    search_fields = ["email", "first_name", "gt_id"]
    actions = ["extend_deadline"]

    @admin.action(description="Extend deadline")
    def extend_deadline(self, request, queryset):
        if 'apply' in request.POST:
            assignment_id = request.POST["assignment"]
            extend_deadline = request.POST["extend_deadline"]
            assignment = Assignment.objects.get(id=assignment_id)
            for student in queryset:
                extension = Extension.objects.create(
                    assignment=assignment,
                    student=student,
                    date=make_aware(datetime.fromisoformat(extend_deadline))
                )
                extension.save()
            self.message_user(request, "Deadline extended successfully")

            return HttpResponseRedirect(request.get_full_path())

        form = ExtendDeadlineForm(initial={
            "_selected_action": queryset.values_list("id", flat=True)
        })

        return render(request, "admin/extend_deadline.html", {
            "form": form,
            "items": queryset
        })


class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "semester", "year", "passwords"]
    ordering = ["name"]
    search_fields = ["name", "code"]
    actions = ["create_roster"]

    @admin.display(description="Passwords")
    def passwords(self, obj):
        return format_html(
            '<a href="{0}" download="{1}">View</a>',
            obj.roster.url.replace("roster.xlsx", "initial_passwords.json"),
            "initial_passwords.json"
        )

    @admin.action(description="Create Roster and Gradebook")
    def create_roster(self, request, queryset):
        for course in queryset:
            course.create_roster_gradebook()
        self.message_user(request, "Roster(s) created successfully")


class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["name", "course", "issue_status_view",
                    "grading_link", "graded_status_view", "gradebook_view"]
    ordering = ["name"]
    actions = ["make_submissions_and_create_feedbacks", "create_gradebook"]

    @admin.display(description="Issuing Status", boolean=True)
    def issue_status_view(self, obj):
        last_date = obj.real_due_date
        extensions = Extension.objects.filter(assignment=obj)
        late_dates = [extension.date for extension in extensions]
        if late_dates:
            last_date = max(*late_dates, last_date)

        if timezone.now() > last_date:
            obj.issue_status = True
            obj.save()
        else:
            obj.issue_status = False
            obj.save()

        return obj.issue_status

    @admin.display(description="Graded Status", boolean=True)
    def graded_status_view(self, obj):
        # get all feedbacks for this assignment
        # assignment has no property feedbacks
        feedbacks = Feedback.objects.filter(
            assignment=obj, issued=True, graded=False)
        feedbacks_issued = Feedback.objects.filter(
            assignment=obj, issued=True)
        if feedbacks.count() == 0 and feedbacks_issued.count() != 0:
            obj.graded_status = True
            obj.save()
        return obj.graded_status

    @admin.display(description="Gradebook")
    def gradebook_view(self, obj):
        # if no gradebook is created
        if not obj.gradebook:
            return "Not created yet"
        return format_html(
            '<a href="{0}" download="{1}">View</a>',
            obj.gradebook.url, os.path.basename(obj.gradebook.name)
        )

    @admin.display(description="Grading Link")
    def grading_link(self, obj):
        return format_html(
            '<a href="/grade/{0}">Grade</a>', obj.grading_secret
        )

    @admin.action(description="Make submissions and create feedbacks")
    def make_submissions_and_create_feedbacks(self, request, queryset):
        for assignment in queryset:
            assignment.make_submissions()
            assignment.create_feedbacks()
        self.message_user(
            request, "Submission(s) and Feedback(s) created successfully")

    @admin.action(description="Create gradebook")
    def create_gradebook(self, request, queryset):
        for assignment in queryset:
            status = assignment.create_gradebook()
            if status:
                messages.add_message(
                    request, messages.SUCCESS,
                    f"Gradebook for {assignment} created successfully"
                )
            else:
                messages.add_message(request, messages.ERROR,
                                     f"{assignment} not graded yet")


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["assignment", "student", "is_late"]
    ordering = ["assignment", "student"]
    actions = ["assign_submissions"]
    list_filter = ["is_late", "assignment"]

    @admin.action(description="Assign submissions for review")
    def assign_submissions(self, request, queryset):
        for submission in queryset:
            submission.assign_submissions()
        self.message_user(request, "Submission(s) assigned successfully")


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["assignment", "student", "reviewer", "issued", "graded"]
    list_filter = ["assignment", "graded"]
    search_fields = ["submission__student__username", "reviewer__username"]


class ExtensionAdmin(admin.ModelAdmin):
    list_display = ["assignment", "student", "date"]
    ordering = ["assignment", "student"]
    list_filter = ["assignment", "student"]


# Register your models here.
admin.site.register(Course, CourseAdmin)
admin.site.register(GTUser, GTUserAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Extension, ExtensionAdmin)
