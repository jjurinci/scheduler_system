from rasptools import Optimizer
import pickle
import data_api.classrooms as room_api
import data_api.professors as prof_api
import data_api.rasps      as rasp_api
import data_api.semesters  as seme_api
import data_api.timetable  as tabl_api

winter_season = False
rasps = set(rasp_api.get_rasps_by_season(winter = winter_season))
fixed_timetable = tabl_api.get_fixed_timetable(rasps)

nasts = seme_api.get_nasts_all_semesters(rasps, winter = winter_season)
students_estimate = seme_api.get_students_per_rasp_estimate(nasts)

starting_rooms = room_api.get_rooms()
starting_rooms_constraints = room_api.get_rooms_available()
rooms_free_terms = room_api.get_rooms_free_terms(starting_rooms_constraints, starting_rooms)
rooms_occupied = room_api.get_rooms_occupied(rooms_free_terms, rasps, fixed_timetable)
computer_rooms = room_api.get_computer_rooms(starting_rooms)
rooms_capacity = room_api.get_rooms_capacity(starting_rooms)

starting_profs = prof_api.get_professors_in_rasps(rasps)
starting_prof_constraints = prof_api.get_professors_available()
professor_occupied = prof_api.get_professors_occupied(starting_prof_constraints, starting_profs)


data = {
        "rasps": rasps,
        "nasts": nasts,
        "fixed": fixed_timetable,
        "free_terms": rooms_free_terms,
        "professor_occupied": professor_occupied,
        "classroom_occupied": rooms_occupied,
        "computer_rooms": computer_rooms,
        "room_capacity": rooms_capacity,
        "students_estimate": students_estimate,
        "season": "W" if winter_season else "S"
}

OPT = Optimizer(data)
sample = OPT.initialize_random_sample(10)
sample = OPT.iterate(sample, 5000, population_cap = 10)

for timetable in sample:
    print(timetable["grade"]["totalScore"])

with open("saved_timetables/saved_timetable.pickle", "wb") as f:
    pickle.dump(sample, f)
