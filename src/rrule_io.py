import pickle
import data_api.classrooms     as room_api
import data_api.professors     as prof_api
import data_api.rasps          as rasp_api
import data_api.semesters      as seme_api
import data_api.time_structure as time_api
from optimizer.dp_optimizer_rrule import Optimizer

START_SEMESTER_DATE, END_SEMESTER_DATE = time_api.get_start_end_semester()
NUM_WEEKS = time_api.weeks_between(START_SEMESTER_DATE, END_SEMESTER_DATE)
timeblocks = time_api.get_day_structure()

hourmin_to_index, index_to_hourmin = time_api.get_hour_index_structure(timeblocks)
NUM_HOURS = len(timeblocks)

winter = True
rasps = rasp_api.get_rasps_by_season(winter = winter)
nasts = seme_api.get_nasts_all_semesters(rasps, winter)
students_estimate = seme_api.get_students_per_rasp_estimate(nasts)
semesters_info = seme_api.get_winter_semesters_dict() if winter else seme_api.get_summer_semesters_dict()

starting_rooms = room_api.get_rooms()
room_capacity = room_api.get_rooms_capacity(starting_rooms)
computer_rooms = room_api.get_computer_rooms(starting_rooms)
rooms_constraints = room_api.get_rooms_constraints()
free_slots = room_api.get_rooms_free_terms(NUM_WEEKS, NUM_HOURS, rooms_constraints, starting_rooms)
rooms_occupied = room_api.get_rooms_occupied(NUM_WEEKS, NUM_HOURS, free_slots, rasps)
starting_slots = room_api.generate_starting_slots(rooms_occupied, NUM_HOURS)

starting_profs_ids = set(rasp.professor_id for rasp in rasps)
starting_profs = prof_api.get_professors_by_ids(starting_profs_ids)
profs_constraints = prof_api.get_professors_constraints()
profs_occupied = prof_api.get_professors_occupied(NUM_WEEKS, NUM_HOURS, profs_constraints, starting_profs_ids)

data = {
        "NUM_WEEKS": NUM_WEEKS,
        "NUM_HOURS": NUM_HOURS,
        "rasps": rasps,
        "nasts": nasts,
        "students_estimate": students_estimate,
        "room_capacity": room_capacity,
        "computer_rooms": computer_rooms,
        "free_slots": free_slots,
        "starting_slots": starting_slots,
        "semesters_info": semesters_info,
        "rooms_occupied": rooms_occupied,
        "profs_occupied": profs_occupied
}

o = Optimizer(data)
got_zero = False
for _ in range(5):
    try:
        data = o.random_timetable()
        data = o.iterate(data)
        if data["grades"]["all"]["totalScore"] == 0:
            got_zero = True
            break
    except KeyboardInterrupt:
        continue

if got_zero:
    name = "zero_timetable.pickle"
    print(f"Saving sample to {name}")
    with open(name, "wb") as p:
        pickle.dump(data, p)
