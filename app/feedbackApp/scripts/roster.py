from pathlib import Path

import json
import random
import string

import openpyxl


def save_to_file(file_path, initial_passwords):
    file_path = file_path.replace("media", "passwords")
    path = Path(file_path)
    json_file_path = path.parent / "initial_passwords.json"
    json_file_path.parent.mkdir(parents=True, exist_ok=True)
    # append to the json file if it already exists
    if json_file_path.exists():
        with open(json_file_path, "r") as f:
            data = json.load(f)
            data.update(initial_passwords)
        with open(json_file_path, "w") as f:
            json.dump(data, f)
    else:
        with open(json_file_path, "w+") as f:
            json.dump(initial_passwords, f)


def create_roster(file_path, UserModel, course):
    wb = openpyxl.load_workbook(file_path)
    sh = wb.active
    initial_passwords = {}
    objs_student = []
    objs_ta = []
    objs_instructor = []
    for r in sh.rows:
        # skip the first row
        if r[0].value == "Name":
            continue
        name = r[0].value
        first_name = name.split(",")[1].strip()
        last_name = name.split(",")[0].strip()
        email = r[1].value
        gt_id = r[2].value
        type = r[5].value
        grade_type = r[8].value
        assign_feedbacks = (grade_type == "Letter Grade") or (
            grade_type == "Pass / Fail")
        is_student = (type == "Student") or (type == "Observer")
        if not UserModel.objects.filter(gt_id=gt_id).exists():
            gt_username = r[3].value
            password = ''.join(random.choices(
                string.ascii_lowercase + string.digits, k=12))
            initial_passwords[gt_username] = password
            if is_student:
                objs_student.append(
                    UserModel(
                        username=gt_username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_student=is_student,
                        assign_feedbacks=assign_feedbacks,
                        gt_id=gt_id,
                        password=password,
                    )
                )
            else:
                if type == "Ta":
                    objs_ta.append(
                        UserModel(
                            username=gt_username,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            is_student=is_student,
                            assign_feedbacks=assign_feedbacks,
                            gt_id=gt_id,
                            password=password,
                        )
                    )
                else:
                    objs_instructor.append(
                        UserModel(
                            username=gt_username,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            is_student=is_student,
                            assign_feedbacks=assign_feedbacks,
                            gt_id=gt_id,
                            password=password,
                        )
                    )
        else:
            person = UserModel.objects.get(gt_id=gt_id)
            if is_student:
                course.students.add(person)
            else:
                if type == "Ta":
                    course.teaching_assistants.add(person)
                else:
                    course.instructor.add(person)

    save_to_file(file_path, initial_passwords)

    students = UserModel.objects.bulk_create(objs_student)
    tas = UserModel.objects.bulk_create(objs_ta)
    instructors = UserModel.objects.bulk_create(objs_instructor)
    course.students.add(*students)
    course.teaching_assistants.add(*tas)
    course.instructor.add(*instructors)

    wb.close()
