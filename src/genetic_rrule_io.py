import pickle
import data_api.classrooms     as room_api
import data_api.rasps          as rasp_api
import data_api.semesters      as seme_api
import data_api.time_structure as time_api
import data_api.timetable      as tabl_api
import data_api.constraints    as cons_api
import optimizer.grade_tool    as grade_tool
import optimizer.genetic_optimizer_rrule as optimizer
from utilities.my_types import State
from utilities.general_utilities import get_size
from tqdm import tqdm
import copy

"""
Saves population to a .pickle file.
"""
def save_population_to_file(population, path):
    print(f"Saving population to {path}")
    with open(path, "wb") as p:
        print(get_size(population) / 10**6)
        pickle.dump(population, p)


"""
Starts solver whose goal is to construct a timetable with fewest collisions possible.
Returns an State object that holds all information necessary to manipulate the timetable
in the future.
"""
def request_solver():
    # Simulating data that user would send
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

    grades                   = grade_tool.init_grades(rasps, rooms)
    timetable                = tabl_api.get_empty_timetable(rasps)
    mutable_constraints      = cons_api.get_mutable_constraints(initial_constraints)
    rasp_rrules, rrule_space = time_api.init_rrule_objects(rasps, time_structure)

    state = State(is_winter, semesters, time_structure, rooms, students_per_rasp,
                  initial_constraints, mutable_constraints,
                  timetable, grades, rasp_rrules, rrule_space,
                  groups, subject_types, set())

    optimizer.set_random_timetable(state)

    POPULATION_SIZE = 20
    population = []
    print(f"Generating populations")
    for _ in tqdm(range(POPULATION_SIZE)):
        new_state = copy.deepcopy(state)
        population.append((False, new_state)) #(converged, state)

    population = optimizer.iterate(population, 100000)
    save_population_to_file(population, "saved_timetables/population.pickle")

request_solver()
