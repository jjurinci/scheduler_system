import pickle
import numpy as np
from construct_data import subjects, summer_semesters
from tabulate import tabulate


def load_timetables():
    name = "timetable_to_analyze2.pickle"
    with open(name, "rb") as f:
        timetables = pickle.load(f)
    return timetables


def day_to_str(day: int):
    if day == 0:
        return "monday"
    if day == 1:
        return "tuesday"
    if day == 2:
        return "wednesday"
    if day == 3:
        return "thursday"
    if day == 4:
        return "friday"


def rasp_to_str(rasp, roomId):
    m = "*" if not rasp.mandatory else ""
    return f"{m}{rasp.subjectId} {rasp.type} {rasp.group} {roomId} {rasp.professorId}"


def get_professor_print_table(timetable, prof_id):
    print_table = np.zeros((16,6), dtype=np.ndarray)
    for i in range(16):
        for j in range(1,6):
            print_table[i][j] = []

    for i in range(16):
        print_table[i][0] = i+1

    for rasp, (room, day, hour) in timetable.items():
        day = day+1
        if rasp.professorId == prof_id:
            rasp_str = rasp_to_str(rasp, room)
            for i in range(rasp.duration):
                print_table[hour+i][day].append(rasp_str)

    return print_table


def get_classroom_print_table(timetable, classroom_id):
    print_table = np.zeros((16,6), dtype=np.ndarray)
    for i in range(16):
        for j in range(1,6):
            print_table[i][j] = []

    for i in range(16):
        print_table[i][0] = i+1

    for rasp, (room, day, hour) in timetable.items():
        day = day+1
        if room == classroom_id:
            rasp_str = rasp_to_str(rasp, room)
            for i in range(rasp.duration):
                print_table[hour+i][day].append(rasp_str)

    return print_table


def get_semester_print_table(timetable, sub_ids):
    print_table = np.zeros((16,6), dtype=np.ndarray)
    for i in range(16):
        for j in range(1,6):
            print_table[i][j] = []

    for i in range(16):
        print_table[i][0] = i+1

    for rasp, (room, day, hour) in timetable.items():
        day = day+1
        if rasp.subjectId in sub_ids:
            rasp_str = rasp_to_str(rasp, room)
            for i in range(rasp.duration):
                print_table[hour+i][day].append(rasp_str)

    return print_table


def get_all_print_table(timetable):
    print_table = np.zeros((16,6), dtype=np.ndarray)
    for i in range(16):
        for j in range(1,6):
            print_table[i][j] = []

    for i in range(16):
        print_table[i][0] = i+1

    for rasp, (room, day, hour) in timetable.items():
        day = day+1
        rasp_str = rasp_to_str(rasp, room)
        for i in range(rasp.duration):
            print_table[hour+i][day].append(rasp_str)

    return print_table


def print_timetable():
    grade, timetable = load_timetables()[0]

    rasps = list(timetable.keys())
    times = list(timetable.values())
    professor_ids = {rasp.professorId for rasp in rasps}
    classroom_ids = {time[0] for time in times}

    semester_subjects = {}
    for semester in summer_semesters:
        semester_subjects[semester] = list(filter(lambda s: semester.id in s.semesterIds, subjects))

    professor_print_tables = ""
    for prof_id in professor_ids:
        print_table = get_professor_print_table(timetable, prof_id)
        professor_print_tables += f"\n\n{prof_id}\n"
        professor_print_tables += tabulate(print_table, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid')
        #print("\n", prof_id)
        #print(tabulate(print_table, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'))


    classroom_print_tables = ""
    for room_id in classroom_ids:
        print_table = get_classroom_print_table(timetable, room_id)
        classroom_print_tables += f"\n\n{room_id}\n"
        classroom_print_tables += tabulate(print_table, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid')
        #print("\n", room_id)
        #print(tabulate(print_table, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'))

    semester_print_tables = ""
    for semester in summer_semesters:
        sub_ids = [subject.id for subject in semester_subjects[semester]]
        print_table = get_semester_print_table(timetable, sub_ids)
        semester_print_tables += f"\n\n{semester.facultyId} {semester.name} {semester.numSemester}\n"
        semester_print_tables += tabulate(print_table, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid')
        #print("\n", semester.name, semester.numSemester)
        #print(tabulate(print_table, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid'))

    all_print_table = get_all_print_table(timetable)
    all_str = "Everything timetable\n"
    all_str += tabulate(all_print_table, headers=['#','monday', 'tuesday', 'wednesday', 'thursday', 'friday'], numalign="left", stralign="left", tablefmt='fancy_grid')


    with open("visual_timetables/professor_timetables.txt", "w") as f:
        f.write(professor_print_tables)

    with open("visual_timetables/classroom_timetables.txt", "w") as f:
        f.write(classroom_print_tables)

    with open("visual_timetables/semester_timetables.txt", "w") as f:
        f.write(semester_print_tables)

    with open("visual_timetables/everything_timetable.txt", "w") as f:
        f.write(all_str)

print_timetable()
