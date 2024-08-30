import shutil
from pathlib import Path

import yaml
from yaml import CLoader as Loader


def create_submissions(filepath, UserModel, assignment, SubmissionModel):
    path = Path(filepath).parent
    prefix = Path(*path.parts[2:])
    shutil.unpack_archive(filepath, path)
    folder = list(path.glob("assignment*"))[0]
    yaml_file = list(folder.glob("*.yml"))[0]
    submissions = []
    submission_data = yaml.load(open(yaml_file), Loader)
    for submission in submission_data:
        subfolder = folder / submission
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
            submissions.append(
                SubmissionModel(
                    assignment=assignment,
                    student=student,
                    file=f"{prefix}/{student.username}.zip",
                    date=created_at,
                )
            )
            shutil.move(file, path)
        shutil.rmtree(subfolder)
    shutil.rmtree(folder)
    SubmissionModel.objects.bulk_create(submissions)
