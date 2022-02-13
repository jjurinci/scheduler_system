import pickle
import numpy as np
from tabulate import tabulate
import datetime


def load_timetable():
    name = "saved_timetables/zero_timetable.pickle"
    with open(name, "rb") as f:
        state = pickle.load(f)
    return state


def show_object_str(show_object):
    rasp, room_id = show_object["rasp"], show_object["room_id"]
    rasp_repr = str(rasp.subject_id) + str(rasp.type) + str(rasp.group)
    return f"{rasp_repr} {room_id} {rasp.professor_id}"


def get_print_table(week_matrix, NUM_DAYS, NUM_HOURS, by_prof_id="", by_room_id="", by_sem_id=""):
    week_matrix = week_matrix.copy()
    print_table = np.zeros((NUM_HOURS,NUM_DAYS + 1), dtype=np.ndarray)
    for i in range(NUM_HOURS):
        for j in range(1,NUM_DAYS+1):
            print_table[i][j] = []

    for i in range(NUM_HOURS):
        print_table[i][0] = i+1

    for day in range(NUM_DAYS):
        for hour in range(NUM_HOURS):
            if by_prof_id:
                week_matrix[day, hour] = [obj for obj in week_matrix[day, hour]
                                          if obj["rasp"].professor_id == by_prof_id]
            elif by_room_id:
                week_matrix[day, hour] = [obj for obj in week_matrix[day, hour]
                                          if obj["room_id"] == by_room_id]
            elif by_sem_id:
                week_matrix[day, hour] = [obj for obj in week_matrix[day, hour]
                                          if by_sem_id in obj["rasp"].mandatory_in_semester_ids or
                                             by_sem_id in obj["rasp"].optional_in_semester_ids]

            for show_object in week_matrix[day, hour]:
                obj_str = show_object_str(show_object)
                for hr in range(hour, hour+show_object["rasp"].duration):
                    print_table[hr, day+1].append(obj_str)

    return print_table


def print_timetable():
    state = load_timetable()
    timetable = state.timetable
    rasp_rrules = state.rasp_rrules
    rasps = timetable.keys()

    START_SEMESTER_DATE = state.time_structure.START_SEMESTER_DATE
    NUM_WEEKS = state.time_structure.NUM_WEEKS
    NUM_DAYS  = state.time_structure.NUM_DAYS
    NUM_HOURS = state.time_structure.NUM_HOURS
    schedule_matrix = np.empty(shape=(NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=object)

    for week in range(NUM_WEEKS):
        for day in range(NUM_DAYS):
            for hour in range(NUM_HOURS):
                schedule_matrix[week,day,hour] = []

    for rasp in rasps:
        show_object = {"rasp": rasp, "room_id": timetable[rasp].room_id, "prof_id": rasp.professor_id}
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        for week, day, hour in all_dates:
            schedule_matrix[week, day, hour].append(show_object)

    prof_ids = set(rasp.professor_id for rasp in rasps)
    for prof_id in prof_ids:
        for week in range(NUM_WEEKS):
            week_matrix = schedule_matrix[week]
            week_matrix = get_print_table(week_matrix, NUM_DAYS, NUM_HOURS, by_prof_id=prof_id)
            date = (START_SEMESTER_DATE + datetime.timedelta(weeks = week)).date()
            print(f"{prof_id} WEEK {week+1} {date}")
            print(tabulate(week_matrix, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'))
            print("")

    room_ids = set(slot.room_id for slot in timetable.values())
    for room_id in room_ids:
        for week in range(NUM_WEEKS):
            week_matrix = schedule_matrix[week]
            week_matrix = get_print_table(week_matrix, NUM_DAYS, NUM_HOURS, by_room_id=room_id)
            date = (START_SEMESTER_DATE + datetime.timedelta(weeks = week)).date()
            print(f"{room_id} WEEK {week+1} {date}")
            print(tabulate(week_matrix, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'))
            print("")

    sem_ids = set()
    for rasp in rasps:
        rasp_sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in rasp_sem_ids:
            sem_ids.add(sem_id)

    for sem_id in sem_ids:
        for week in range(NUM_WEEKS):
            week_matrix = schedule_matrix[week]
            week_matrix = get_print_table(week_matrix, NUM_DAYS, NUM_HOURS, by_sem_id=sem_id)
            date = (START_SEMESTER_DATE + datetime.timedelta(weeks = week)).date()
            print(f"{sem_id} WEEK {week+1} {date}")
            print(tabulate(week_matrix, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'))
            print("")


print_timetable()
