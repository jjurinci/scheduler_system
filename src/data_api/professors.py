import json
import numpy as np
from collections import defaultdict
from data_api.utilities.my_types import Professor

def get_professors():
    with open("database/input/professors.json", "r") as fp:
        professors = json.load(fp)["professors"]
    professors = [Professor(**{field: prof[field] for field in Professor._fields}) for prof in professors]
    return professors


def get_professors_available():
    with open("database/constraints/professor_available.json", "r") as fp:
        prof_available = json.load(fp)["professorAvailable"]
    return prof_available


def get_professors_by_ids(professor_ids):
    professors = get_professors()
    professors = [prof for prof in professors if prof.id in professor_ids]
    return professors


def get_professors_in_rasps(rasps):
    professor_ids = [rasp.professorId for rasp in rasps]
    return get_professors_by_ids(professor_ids)


def get_professors_occupied(prof_available, professors):
    #1 = [prof.id][day,hour] IS OCCUPIED, 0 = [prof.id][day,hour] IS FREE
    professor_occupied = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.int32))
    done_professors = {}
    for avail in prof_available:
        prof_id = avail["professorId"]
        if prof_id not in professors:
            continue

        done_professors[prof_id] = True

        monday    = transform_prof_time(avail["monday"])
        tuesday   = transform_prof_time(avail["tuesday"])
        wednesday = transform_prof_time(avail["wednesday"])
        thursday  = transform_prof_time(avail["thursday"])
        friday    = transform_prof_time(avail["friday"])

        professor_occupied[prof_id][0] = monday
        professor_occupied[prof_id][1] = tuesday
        professor_occupied[prof_id][2] = wednesday
        professor_occupied[prof_id][3] = thursday
        professor_occupied[prof_id][4] = friday

    for prof in professors:
        if prof.id not in done_professors:
            professor_occupied[prof.id][0] = [0]*16
            professor_occupied[prof.id][1] = [0]*16
            professor_occupied[prof.id][2] = [0]*16
            professor_occupied[prof.id][3] = [0]*16
            professor_occupied[prof.id][4] = [0]*16

    return professor_occupied


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
