import data_api.classrooms as room_api
import data_api.professors as prof_api
import data_api.semesters  as seme_api
from data_api.utilities.my_types import InitialConstraints, MutableConstraints

def get_initial_constraints(time_structure, rooms, rasps):
    NUM_WEEKS = time_structure.NUM_WEEKS
    NUM_DAYS  = time_structure.NUM_DAYS
    NUM_HOURS = time_structure.NUM_HOURS
    rooms_occupied   = room_api.get_rooms_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rooms)
    profs_occupied   = prof_api.get_professors_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps)
    nasts_occupied, optionals_occupied, groups_occupied = seme_api.get_nasts_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps)

    return InitialConstraints(rooms_occupied, profs_occupied, nasts_occupied,
                              optionals_occupied, groups_occupied)


def get_mutable_constraints(initial_constraints: InitialConstraints):
    rooms_occupied     = {k:v.copy() for k,v in initial_constraints.rooms_occupied.items()}
    profs_occupied     = {k:v.copy() for k,v in initial_constraints.profs_occupied.items()}
    nasts_occupied     = {k:v.copy() for k,v in initial_constraints.nasts_occupied.items()}
    optionals_occupied = {k:v.copy() for k,v in initial_constraints.optionals_occupied.items()}
    groups_occupied    = {k:v.copy() for k,v in initial_constraints.groups_occupied.items()}

    return MutableConstraints(rooms_occupied, profs_occupied, nasts_occupied,
                              optionals_occupied, groups_occupied)


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
