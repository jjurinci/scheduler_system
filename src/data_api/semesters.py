import json
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from itertools import product
from data_api.utilities.my_types import Semester
import data_api.semesters as seme_api
import data_api.subjects  as subj_api

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


def get_semesters_dict():
    semesters = get_semesters()
    semesters = {sem.id : sem for sem in semesters}
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


def get_students_per_rasp_estimate_nasts(nasts):
    students_per_rasp = Counter()
    for semester, the_nasts in nasts.items():
        if not the_nasts:
            continue

        num_students = semester[2]
        stud_per_nast = num_students/len(the_nasts)
        for nast in the_nasts:
            margin = {rasp.id: stud_per_nast for rasp in nast}
            students_per_rasp.update(margin)

    for key in students_per_rasp:
        students_per_rasp[key] = round(students_per_rasp[key], 2)

    return students_per_rasp


def get_students_per_rasp_estimate(rasps):
    semester_rasps = defaultdict(lambda: set())
    for rasp in rasps:
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in sem_ids:
            semester_rasps[sem_id].add(rasp)

    optionals_per_sem = Counter()
    for sem_id, rasps in semester_rasps.items():
        optionals = [rasp for rasp in rasps if sem_id in rasp.optional_in_semester_ids]
        optionals_per_sem[sem_id] += len(optionals)

    semesters = seme_api.get_semesters_dict()
    students_per_rasp = Counter()
    for sem_id, rasps in semester_rasps.items():
        num_students  = semesters[sem_id].num_students
        num_optionals = optionals_per_sem[sem_id]
        for rasp in rasps:
            if sem_id in rasp.mandatory_in_semester_ids:
                students_per_rasp[rasp.id] += (num_students / rasp.total_groups)
            elif sem_id in rasp.optional_in_semester_ids:
                students_per_rasp[rasp.id] += (num_students / num_optionals) / rasp.total_groups

    for key in students_per_rasp:
        students_per_rasp[key] = round(students_per_rasp[key], 2)

    return students_per_rasp


def get_nasts_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps):
    nasts_occupied, optionals_occupied = {}, {}
    all_semester_ids = set()
    for rasp in rasps:
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in sem_ids:
            all_semester_ids.add(sem_id)

    semesters = seme_api.get_semesters_dict()
    for sem_id in all_semester_ids:
        nasts_occupied[sem_id] = np.zeros((NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8)
        if semesters[sem_id].has_optional_subjects:
            optionals_occupied[sem_id] = np.zeros((NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8)

    return nasts_occupied, optionals_occupied


def get_semester_ids_csv():
    path = "database/input/csvs/semesters.csv"
    with open(path) as csv_file:
        semesters = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1,2,3,4,5])

        semesters = pd.DataFrame(semesters).astype("str")

    return set(semesters.id)
