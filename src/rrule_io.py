import data_api.classrooms     as room_api
import data_api.professors     as prof_api
import data_api.rasps          as rasp_api
import data_api.semesters      as seme_api
import data_api.time_structure as time_api
from optimizer_rrule import Optimizer

START_SEMESTER_DATE, END_SEMESTER_DATE = time_api.get_start_end_semester()
NUM_WEEKS = time_api.weeks_between(START_SEMESTER_DATE, END_SEMESTER_DATE)
day_structure = time_api.get_day_structure()
hourmin_to_index, index_to_hourmin = time_api.get_hour_index_structure(day_structure)
NUM_HOURS = len(day_structure)

winter = False
rasps = rasp_api.get_rasps_by_season(winter = winter)
nasts = seme_api.get_nasts_all_semesters(rasps, winter)
students_estimate = seme_api.get_students_per_rasp_estimate(nasts)

starting_rooms = room_api.get_rooms()
room_capacity = room_api.get_rooms_capacity(starting_rooms)
computer_rooms = room_api.get_computer_rooms(starting_rooms)
rooms_constraints = room_api.get_rooms_constraints()
free_slots = room_api.get_rooms_free_terms(NUM_WEEKS, NUM_HOURS, rooms_constraints, starting_rooms)
rooms_occupied = room_api.get_rooms_occupied(NUM_WEEKS, NUM_HOURS, free_slots, rasps)
starting_slots = room_api.generate_starting_slots(rooms_occupied, NUM_HOURS)

starting_profs_ids = set(rasp.professorId for rasp in rasps)
starting_profs = prof_api.get_professors_by_ids(starting_profs_ids)
profs_constraints = prof_api.get_professors_constraints()
profs_occupied = prof_api.get_professors_occupied(NUM_WEEKS, NUM_HOURS, profs_constraints, starting_profs)

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
        "rooms_occupied": rooms_occupied,
        "profs_occupied": profs_occupied
}

o = Optimizer(data)
sample = o.random_sample(5)
o.iterate(sample)
