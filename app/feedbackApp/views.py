from .forms import CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.shortcuts import redirect, render

from .models import Assignment, Course, Feedback, Submission, Extension


@login_required
def change_password(request, first_time=False):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            request.user.should_change_password = False
            request.user.save()
            # Redirect to a relevant page after password change
            return redirect('courses')
        else:
            return render(request, 'registration/change_password.html', {
                'form': form,
                'first_time': first_time
            })
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'registration/change_password.html', {
        'form': form,
        'first_time': first_time
    })


@login_required
def course_list(request):
    if request.user.should_change_password:
        return redirect("change_password_first", first_time=True)
    courses = Course.objects.filter(students=request.user)
    return render(request, "courses.html", {"courses": courses})


@login_required
def course_view(request, slug):
    course = Course.objects.get(slug=slug)
    if not course.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this course."
        })
    assignments = course.assignments.all()
    # check if the user submitted this assignment
    for assignment in assignments:
        try:
            submission = Submission.objects.get(
                assignment=assignment, student=request.user)
            assignment.submitted = True
            assignment.is_late = submission.is_late
            # check if extension is granted
            try:
                extension = Extension.objects.get(
                    assignment=assignment, student=request.user)
                assignment.due_date = extension.date
                assignment.extension = True
            except Extension.DoesNotExist:
                assignment.extension = False
            # if deadline is passed let me know
            if assignment.real_due_date > timezone.now():
                pending_feedbacks_count = Feedback.objects.filter(
                    assignment=assignment,
                    reviewer=request.user,
                    issued=False).count()
                assignment.pending_feedbacks = pending_feedbacks_count
                assignment.deadline_passed = False
            else:
                assignment.pending_feedbacks = 0
                assignment.deadline_passed = True
        except Submission.DoesNotExist:
            assignment.submitted = False
    return render(request, "course_detail.html", {
        "course": course,
        "assignments": assignments
    })


@login_required
def assignment_view(request, slug, id):
    assignment = Assignment.objects.get(id=id)
    if not assignment.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this assignment."
        })
    submission_type = "Missing"
    try:
        submission = Submission.objects.get(
            assignment=assignment, student=request.user)
        if submission.is_late:
            submission_type = "Late"
        else:
            submission_type = "On Time"
    except Submission.DoesNotExist:
        submission = None
    feedbacks = Feedback.objects.filter(
        assignment=assignment, reviewer=request.user)
    pending_feedbacks = feedbacks.filter(issued=False)
    completed_feedbacks = feedbacks.filter(issued=True)
    comments = Feedback.objects.filter(submission=submission, issued=True)
    # check if extension is granted
    try:
        extension = Extension.objects.get(
            assignment=assignment, student=request.user)
        assignment.due_date = extension.date
        assignment.extension = True
    except Extension.DoesNotExist:
        assignment.extension = False
    assignment.due_date_passed = assignment.real_due_date < timezone.now()

    return render(request, "assignment_detail.html", {
        "assignment": assignment,
        "submission": submission,
        "pending_feedbacks": pending_feedbacks,
        "completed_feedbacks": completed_feedbacks,
        "comments": comments,
        "submission_type": submission_type
    })


@login_required
def feedback_view(request, id):
    feedback = Feedback.objects.get(id=id)
    submission = feedback.submission
    assignment = submission.assignment
    # check if extension is granted
    try:
        extension = Extension.objects.get(
            assignment=assignment, student=request.user)
        assignment.due_date = extension.date
        assignment.extension = True
    except Extension.DoesNotExist:
        assignment.extension = False
    if not feedback.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this feedback."
        })
    if request.method == "POST" and request.user == feedback.reviewer:
        if assignment.real_due_date < timezone.now():
            return render(request, "403.html", {
                "message": "The due date for this assignment has passed."
            })
        message = request.POST.get("comments")
        grade = request.POST.get("grade")
        feedback.comment = message
        feedback.grade = grade
        feedback.issued = True
        feedback.created_at = timezone.now()
        feedback.save()
        return redirect("feedback", id=id)
    all_feedbacks = Feedback.objects.filter(submission=submission)
    comments = all_feedbacks.filter(issued=True)
    reviewers = [all_feedbacks[i].reviewer for i in range(len(all_feedbacks))]
    return render(request, "feedback.html", {
        "feedback": feedback,
        "submission": submission,
        "comments": comments,
        "reviewers": reviewers,
        "due_date_passed": assignment.real_due_date < timezone.now()
    })


@login_required
def edit_comment(request, id):
    comment = Feedback.objects.get(id=id)
    if not comment.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this comment."
        })
    comment.issued = False
    comment.graded = False
    comment.grade = None
    comment.save()
    return redirect("feedback", id)


@login_required
def delete_comment(request, id):
    comment = Feedback.objects.get(id=id)
    if not comment.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this comment."
        })
    comment.comment = ""
    comment.grade = None
    comment.graded = False
    comment.issued = False
    comment.created_at = None
    comment.save()
    return redirect("feedback", id)


@login_required
@staff_member_required
def ta_view_assignment(request, ass_id):
    assignment = Assignment.objects.get(grading_secret=ass_id)
    submissions = Submission.objects.filter(assignment=assignment)
    deadline_passed = timezone.now() > assignment.real_due_date
    for i, submission in enumerate(submissions, start=1):
        submission.number = i
        feedbacks = Feedback.objects.filter(submission=submission)
        status = "Not Ready"
        number_issued = 0
        number_graded = 0
        number_total = len(feedbacks)

        for feedback in feedbacks:
            if feedback.graded:
                number_graded += 1
            if feedback.issued:
                number_issued += 1
        if number_issued == number_total or deadline_passed:
            if number_graded != number_issued and number_issued != 0:
                percent = 100 * number_graded / number_issued
                status = f"Grading - {percent:.0f} %"
            else:
                status = "Graded"
        submission.status = status
    extensions = Extension.objects.filter(assignment=assignment)
    extension_granted = False
    last_date = assignment.real_due_date
    late_dates = [extension.date for extension in extensions]
    if late_dates:
        extension_granted = True
        last_date = max(*late_dates, assignment.real_due_date)
    return render(request, "ta_view_all.html", {
        "assignment": assignment,
        "submissions": submissions,
        "extension_granted": extension_granted,
        "last_date": last_date
    })


@login_required
@staff_member_required
def ta_view_feedback(request, sub_id):
    # find all the submissions for this assignment
    submission = Submission.objects.get(id=sub_id)
    max_grade = submission.assignment.out_of
    feedbacks = Feedback.objects.filter(submission=submission, issued=True)
    next_submission = Submission.objects.filter(id=sub_id + 1).first()
    if not next_submission:
        next_submission = False

    return render(request, "ta_view.html", {
        "submission": submission,
        "feedbacks": feedbacks,
        "next_submission": next_submission,
        "max_grade": max_grade
    })


@login_required
@staff_member_required
def grade_feedback(request, feedback_id):
    feedback = Feedback.objects.get(id=feedback_id)
    if request.method == "POST":
        grade = request.POST.get("grade")
        comment = request.POST.get("comment")
        feedback.grade = grade
        feedback.comment_TA = comment
        feedback.graded = True
        feedback.save()
        return redirect("ta_view", sub_id=feedback.submission.id)
    return redirect("ta_view", sub_id=feedback.submission.id)
