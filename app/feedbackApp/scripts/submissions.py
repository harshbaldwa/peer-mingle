import os
import shutil
from pathlib import Path

import yaml


def create_submissions(filepath, UserModel, assignment, SubmissionModel):
    path = Path(filepath).parent
    shutil.unpack_archive(filepath, path)
    folder = list(path.glob("assignment*"))[0]
    cwd = os.getcwd()
    os.chdir(folder)
    submission_data = yaml.safe_load(open("submission_metadata.yml"))
    for submission in submission_data:
        subfolder = submission
        try:
            try:
                gt_id = submission_data[submission][":submitters"][0][":sid"]
                student = UserModel.objects.get(gt_id=gt_id)
            except KeyError:
                email = submission_data[submission][":submitters"][0][":email"]
                student = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            continue
        created_at = submission_data[submission][":created_at"]
        if student.is_student and student.assign_feedbacks:
            file = shutil.make_archive(
                f"{student.username}", "zip", subfolder
            )
            submission = SubmissionModel.objects.create(
                assignment=assignment,
                student=student,
                file=f"{student.username}.zip",
                date=created_at,
            )
            shutil.move(file, path)
        shutil.rmtree(subfolder)
    shutil.rmtree(folder)
    os.chdir(cwd)
    # os.remove(filepath)
