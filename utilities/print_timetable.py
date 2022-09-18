import numpy as np
from tabulate import tabulate
import datetime
from utilities.general_utilities import load_state


"""
String representation of a rasp that will be shown in timetable.
"""
def show_object_str(show_object, by_sem_id):
    rasp, room_id = show_object["rasp"], show_object["room_id"]
    rasp_repr = str(rasp.subject_id) + str(rasp.type) + str(rasp.group)
    optional = "*" if by_sem_id in rasp.optional_in_semester_ids else ""
    return f"{rasp_repr}{optional} {room_id} {rasp.professor_id}"


"""
Constructs one week timetable "print_table" from given "week_matrix".
"week_matrix" is already populated with rasps at relevant [day,hour]s, it's
just the matter of filtering them by either (rooms, profs, semesters) and then
converting them to string representation.
"""
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
                obj_str = show_object_str(show_object, by_sem_id)
                print_table[hour, day+1].append(obj_str)

    return print_table


"""
Prints the timetable in stdout.
3 timetable views are printed:
- by rooms, by profs, and by semesters
Can be redirected to a .txt file.
"""
def run():
    state = load_state()
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

    f = open("timetable.txt", "w")
    prof_ids = set(rasp.professor_id for rasp in rasps)
    for prof_id in prof_ids:
        for week in range(NUM_WEEKS):
            week_matrix = schedule_matrix[week]
            week_matrix = get_print_table(week_matrix, NUM_DAYS, NUM_HOURS, by_prof_id=prof_id)
            date = (START_SEMESTER_DATE + datetime.timedelta(weeks = week)).date()
            print(f"{prof_id} WEEK {week+1} {date}", file=f)
            print(tabulate(week_matrix, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'), file=f)
            print("", file=f)

    room_ids = set(slot.room_id for slot in timetable.values())
    for room_id in room_ids:
        for week in range(NUM_WEEKS):
            week_matrix = schedule_matrix[week]
            week_matrix = get_print_table(week_matrix, NUM_DAYS, NUM_HOURS, by_room_id=room_id)
            date = (START_SEMESTER_DATE + datetime.timedelta(weeks = week)).date()
            print(f"{room_id} WEEK {week+1} {date}", file=f)
            print(tabulate(week_matrix, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'), file=f)
            print("", file=f)

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
            print(f"{sem_id} WEEK {week+1} {date}", file=f)
            print(tabulate(week_matrix, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'), file=f)
            print("", file=f)
