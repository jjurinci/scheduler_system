import data_api.classrooms as room_api
import data_api.professors as prof_api
import data_api.semesters  as seme_api
from utilities.my_types import InitialConstraints, MutableConstraints
from collections import defaultdict

"""
Returns InitialConstraints object that contains initial constraints of:
rooms, professors, and semesters.
This object is not meant to be mutated.
"""
def get_initial_constraints(time_structure, rooms, rasps):
    NUM_WEEKS = time_structure.NUM_WEEKS
    NUM_DAYS  = time_structure.NUM_DAYS
    NUM_HOURS = time_structure.NUM_HOURS
    rooms_occupied   = room_api.get_rooms_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rooms)
    profs_occupied   = prof_api.get_professors_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps)
    nasts_occupied, optionals_occupied = seme_api.get_nasts_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps)

    return InitialConstraints(rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied)


"""
Returns MutableConstraints object that contains initial constraints of:
rooms, professors, and semesters.
This object is meant to be mutated.
"""
def get_mutable_constraints(initial_constraints: InitialConstraints):
    rooms_occupied     = {k:v.copy() for k,v in initial_constraints.rooms_occupied.items()}
    profs_occupied     = {k:v.copy() for k,v in initial_constraints.profs_occupied.items()}
    nasts_occupied     = {k:v.copy() for k,v in initial_constraints.nasts_occupied.items()}
    optionals_occupied = {k:v.copy() for k,v in initial_constraints.optionals_occupied.items()}

    return MutableConstraints(rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied)


"""
Returns a dictionary that for each rasp type (subject_id + type) has a set of rasps.
E.g. matV: set(matV1, matV2, matV3)
     matP: set(matP1)
     ...
Used for easier rasp group identification.
"""
def get_type_rasps(rasps):
    groups = defaultdict(lambda: set())
    for rasp in rasps:
        type_key = str(rasp.subject_id) + str(rasp.type)
        groups[type_key].add(rasp.id)
    return dict(**groups)


"""
Returns a dictionary that for each subject_id has a set of (subject_id + type).
E.g. mat:  set(matP, matV)
     prog: set(progP, progV)
     ...
Used for easier rasp group identification.
"""
def get_subject_types(rasps):
    subject_types = defaultdict(lambda: set())
    for rasp in rasps:
        type_key = str(rasp.subject_id) + str(rasp.type)
        subject_types[rasp.subject_id].add(type_key)
    return dict(**subject_types)


"""
TODO: Could be optimized further (memoization of groups all dates).
1) Gets all (other) groups of a given rasp's type.
   E.g. if "matV1" is a given rasp (type is "V") then it could get "matV2", "matV3"
2) Returns a list of all rrule dates of other groups
Used to identify where groups of a given rasp are being taxed.
"""
def get_own_groups_all_dates(state, rasp):
    groups = state.groups
    rasp_rrules = state.rasp_rrules
    own_type = str(rasp.subject_id) + str(rasp.type)
    own_groups = groups[own_type]

    own_group_dates = set()
    for rasp_id in own_groups:
        if rasp_id != rasp.id:
            all_dates = rasp_rrules[rasp_id]["all_dates"]
            other_rasp_duration = rasp_rrules[rasp_id]["rasp_duration"]
            for week, day, hour in all_dates:
                for hr in range(hour, hour + other_rasp_duration):
                    own_group_dates.add((week, day, hr))
    return own_group_dates


"""
TODO: Could be optimized further (memoization of groups all dates).
1) Gets all (other) groups of a given rasp, but of different types.
   E.g. if "matV1" is given (type is "V") then it could get "matP1", "matP2"
2) Returns a list of all rrule dates of other groups
Used to identify where groups of a given subject are being taxed.
"""
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
            all_dates = rasp_rrules[rasp_id]["all_dates"]
            other_rasp_duration = rasp_rrules[rasp_id]["rasp_duration"]
            for week, day, hour in all_dates:
                for hr in range(hour, hour + other_rasp_duration):
                    other_all_dates.add((week, day, hr))

    return other_all_dates
