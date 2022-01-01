import pickle
import numpy as np
import data_api.classrooms     as room_api
import data_api.semesters      as seme_api
import data_api.rasps          as rasp_api
import data_api.professors     as prof_api
from collections import defaultdict

#TODO: Check if rrule actually has correct dates (DTSTART, UNTIL, ALL_DATES)

path = "saved_timetables/zero_timetable.pickle"

with open(path, "rb") as p:
    data = pickle.load(p)

    winter = True
    NUM_WEEKS = 17
    NUM_HOURS = 16
    semesters_info = seme_api.get_winter_semesters_dict() if winter else seme_api.get_summer_semesters_dict()
    rasps = rasp_api.get_rasps_by_season(winter = winter)
    nasts = seme_api.get_nasts_all_semesters(rasps, winter)
    students_estimate = seme_api.get_students_per_rasp_estimate(nasts)


def __tax_rrule_in_nasts(matrix3D, rasp, rrule_dates):
    for week, day, hour in rrule_dates:
        matrix3D[week, day, hour:(hour + rasp.duration)] += 1


def __nast_tax_rrule_optional_rasp(nast_occupied, optionals_occupied, rasp, hour, rrule_dates):
    for week, day, _ in rrule_dates:
        for hr in range(hour, hour + rasp.duration):
            if optionals_occupied[week, day, hr] == 0.0:
                nast_occupied[week, day, hr] += 1

        optionals_occupied[week, day, hour:(hour + rasp.duration)] += 1


def __tax_rasp_nasts(slot, rasp, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied):
    all_dates = rasp_rrules[rasp.id]["all_dates"]
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    key = str(rasp.subject_id) + str(rasp.type)
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        parallel_optionals = True if semesters_info[sem_id].has_optional_subjects == 1 else False
        if rasp.total_groups == 1:
            if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                # Tax semester fully
                __tax_rrule_in_nasts(nasts_occupied[sem_id], rasp, all_dates)
            elif not rasp_mandatory and parallel_optionals:
                # Tax only if it's the first optional at that slot
                __nast_tax_rrule_optional_rasp(nasts_occupied[sem_id], optionals_occupied[sem_id], rasp, slot.hour, all_dates)

        elif rasp.total_groups > 1:
            if slot not in groups_occupied[key]:
                groups_occupied[key][slot] = 0
            if rasp_mandatory and groups_occupied[key][slot] == 0:
                # Tax only if it's the first "subject_id + type" at that slot
                __tax_rrule_in_nasts(nasts_occupied[sem_id], rasp, all_dates)
            elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                # Tax only if it's the first "subject_id + type" at that slot AND first optional at that slot
                __nast_tax_rrule_optional_rasp(nasts_occupied[sem_id], optionals_occupied[sem_id], rasp, slot.hour, all_dates)

            #assert groups_occupied[key][slot] >= 0
            groups_occupied[key][slot] += 1


# It's actually all zeros
def check_grade_is_0(data):
    timetable   = data["timetable"]
    rasp_rrules = data["rasp_rrules"]

    nasts_occupied = defaultdict(lambda: np.zeros(shape=(NUM_WEEKS, 5, NUM_HOURS), dtype=np.uint8))
    optionals_occupied = defaultdict(lambda: np.zeros(shape=(NUM_WEEKS, 5, NUM_HOURS), dtype=np.uint8))
    groups_occupied = {}
    for rasp in timetable:
        if rasp.total_groups > 1:
            key = str(rasp.subject_id) + str(rasp.type)
            groups_occupied[key] = {}

    starting_rooms = room_api.get_rooms()
    room_capacity = room_api.get_rooms_capacity(starting_rooms)
    computer_rooms = room_api.get_computer_rooms(starting_rooms)
    rooms_constraints = room_api.get_rooms_constraints()
    free_slots = room_api.get_rooms_free_terms(NUM_WEEKS, NUM_HOURS, rooms_constraints, starting_rooms)

    starting_profs_ids = set(rasp.professor_id for rasp in rasps)
    profs_constraints = prof_api.get_professors_constraints()

    # Loading starting constraints
    rooms_occupied = room_api.get_rooms_occupied(NUM_WEEKS, NUM_HOURS, free_slots, rasps)
    profs_occupied = prof_api.get_professors_occupied(NUM_WEEKS, NUM_HOURS, profs_constraints, starting_profs_ids)

    for rasp, slot in timetable.items():
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        for week, day, hour in all_dates:
            rooms_occupied[slot.room_id][week, day, hour:(hour + rasp.duration)] += 1
            profs_occupied[rasp.professor_id][week, day, hour:(hour + rasp.duration)] += 1
        __tax_rasp_nasts(slot, rasp, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied)

    for rasp, slot in timetable.items():
        if room_capacity[slot.room_id] < students_estimate[rasp.id]:
            print(f"{rasp.id} has a capacity problem at {slot}.")
        if slot.room_id not in computer_rooms and rasp.needs_computers:
            print(f"{rasp.id} has a strong computer problem at {slot}.")
        if slot.room_id in computer_rooms and not rasp.needs_computers:
            print(f"{rasp.id} has a weak computer problem at {slot}.")

    rooms_occupied = dict(**rooms_occupied)
    profs_occupied = dict(**profs_occupied)
    nasts_occupied = dict(**nasts_occupied)

    given_rooms_occupied = data["rooms_occupied"]
    for room_id in rooms_occupied:
        for week in range(NUM_WEEKS):
            for day in range(5):
                for hour in range(NUM_HOURS):
                    if rooms_occupied[room_id][week, day, hour] > 1:
                        print(f"ROOMS: {room_id} has a collision problem at ({week}, {day}, {hour}).")
                    if rooms_occupied[room_id][week, day, hour] != given_rooms_occupied[room_id][week, day, hour]:
                        print(f"{room_id} is not the same in given and calculated 'rooms_occupied' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", rooms_occupied[room_id][week, day, hour])
                        print(f"given is: ", given_rooms_occupied[room_id][week, day, hour])

    given_profs_occupied = data["profs_occupied"]
    prof_ids = set([rasp.professor_id for rasp in timetable])
    for prof_id in prof_ids:
        for week in range(NUM_WEEKS):
            for day in range(5):
                for hour in range(NUM_HOURS):
                    if profs_occupied[prof_id][week, day, hour] > 1:
                        print(f"PROFS: {prof_id} has a collision problem at ({week}, {day}, {hour}).")
                    if profs_occupied[prof_id][week, day, hour] != given_profs_occupied[prof_id][week, day, hour]:
                        print(f"{prof_id} is not the same in given and calculated 'profs_occupied' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", profs_occupied[prof_id][week, day, hour])
                        print(f"given is: ", given_profs_occupied[prof_id][week, day, hour])

    given_nasts_occupied = data["nasts_occupied"]
    all_sem_ids = set(sem_id for rasp in timetable for sem_id in rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids)

    for sem_id in all_sem_ids:
        for week in range(NUM_WEEKS):
            for day in range(5):
                for hour in range(NUM_HOURS):
                    if nasts_occupied[sem_id][week, day, hour] > 1:
                        print(f"NASTS: {sem_id} has a collision problem at ({week}, {day}, {hour}).")
                    if nasts_occupied[sem_id][week, day, hour] != given_nasts_occupied[sem_id][week, day, hour]:
                        print(f"{sem_id} is not the same in given and calculated 'nasts_occupied' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", nasts_occupied[sem_id][week, day, hour])
                        print(f"given is: ", given_nasts_occupied[sem_id][week, day, hour])


def no_mandatory_optional_collisions(data):
    timetable, rasp_rrules = data["timetable"], data["rasp_rrules"]

    mandatory_occupied = defaultdict(lambda: np.zeros(shape=(NUM_WEEKS, 5, NUM_HOURS), dtype=np.uint8))
    optionals_occupied = defaultdict(lambda: np.zeros(shape=(NUM_WEEKS, 5, NUM_HOURS), dtype=np.uint8))

    for rasp, _ in timetable.items():
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in sem_ids:
            rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False

            for week, day, hour in all_dates:
                if rasp_mandatory:
                    mandatory_occupied[sem_id][week, day, hour:(hour + rasp.duration)] += 1
                    assert all(mandatory_occupied[sem_id][week, day, hour:(hour + rasp.duration)]<=1), "Mandatory rasps collide"
                else:
                    optionals_occupied[sem_id][week, day, hour:(hour + rasp.duration)] += 1

    all_sem_ids = set([sem_id for rasp in timetable for sem_id in rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids])
    for sem_id in all_sem_ids:
        for week in range(NUM_WEEKS):
            for day in range(5):
                for hour in range(NUM_HOURS):
                    mand_val = mandatory_occupied[sem_id][week, day, hour]
                    opti_val = optionals_occupied[sem_id][week, day, hour]
                    assert not (mand_val >= 1 and opti_val >= 1), "Mandatory and optional rasps collide"


def all_rasps_have_dates(data):
    timetable, rasp_rrules = data["timetable"], data["rasp_rrules"]
    bads = []
    for rasp, _ in timetable.items():
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        if not all_dates:
            bads.append(rasp)
    if bads:
        for rasp in bads:
            print(f"rasp_rrule[{rasp.id}]['all_dates'] is empty.")
            dtstart = rasp_rrules[rasp.id]["DTSTART"]
            until = rasp_rrules[rasp.id]["UNTIL"]
            print(f"{rasp}\n{dtstart}\n{until}\n")

    assert not bads


def all_dates_correct_start(data):
    timetable, rasp_rrules = data["timetable"], data["rasp_rrules"]

    for rasp, (_, week, day, hour) in timetable.items():
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        start_slot = (week, day, hour)
        assert start_slot == all_dates[0]


all_rasps_have_dates(data)
all_dates_correct_start(data)
no_mandatory_optional_collisions(data)
check_grade_is_0(data)
