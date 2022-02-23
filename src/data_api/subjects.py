import json
import pandas as pd
from collections import defaultdict
from data_api.utilities.my_types import Subject

def get_subjects():
    with open("database/input/subjects.json", "r") as fp:
        subjects = json.load(fp)["subjects"]

    typed_subjects = []
    for subject in subjects:
        subject["rasps"] = None
        subject["mandatory_in_semester_ids"] = tuple(subject["mandatory_in_semester_ids"]) if subject["mandatory_in_semester_ids"] != [''] else ()
        subject["optional_in_semester_ids"] = tuple(subject["optional_in_semester_ids"]) if subject["optional_in_semester_ids"] != [''] else ()
        subject["user_id"] = None
        subject = Subject(**{field: subject[field] for field in Subject._fields})
        typed_subjects.append(subject)

    return typed_subjects


def get_subject_by_id(subject_id):
    subjects = get_subjects()
    for sub in subjects:
        if sub.id == subject_id:
            return sub
    return -1


def get_subjects_with_rasps(rasps):
    subject_rasps = defaultdict(lambda: defaultdict(set))
    for rasp in rasps:
        subject_rasps[rasp.subject_id][rasp.type].add(rasp)

    subjects, seen = [], {}
    for rasp in rasps:
        if rasp.subject_id in seen:
            continue

        seen[rasp.subject_id] = True

        sub = get_subject_by_id(rasp.subject_id)
        if sub != -1:
            subject = Subject(sub.id, sub.name, sub.mandatory_in_semester_ids,
                              sub.optional_in_semester_ids, sub.user_id, subject_rasps[sub.id])
            subjects.append(subject)
    return subjects


def get_subject_ids_csv():
    path = "database/input/csvs/subjects.csv"
    with open(path) as csv_file:
        subjects = pd.read_csv(csv_file,
                               delimiter=",",
                               usecols=[0,1,2,3])

        subjects = pd.DataFrame(subjects).astype("str")

    return set(subjects.id)
