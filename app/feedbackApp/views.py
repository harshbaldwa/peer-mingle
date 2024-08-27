from .forms import CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.shortcuts import redirect, render

from .models import Assignment, Course, Feedback, Submission


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
    pending_feedbacks = 0
    # check if the user submitted this assignment
    for assignment in assignments:
        try:
            Submission.objects.get(
                assignment=assignment, student=request.user)
            assignment.submitted = True
            # check how many feedbacks the user has to issue
            pending_feedbacks = Feedback.objects.filter(
                assignment=assignment,
                reviewer=request.user,
                issued=False).count()
        except Submission.DoesNotExist:
            assignment.submitted = False
    return render(request, "course_detail.html", {
        "course": course,
        "assignments": assignments,
        "pending_feedbacks": pending_feedbacks
    })


@login_required
def assignment_view(request, slug, id):
    assignment = Assignment.objects.get(id=id)
    if not assignment.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this assignment."
        })
    try:
        submission = Submission.objects.get(
            assignment=assignment, student=request.user)
    except Submission.DoesNotExist:
        submission = None
    feedbacks = Feedback.objects.filter(
        assignment=assignment, reviewer=request.user)
    pending_feedbacks = feedbacks.filter(issued=False)
    completed_feedbacks = feedbacks.filter(issued=True)
    comments = Feedback.objects.filter(submission=submission, issued=True)

    return render(request, "assignment_detail.html", {
        "assignment": assignment,
        "submission": submission,
        "pending_feedbacks": pending_feedbacks,
        "completed_feedbacks": completed_feedbacks,
        "comments": comments
    })


@login_required
def feedback_view(request, id):
    feedback = Feedback.objects.get(id=id)
    submission = feedback.submission
    assignment = submission.assignment
    if not feedback.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this feedback."
        })
    if request.method == "POST" and request.user == feedback.reviewer:
        if assignment.due_date < timezone.now():
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
        "due_date_passed": assignment.due_date < timezone.now()
    })


@login_required
def edit_comment(request, id):
    comment = Feedback.objects.get(id=id)
    if not comment.who_has_access(request.user):
        return render(request, "403.html", {
            "message": "You don't have access to this comment."
        })
    comment.issued = False
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
    comment.issued = False
    comment.created_at = None
    comment.save()
    return redirect("feedback", id)


@login_required
@staff_member_required
def ta_view_assignment(request, ass_id):
    assignment = Assignment.objects.get(id=ass_id)
    submissions = Submission.objects.filter(assignment=assignment)
    for submission in submissions:
        graded = True
        feedbacks = Feedback.objects.filter(submission=submission, issued=True)
        for feedback in feedbacks:
            graded = feedback.graded and graded
        submission.graded = graded

    return render(request, "ta_view_all.html", {
        "assignment": assignment,
        "submissions": submissions
    })


@login_required
@staff_member_required
def ta_view_feedback(request, sub_id):
    # find all the submissions for this assignment
    submission = Submission.objects.get(id=sub_id)
    feedbacks = Feedback.objects.filter(submission=submission, issued=True)
    next_submission = Submission.objects.filter(id=sub_id + 1)
    if next_submission:
        next_submission = next_submission[0]
    else:
        next_submission = False

    return render(request, "ta_view.html", {
        "submission": submission,
        "feedbacks": feedbacks,
        "next_submission": next_submission
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
