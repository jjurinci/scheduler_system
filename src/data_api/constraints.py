import data_api.classrooms as room_api
import data_api.professors as prof_api
import data_api.semesters  as seme_api
from data_api.utilities.my_types import InitialConstraints, MutableConstraints
from collections import defaultdict

def get_initial_constraints(time_structure, rooms, rasps):
    NUM_WEEKS = time_structure.NUM_WEEKS
    NUM_DAYS  = time_structure.NUM_DAYS
    NUM_HOURS = time_structure.NUM_HOURS
    rooms_occupied   = room_api.get_rooms_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rooms)
    profs_occupied   = prof_api.get_professors_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps)
    nasts_occupied, optionals_occupied = seme_api.get_nasts_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps)

    return InitialConstraints(rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied)


def get_mutable_constraints(initial_constraints: InitialConstraints):
    rooms_occupied     = {k:v.copy() for k,v in initial_constraints.rooms_occupied.items()}
    profs_occupied     = {k:v.copy() for k,v in initial_constraints.profs_occupied.items()}
    nasts_occupied     = {k:v.copy() for k,v in initial_constraints.nasts_occupied.items()}
    optionals_occupied = {k:v.copy() for k,v in initial_constraints.optionals_occupied.items()}

    return MutableConstraints(rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied)


def get_type_rasps(rasps):
    groups = defaultdict(lambda: set())
    for rasp in rasps:
        type_key = str(rasp.subject_id) + str(rasp.type)
        groups[type_key].add(rasp.id)
    return dict(**groups)


def get_subject_types(rasps):
    subject_types = defaultdict(lambda: set())
    for rasp in rasps:
        type_key = str(rasp.subject_id) + str(rasp.type)
        subject_types[rasp.subject_id].add(type_key)
    return dict(**subject_types)


def get_own_groups_all_dates(state, rasp):
    groups = state.groups
    rasp_rrules = state.rasp_rrules
    own_type = str(rasp.subject_id) + str(rasp.type)
    own_groups = groups[own_type]

    own_group_dates = set()
    for rasp_id in own_groups:
        if rasp_id != rasp.id:
            for week, day, hour in rasp_rrules[rasp_id]["all_dates"]:
                for hr in range(hour, hour + rasp.duration):
                    own_group_dates.add((week, day, hr))
    return own_group_dates


def get_other_groups_all_dates(state, rasp):
    groups = state.groups
    subject_types = state.subject_types
    rasp_rrules = state.rasp_rrules
    own_type = str(rasp.subject_id) + str(rasp.type)

    other_types = [sub_type for sub_type in subject_types[rasp.subject_id] if sub_type != own_type]

    other_all_dates = set()
    for other_type in other_types:
        type_groups = groups[other_type]
        for rasp_id in type_groups:
            for week, day, hour in rasp_rrules[rasp_id]["all_dates"]:
                for hr in range(hour, hour + rasp.duration):
                    other_all_dates.add((week, day, hr))
    return other_all_dates


def get_rasp_priority(rasps, initial_constraints, time_structure, students_per_rasp, rooms):
    profs_occupied = initial_constraints.profs_occupied
    NUM_DAYS = time_structure.NUM_DAYS
    NUM_HOURS = time_structure.NUM_HOURS

    rasp_duration_per_prof = {}
    for rasp in rasps:
        if rasp.professor_id not in rasp_duration_per_prof:
            rasp_duration_per_prof[rasp.professor_id] = rasp.duration
        else:
            rasp_duration_per_prof[rasp.professor_id] += rasp.duration


    prof_free_time = {}
    profs = set(rasp.professor_id for rasp in rasps)
    for prof_id in profs:
        for day in range(NUM_DAYS):
            for hour in range(NUM_HOURS):
                if profs_occupied[prof_id][0, day, hour]==0:
                    if prof_id not in prof_free_time:
                        prof_free_time[prof_id] = 1
                    else:
                        prof_free_time[prof_id] += 1

    rasp_priority = {}
    for rasp in rasps:
        rasp_priority[rasp.id] = prof_free_time[rasp.professor_id] / rasp_duration_per_prof[rasp.professor_id]

    sorted_rasps = sorted(rasps, key = lambda rasp: rasp_priority[rasp.id])
    return sorted_rasps
