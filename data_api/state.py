import data_api.classrooms     as room_api
import data_api.rasps          as rasp_api
import data_api.semesters      as seme_api
import data_api.time_structure as time_api
import data_api.constraints    as cons_api
import optimizer.grade_tool    as grade_tool
from utilities.my_types import State

def get_state():
    is_winter = True
    time_structure           = time_api.get_time_structure()
    semesters                = seme_api.get_winter_semesters_dict() if is_winter else seme_api.get_summer_semesters_dict()
    rasps                    = rasp_api.get_rasps_by_season(is_winter)
    students_per_rasp        = seme_api.get_students_per_rasp_estimate(rasps)
    rooms                    = room_api.get_rooms_dict()
    initial_constraints      = cons_api.get_initial_constraints(time_structure, rooms, rasps)
    rooms                    = room_api.update_rooms(rooms, initial_constraints.rooms_occupied)

    groups = cons_api.get_type_rasps(rasps)
    subject_types = cons_api.get_subject_types(rasps)

    state = State(is_winter, semesters, time_structure, rasps, rooms, students_per_rasp,
                  initial_constraints, groups, subject_types,
                  None, None, None, None, None)

    clear_mutable(state)
    return state


def clear_mutable(state):
    rasps = state.rasps
    initial_constraints = state.initial_constraints
    time_structure = state.time_structure

    state.grade                          = grade_tool.init_grade(rasps)
    state.timetable                      = {}
    state.mutable_constraints            = cons_api.get_mutable_constraints(initial_constraints)
    state.rasp_rrules, state.rrule_table = time_api.init_rrule_objects(rasps, time_structure)

