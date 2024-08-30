from django.core.files import File
from pathlib import Path
import os

import pandas as pd


def create_gradebook(filepath):
    df = pd.read_csv(filepath)
    df = df.iloc[:, :4]
    df["dummy"] = ""
    df.loc[0, "dummy"] = "Manual Posting"
    df.to_csv(filepath, index=False)


def create_assignment_gradebook(assignment):
    template_gradebook = assignment.course.gradebook.path
    df = pd.read_csv(template_gradebook)
    df.columns = df.columns[:-1].tolist() + [assignment.name]
    df.loc[1, assignment.name] = int(
        assignment.out_of) * assignment.num_reviewers
    df.loc[2:, assignment.name] = 0
    feedbacks = assignment.feedback.all()
    for feedback in feedbacks:
        student = feedback.reviewer
        if feedback.grade:
            grade = int(feedback.grade)
        else:
            grade = 0
        assignment_grade = int(
            df.loc[df['SIS Login ID'] == student.username,
                   assignment.name].values[0])
        df.loc[df['SIS Login ID'] == student.username,
               assignment.name] = assignment_grade + grade

    if assignment.gradebook:
        assignment_gradebook = Path(assignment.gradebook.path)
    else:
        random_hex = os.urandom(4).hex()
        assignment_gradebook = f"courses/{assignment.course.slug}/assignments/{
            assignment.slug}/grading-{random_hex}/{assignment.slug}.csv"
        assignment_gradebook = Path(assignment_gradebook)
        os.makedirs(assignment_gradebook.parent, exist_ok=True)
    df.to_csv(f"/tmp/{assignment.slug}.csv", index=False)
    assignment.gradebook.save(assignment_gradebook, File(
        open(f"/tmp/{assignment.slug}.csv", "rb")))
    os.remove(f"/tmp/{assignment.slug}.csv")
