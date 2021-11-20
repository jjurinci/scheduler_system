from rasptools import Optimizer
from collections import Counter, defaultdict
from itertools import product
import numpy as np
import pandas as pd
import pickle

import data_api
from my_types import Subject


def get_nasts(subjects, optionals=1):
    if (not subjects and optionals) or optionals<0:
        return frozenset()
    elif not subjects:
        return frozenset([frozenset()])

    subject = subjects[0]
    subjects = subjects[1:]
    choices = frozenset(frozenset(x) for x in product(*subject.rasps.values()))
    later_included = frozenset()
    if not subject.mandatory:
        later_included = get_nasts(subjects, optionals)

        if optionals:
            included = get_nasts(subjects, optionals-1)
        else:
            included = frozenset()
    else:
        included = get_nasts(subjects, optionals)
    included = frozenset(od|li for od, li in product(choices, included))
    return included|later_included


summer_rasps = set(data_api.get_rasps_by_season(summer = True))

subject_rasps = defaultdict(lambda: defaultdict(set))
for rasp in summer_rasps:
    subject_rasps[rasp.subjectId][rasp.type].add(rasp)

seen = {}
subjects = []
for rasp in summer_rasps:
    if rasp.subjectId in seen:
        continue

    seen[rasp.subjectId] = True

    sub = data_api.get_subject_by_id(rasp.subjectId)
    if sub != -1:
        subject = Subject(sub.id, sub.name, sub.mandatory, \
                          sub.semesterIds, sub.userId, \
                          subject_rasps[sub.id])
        subjects.append(subject)


summer_semesters = data_api.get_summer_semesters()
nasts = {}
for semester in summer_semesters:
    sem_id, num_students = semester.id, semester.numStudents
    sem_name, num_semester = semester.name, semester.numSemester
    has_optional_subjects = semester.hasOptionalSubjects

    filtered_subjects = list(filter(lambda s: sem_id in s.semesterIds, subjects))
    q = get_nasts(filtered_subjects, optionals=has_optional_subjects)

    if q is None:
        q = frozenset(frozenset())

    nasts[(sem_name, num_semester, num_students)] = q


import json
def transform_time(ugly_time):
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


def transform_free_time(ugly_time):
    if ugly_time == "F":
        return []
    elif ugly_time == "T":
        return [range(0,16)]
    else:
        ranges = []
        for i in range(0,len(ugly_time), 2):
            start, finish = int(ugly_time[i]), int(ugly_time[i+1])
            ranges.append(range(start-1, finish))
        return ranges


#1 = [prof.id][day,hour] IS OCCUPIED, 0 = [prof.id][day,hour] IS FREE
professor_occupied = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.int32))
professors  = set(r.professorId for r in summer_rasps)
with open("constraints/professor_available.json") as fp:
    prof_available = json.load(fp)["professorAvailable"]

    done_professors = {}
    for avail in prof_available:
        prof_id = avail["professorId"]
        if prof_id not in professors:
            continue

        done_professors[prof_id] = True

        monday    = transform_time(avail["monday"])
        tuesday   = transform_time(avail["tuesday"])
        wednesday = transform_time(avail["wednesday"])
        thursday  = transform_time(avail["thursday"])
        friday    = transform_time(avail["friday"])

        professor_occupied[prof_id][0] = monday
        professor_occupied[prof_id][1] = tuesday
        professor_occupied[prof_id][2] = wednesday
        professor_occupied[prof_id][3] = thursday
        professor_occupied[prof_id][4] = friday

    for prof_id in professors:
        if prof_id not in done_professors:
            professor_occupied[prof_id][0] = [0]*16
            professor_occupied[prof_id][1] = [0]*16
            professor_occupied[prof_id][2] = [0]*16
            professor_occupied[prof_id][3] = [0]*16
            professor_occupied[prof_id][4] = [0]*16


FREE_TERMS = set()
classrooms = data_api.get_classrooms()
done_rooms = {}
with open("constraints/classroom_available.json", "r") as fp:
    room_available = json.load(fp)["classroomAvailable"]

    for avail in room_available:
        room_id = avail["classroomId"]
        done_rooms[room_id] = True

        monday_terms    = transform_free_time(avail["monday"])
        tuesday_terms   = transform_free_time(avail["tuesday"])
        wednesday_terms = transform_free_time(avail["wednesday"])
        thursday_terms  = transform_free_time(avail["thursday"])
        friday_terms    = transform_free_time(avail["friday"])

        if monday_terms:
            for term in monday_terms:
                FREE_TERMS |= set(product([room_id], [0], term))
        if tuesday_terms:
            for term in tuesday_terms:
                FREE_TERMS |= set(product([room_id], [1], term))
        if wednesday_terms:
            for term in wednesday_terms:
                FREE_TERMS |= set(product([room_id], [2], term))
        if thursday_terms:
            for term in thursday_terms:
                FREE_TERMS |= set(product([room_id], [3], term))
        if friday_terms:
            for term in friday_terms:
                FREE_TERMS |= set(product([room_id], [4], term))

    for room in classrooms:
        if room.id in done_rooms:
            continue
        FREE_TERMS |= set(product([room.id], range(0,5), range(0,16)))


#1 = [room][day,hour] IS OCCUPIED, 0 = [room][day,hour] IS FREE
classroom_occupied = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.int32))
for room, day, hour in FREE_TERMS:
    classroom_occupied[room][day,hour] = 0


students_estimate = Counter()
for semester, the_nasts in nasts.items():
    if not the_nasts:
        continue

    num_students = semester[2]
    stud_per_nast = num_students/len(the_nasts)
    for nast in the_nasts:
        margin = {rasp: stud_per_nast for rasp in nast}
        students_estimate.update(margin)

computer_rooms = set(room.id for room in classrooms if room.hasComputers)
room_capacity = {room.id : room.capacity for room in classrooms}

FIXED = {}
#for rasp in summer_rasps:
#    room_id, day, hour = rasp.fixedAt.split(",")
#    FIXED[rasp] = (room_id, day, hour)

data = {
        "rasps": summer_rasps,
        "nasts": nasts,
        "fixed": FIXED,
        "free_terms": FREE_TERMS,
        "professor_occupied": professor_occupied,
        "classroom_occupied": classroom_occupied,
        "computer_rooms": computer_rooms,
        "room_capacity": room_capacity,
        "students_estimate": students_estimate
}

OPT = Optimizer(data)
sample = OPT.initialize_random_sample(10)
start = pd.Series([s[0]["totalScore"] for s in sample]).describe()
sample = OPT.iterate(sample, 100, population_cap = 512)
end = pd.Series([s[0]["totalScore"] for s in sample]).describe()
print(start, end, start-end)

with open("saved_timetable.pickle", "wb") as f:
    pickle.dump(sample, f)
