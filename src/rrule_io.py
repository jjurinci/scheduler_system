import pickle
import data_api.classrooms     as room_api
import data_api.rasps          as rasp_api
import data_api.semesters      as seme_api
import data_api.time_structure as time_api
import data_api.timetable      as tabl_api
import data_api.constraints    as cons_api
import optimizer.grade_tool    as grade_tool
import optimizer.dp_optimizer_rrule as optimizer
from data_api.utilities.my_types import State

def request_solver():
    # Simulating data that user would send
    is_winter = True
    semesters                = seme_api.get_winter_semesters_dict() if is_winter else seme_api.get_summer_semesters_dict()
    rasps                    = rasp_api.get_rasps_by_season(winter = is_winter)
    students_per_rasp        = seme_api.get_students_per_rasp_estimate(rasps)
    rooms                    = room_api.get_rooms_dict()
    time_structure           = time_api.get_time_structure()
    initial_constraints      = cons_api.get_initial_constraints(time_structure, rooms, rasps)

    goods, bads = 0,0
    for _ in range(5):
        try:
            # Fresh initialization of mutable objects
            grades                   = grade_tool.init_grades(rasps, rooms)
            timetable                = tabl_api.get_empty_timetable(rasps)
            mutable_constraints      = cons_api.get_mutable_constraints(initial_constraints)
            rasp_rrules, rrule_space = time_api.init_rrule_objects(rasps, time_structure)

            state = State(is_winter, semesters, time_structure, rooms, students_per_rasp,
                          initial_constraints, mutable_constraints,
                          timetable, grades, rasp_rrules, rrule_space)

            optimizer.iterate(state, 1000)

            if state.grades["all"]["totalScore"] != 0:
                #print(state.grades)
                bads += 1

            if state.grades["all"]["totalScore"] == 0:
                goods += 1
                name = "saved_timetables/zero_timetable.pickle"
                print(f"Saving sample to {name}")
                with open(name, "wb") as p:
                    pickle.dump(state, p)
                break

        except KeyboardInterrupt:
            break

        print(f"{goods=} {bads=}")

request_solver()
