import json
import numpy as np
from collections import defaultdict
from data_api.utilities.my_types import Professor

def get_professors():
    with open("database/input/professors.json", "r") as fp:
        professors = json.load(fp)["professors"]

    typed_professors = []
    for prof in professors:
        prof["user_id"] = None
        prof = Professor(**{field: prof[field] for field in Professor._fields})
        typed_professors.append(prof)

    return typed_professors


def get_professors_constraints():
    with open("database/constraints/professor_available.json", "r") as fp:
        prof_available = json.load(fp)["professor_available"]
    return prof_available


def get_professors_by_ids(professor_ids):
    professors = get_professors()
    professors = [prof for prof in professors if prof.id in professor_ids]
    return professors


def get_professors_in_rasps(rasps):
    professor_ids = [rasp.professor_id for rasp in rasps]
    return get_professors_by_ids(professor_ids)


def get_professors_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps):
    professor_ids = set(rasp.professor_id for rasp in rasps)
    prof_constraints  = get_professors_constraints()

    #1 = [prof.id][week,day,hour] IS OCCUPIED, 0 = [prof.id][week,day,hour] IS FREE
    professor_occupied = defaultdict(lambda: np.ones(shape=(NUM_WEEKS,NUM_DAYS,NUM_HOURS), dtype=np.uint8))
    done_professors = {}
    for avail in prof_constraints:
        prof_id = avail["professor_id"]
        if prof_id not in professor_ids:
            continue

        done_professors[prof_id] = True

        monday    = transform_prof_time(avail["monday"])
        tuesday   = transform_prof_time(avail["tuesday"])
        wednesday = transform_prof_time(avail["wednesday"])
        thursday  = transform_prof_time(avail["thursday"])
        friday    = transform_prof_time(avail["friday"])

        for week in range(NUM_WEEKS):
            professor_occupied[prof_id][week][0] = monday
            professor_occupied[prof_id][week][1] = tuesday
            professor_occupied[prof_id][week][2] = wednesday
            professor_occupied[prof_id][week][3] = thursday
            professor_occupied[prof_id][week][4] = friday

    for prof_id in professor_ids:
        if prof_id not in done_professors:
            for week in range(NUM_WEEKS):
                professor_occupied[prof_id][week][0] = [0]*16
                professor_occupied[prof_id][week][1] = [0]*16
                professor_occupied[prof_id][week][2] = [0]*16
                professor_occupied[prof_id][week][3] = [0]*16
                professor_occupied[prof_id][week][4] = [0]*16

    return dict(**professor_occupied)


def transform_prof_time(ugly_time):
    if ugly_time == "F":
        return [1]*16
    elif ugly_time == "T":
        return [0]*16
    else:
        pretty_time = [1]*16
        for i in range(0,len(ugly_time), 2):
            start, finish = int(ugly_time[i]), int(ugly_time[i+1])
            for j in range(start, finish+1):
                pretty_time[j-1] = 0
        return pretty_time
