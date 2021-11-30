import random
import pandas as pd
from collections import defaultdict
from itertools import product
from datetime import datetime
from dateutil.rrule import rrule, DAILY, WEEKLY, MO, TU, WE, TH, FR
import data_api.classrooms as room_api
import data_api.professors as prof_api
import data_api.rasps      as rasp_api
import data_api.semesters  as seme_api

#TODO: Implement starting room & prof constraints
#TODO: Implement nasts & nasts constraints
#TODO: Implement genetic operators & iterate function
#TODO: Make everything faster

def get_day_structure():
    path = "database/input/csvs/day_structure.csv"
    with open(path) as csv_file:
        day_structure = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1])

        day_structure = pd.DataFrame(day_structure).astype("str")

    return day_structure


def rooms_free_time(rooms, every_date_possible):
    free_time = set()
    for room in rooms :
        free_time |= set(product([room.id], every_date_possible))

    return free_time


# TODO: make faster
def invalid_rasp_starting_times(rasp_rrule, avs):
    all_rasp_dates = list(rasp_rrule)
    nonavs = set()
    for room, date in avs:
        if any((room, raspdate) not in avs for raspdate in all_rasp_dates):
            nonavs.add((room,date))

    return nonavs


# TODO: make faster
def remove_taken(rasp_rrule, slot, avs: set):
    room_id, _ = slot
    remove_dates = set(product([room_id], rasp_rrule))
    avs -= remove_dates
    return avs


def random_sample(rasps, free_time_pool, all_starting_times):
    END_SEMESTER_DATE = datetime(2022, 1, 28)

    room_ids = list(map(lambda r: r.id, room_api.get_rooms()))
    all_starting_times = list(product(room_ids, all_starting_times))

    timetable = {}
    avs = free_time_pool
    for rasp in rasps:
        okay = False
        slot = None
        while not okay:
            # I assume a rasp is going to have its own dtstart since rasp could be 6 days midsemester only
            # If they don't provide dtstart I'm going to choose randomly 1 in all_starting_times
            #
            # Choosing one randomly:
            slot = random.choice(all_starting_times)
            room_id, RASP_DTSTART = random.choice(all_starting_times)
            UNTIL_DATE = END_SEMESTER_DATE.replace(hour=RASP_DTSTART.hour, minute = RASP_DTSTART.minute)

            # Defining my own rasp rrule:
            rasp_rrule = rrule(freq=WEEKLY, dtstart=RASP_DTSTART, until=UNTIL_DATE, cache=True)
            nonavs = invalid_rasp_starting_times(rasp_rrule, avs)
            avs_cp = avs.copy()
            avs_cp -= nonavs

            if avs_cp:
                avs = remove_taken(rasp_rrule, slot, avs)
                all_starting_times.remove(slot)
                okay = True

        timetable[rasp] = slot

    return timetable


def generate_free_time():
    day_structure = get_day_structure()

    START_SEMESTER_DATE = datetime(2021, 10, 4)
    END_SEMESTER_DATE = datetime(2022, 1, 28)
    date_index, index_date = {}, {}

    all_starting_times = []
    for _, row in day_structure.iterrows():
        start_time, end_time = row["timeblock"].split("-")

        start_hr, start_min = list(map(int, start_time.split(":")))
        end_hr, end_min     = list(map(int, end_time.split(":")))

        first_date = START_SEMESTER_DATE.replace(hour=start_hr, minute=start_min)
        all_dates = rrule(freq = DAILY, count=5, dtstart=first_date, byweekday=(MO, TU, WE, TH, FR), cache=True)
        all_starting_times += list(all_dates)

        date_index[(start_hr, start_min)] = int(row["#"])
        index_date[int(row["#"])] = (start_hr, start_min)


    # all available
    every_date_possible = []
    for date in all_starting_times:
        end_date = END_SEMESTER_DATE.replace(hour=date.hour, minute=date.minute)
        all_dates = rrule(freq = WEEKLY, dtstart=date, until=end_date, cache=True)
        every_date_possible += list(all_dates)

    rooms = room_api.get_rooms()
    free_time_pool = rooms_free_time(rooms, every_date_possible)
    rooms_occupied = defaultdict(lambda: defaultdict(lambda: 0))

    professors = prof_api.get_professors()
    professors_occupied = defaultdict(lambda: defaultdict(lambda: 0))

    rasps = rasp_api.get_rasps_by_season(winter = True)
    timetable = random_sample(rasps, free_time_pool, all_starting_times)

    # DEFAULT_RASP_RRULE = rrule(freq=WEEKLY, dtstart=#given, until=END_SEMESTER_DATE)
    # grading

    room_capacity  = room_api.get_rooms_capacity(rooms)
    computer_rooms = room_api.get_computer_rooms(rooms)
    RASP_STUDENTS = random.randint(15,80)

    total_score = 0
    total_room_score, total_professor_score = 0, 0
    total_capacity_score, total_computers_score = 0, 0

    for rasp, (room_id, start_date) in timetable.items():
        hr, mi = start_date.hour, start_date.minute

        end_date = END_SEMESTER_DATE.replace(hour=hr, minute=mi)
        all_rasp_dates = list(rrule(freq=WEEKLY, dtstart=start_date, until=end_date, cache=True))

        for raspdate in all_rasp_dates:
            rooms_occupied[room_id][raspdate] += 1
            professors_occupied[rasp.professorId][raspdate] += 1

    for rasp, (room_id, start_date) in timetable.items():
        hr, mi = start_date.hour, start_date.minute

        end_date = END_SEMESTER_DATE.replace(hour=hr, minute=mi)
        all_rasp_dates = list(rrule(freq=WEEKLY, dtstart=start_date, until=end_date, cache=True))

        cnt_room_occupied, cnt_prof_occupied = 0,0
        for raspdate in all_rasp_dates:
            # Room collisions
            room_value = rooms_occupied[room_id][raspdate]
            room_tax = 0 if room_value <= 1 else room_value
            cnt_room_occupied += room_tax

            # Professor collisions
            prof_value = professors_occupied[rasp.professorId][raspdate]
            prof_tax = 0 if prof_value <= 1 else prof_value
            cnt_prof_occupied += prof_tax

        score_rooms = cnt_room_occupied * RASP_STUDENTS
        total_room_score -= score_rooms
        total_score -= score_rooms

        score_professors = cnt_prof_occupied * RASP_STUDENTS
        total_professor_score -= score_professors
        total_score -= score_professors

        # Insufficient room capacity
        capacity = bool(RASP_STUDENTS - room_capacity[room_id]>=0)
        score_capacity = capacity * rasp.duration * RASP_STUDENTS
        total_capacity_score -= score_capacity
        total_score -= score_capacity

        # Computer room & computer rasp collisions
        if not room_id in computer_rooms and rasp.needsComputers:
            score_computers = RASP_STUDENTS
            total_computers_score -= score_computers
            total_score -= score_computers

        if room_id in computer_rooms and not rasp.needsComputers:
            score_computers = RASP_STUDENTS * 0.1
            total_computers_score -= score_computers
            total_score -= score_computers

    print(f"{total_score=} {total_room_score=} {total_professor_score=} {total_capacity_score=} {total_computers_score=}")


generate_free_time()
