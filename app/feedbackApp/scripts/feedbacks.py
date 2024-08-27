from .graph import create_regular_graph


def create_feedbacks(assignment, UserModel, SubmissionModel, FeedbackModel):
    # get a list of all the usernames who submitted this assignment
    students = assignment.submissions.values_list("student", flat=True)
    num_reviewers = assignment.num_reviewers
    # get all the student objects using the usernames
    students = UserModel.objects.filter(id__in=students)
    if num_reviewers > students.count():
        num_reviewers = students.count()
        assignment.num_reviewers = num_reviewers
        assignment.save()

    mapping = create_regular_graph(students.count(), num_reviewers).edges()
    mapping = [students[i] for _, i in mapping]

    for i, student in enumerate(students):
        reviewers = []

        for reviewer in mapping[i * num_reviewers:(i + 1) * num_reviewers]:
            reviewers.append(reviewer)

        submission = SubmissionModel.objects.get(
            assignment=assignment, student=student
        )
        # create a feedback object for each reviewer
        for reviewer in reviewers:
            FeedbackModel.objects.create(
                assignment=assignment,
                submission=submission,
                reviewer=reviewer,
            )
