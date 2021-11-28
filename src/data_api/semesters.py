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
        semester["numSemester"] = int(semester["numSemester"])
        semester["hasOptionalSubjects"] = int(semester["hasOptionalSubjects"])
        semester["numStudents"] = int(semester["numStudents"])
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


def get_nasts_one_semester(subjects, optionals=1):
    if (not subjects and optionals) or optionals<0:
        return frozenset()
    elif not subjects:
        return frozenset([frozenset()])

    subject = subjects[0]
    subjects = subjects[1:]
    choices = frozenset(frozenset(x) for x in product(*subject.rasps.values()))
    later_included = frozenset()
    if not subject.mandatory:
        later_included = get_nasts_one_semester(subjects, optionals)

        if optionals:
            included = get_nasts_one_semester(subjects, optionals-1)
        else:
            included = frozenset()
    else:
        included = get_nasts_one_semester(subjects, optionals)
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
        sem_id, num_students = semester.id, semester.numStudents
        sem_name, num_semester = semester.name, semester.numSemester
        has_optional_subjects = semester.hasOptionalSubjects

        #filtered_subjects = list(filter(lambda s: sem_id in s.semesterIds, subjects))
        filtered_subjects = [sub for sub in subjects if sem_id in sub.semesterIds]
        q = get_nasts_one_semester(filtered_subjects, optionals=has_optional_subjects)

        if q is None:
            q = frozenset(frozenset())

        nasts[(sem_id, sem_name, num_semester, num_students)] = q
    return nasts


def get_students_per_rasp_estimate(nasts):
    students_estimate = Counter()
    for semester, the_nasts in nasts.items():
        if not the_nasts:
            continue

        num_students = semester[3]
        stud_per_nast = num_students/len(the_nasts)
        for nast in the_nasts:
            margin = {rasp: stud_per_nast for rasp in nast}
            students_estimate.update(margin)

    return students_estimate
