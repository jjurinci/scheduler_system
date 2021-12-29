import json
from collections import Counter
from itertools import product
from data_api.utilities.my_types import Semester
import data_api.subjects as subj_api

def get_semesters():
    with open("database/input/semesters.json", "r") as fp:
        semesters = json.load(fp)["semesters"]

    typed_semesters = []
    for semester in semesters:
        semester["num_semester"] = int(semester["num_semester"])
        semester["has_optional_subjects"] = int(semester["has_optional_subjects"])
        semester["num_students"] = int(semester["num_students"])
        semester["user_id"] = None
        semester = Semester(**{field: semester[field] for field in Semester._fields})
        typed_semesters.append(semester)

    return typed_semesters


def get_winter_semesters():
    semesters = get_semesters()
    semesters = [sem for sem in semesters if sem.season == "W"]
    return semesters


def get_summer_semesters():
    semesters = get_semesters()
    semesters = [sem for sem in semesters if sem.season == "S"]
    return semesters


def get_winter_semesters_dict():
    semesters = get_semesters()
    semesters = {sem.id : sem for sem in semesters if sem.season == "W"}
    return semesters


def get_summer_semesters_dict():
    semesters = get_semesters()
    semesters = {sem.id:sem for sem in semesters if sem.season == "S"}
    return semesters


def get_nasts_one_semester(subjects, mandatory, optionals=1):
    if (not subjects and optionals) or optionals<0:
        return frozenset()
    elif not subjects:
        return frozenset([frozenset()])

    subject = subjects[0]
    subjects = subjects[1:]
    choices = frozenset(frozenset(x) for x in product(*subject.rasps.values()))
    later_included = frozenset()
    if not mandatory[subject.id]: #subject.mandatory:
        later_included = get_nasts_one_semester(subjects, mandatory, optionals)

        if optionals:
            included = get_nasts_one_semester(subjects, mandatory, optionals-1)
        else:
            included = frozenset()
    else:
        included = get_nasts_one_semester(subjects, mandatory, optionals)
    included = frozenset(od|li for od, li in product(choices, included))
    return included|later_included


def get_nasts_all_semesters(rasps, winter):
    subjects = subj_api.get_subjects_with_rasps(rasps)

    semesters = None
    if winter:
        semesters = get_winter_semesters()
    else:
        semesters = get_summer_semesters()

    nasts = {}
    for semester in semesters:
        sem_id, num_students = semester.id, semester.num_students
        num_semester = semester.num_semester
        has_optional_subjects = semester.has_optional_subjects

        filtered_subjects = [sub for sub in subjects if sem_id in sub.mandatory_in_semester_ids or sem_id in sub.optional_in_semester_ids]
        mandatory = {sub.id : True if sem_id in sub.mandatory_in_semester_ids else False for sub in filtered_subjects}
        q = get_nasts_one_semester(filtered_subjects, mandatory, optionals=has_optional_subjects)

        if q is None:
            q = frozenset(frozenset())

        nasts[(sem_id, num_semester, num_students)] = q
    return nasts


def get_students_per_rasp_estimate(nasts):
    students_estimate = Counter()
    for semester, the_nasts in nasts.items():
        if not the_nasts:
            continue

        num_students = semester[2]
        stud_per_nast = num_students/len(the_nasts)
        for nast in the_nasts:
            margin = {rasp.id: stud_per_nast for rasp in nast}
            students_estimate.update(margin)

    for key in students_estimate:
        students_estimate[key] = round(students_estimate[key], 2)

    return students_estimate
