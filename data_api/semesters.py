import json
import math
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from utilities.my_types import Semester
from utilities.general_utilities import load_settings
import data_api.semesters as seme_api

"""
1) Gets semesters from a .json file
2) Fits them into Semester type
3) Returns the list of semesters
"""
def get_semesters():
    settings = load_settings()
    semesters_path = settings["path_semesters_json"]
    with open(semesters_path, "r", encoding="utf-8") as fp:
        semesters = json.load(fp)["semesters"]

    typed_semesters = []
    for semester in semesters:
        semester["num_semester"] = int(semester["num_semester"])
        semester["num_students"] = int(semester["num_students"])
        semester = Semester(**{field: semester[field] for field in Semester._fields})
        typed_semesters.append(semester)

    return typed_semesters


"""
1) Gets semesters from a .csv file
2) Fits them into a pandas Dataframe and converts every cell to string
3) Returns the pandas Dataframe
"""
def get_semester_ids_csv():
    settings = load_settings()
    semesters_path = settings["path_semesters_csv"]
    with open(semesters_path, encoding="utf-8") as csv_file:
        semesters = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1,2,3,4])

        semesters = pd.DataFrame(semesters).astype("str")

    return set(semesters.id)


"""
Returns a dictionary of all semesters in "[sem_id] = Semester" form.
"""
def get_semesters_dict():
    semesters = get_semesters()
    semesters = {sem.id : sem for sem in semesters}
    return semesters


"""
Returns a dictionary of winter semesters in "[sem_id] = Semester" form.
"""
def get_winter_semesters_dict():
    semesters = get_semesters()
    semesters = {sem.id : sem for sem in semesters if sem.season == "W"}
    return semesters


"""
Returns a dictionary of summer semesters in "[sem_id] = Semester" form.
"""
def get_summer_semesters_dict():
    semesters = get_semesters()
    semesters = {sem.id:sem for sem in semesters if sem.season == "S"}
    return semesters


"""
Returns a dictionary in form "[rasp.id] = number of students".
Number of students per rasp is approximated by taking the number of students
per semester and equally distributing it across rasps in that semester.
"""
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

    for rasp_id in students_per_rasp:
        students_per_rasp[rasp_id] = math.ceil(students_per_rasp[rasp_id])

    return students_per_rasp


"""
Returns three dictionaries:
1) sems_occupied[sem_id]      = np.zeros[NUM_WEEKS][NUM_DAYS][NUM_HOURS]
2) optionals_occupied[sem_id] = np.zeros[NUM_WEEKS][NUM_DAYS][NUM_HOURS]
3) sems_collisions[sem_id]    = np.zeros[NUM_WEEKS][NUM_DAYS][NUM_HOURS]

sems_occupied represents all rasps in semesters.

optionals_occupied represents only optional rasps in semesters to aid future calculation.

sems_collisions represents (only) collisions in semesters for both mandatory and optional rasps.
"""
def get_sems_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps):
    sems_occupied, optionals_occupied, sems_collisions = {}, {}, {}
    all_semester_ids = set()
    for rasp in rasps:
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in sem_ids:
            all_semester_ids.add(sem_id)

    semesters_with_optionals = set()
    for rasp in rasps:
        for sem_id in rasp.optional_in_semester_ids:
            semesters_with_optionals.add(sem_id)

    for sem_id in all_semester_ids:
        sems_occupied[sem_id] = np.zeros((NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8)
        sems_collisions[sem_id] = np.zeros((NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8)
        if sem_id in semesters_with_optionals:
            optionals_occupied[sem_id] = np.zeros((NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8)

    return sems_occupied, optionals_occupied, sems_collisions
