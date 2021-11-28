import data_api.semesters  as seme_api
import data_api.classrooms as room_api

import pickle
import numpy as np

from tabulate import tabulate

def load_timetables():
    name = "saved_timetables/saved_timetable.pickle"
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

def analyze_timetable():
    data = load_timetables()[0]
    timetable = data["timetable"]
    rooms_occupied = data["rooms_occupied"]
    professors_occupied = data["professors_occupied"]
    season = data["season"]

    room_ids = rooms_occupied.keys()
    rooms = room_api.get_rooms_by_ids(room_ids)
    computer_rooms = room_api.get_computer_rooms(rooms)
    room_capacity = room_api.get_rooms_capacity(rooms)

    chosen_season = True if season == "W" else False
    rasps = timetable.keys()
    nasts = seme_api.get_nasts_all_semesters(rasps, winter = chosen_season)
    students_estimate = seme_api.get_students_per_rasp_estimate(nasts)

    # PER RASP
    professor_problems, classroom_problems, capacity_problems,  = [], [], []
    computer_srs_problems, computer_weak_problems, nast_problems = [], [], []
    for rasp, (room, day, hour) in timetable.items():
        m = "*" if not rasp.mandatory else ""
        f = " [fixed]" if rasp.fixedAt else ""

        good_day = day_to_str(day)
        good_hour = hour + 1

        # Room collisions
        cnt = sum(rooms_occupied[room][day, hour:(hour + rasp.duration)]>1)
        score_rooms = round(- cnt * students_estimate[rasp], 2)
        problematic_hours = []
        for i in range(rasp.duration):
            if rooms_occupied[room][day, hour+i] > 1:
                problematic_hours.append(hour+i+1) #+1 to get range [1-16] instead of [0-15]

        if problematic_hours:
            classroom_problems.append((score_rooms, [f"{score_rooms}", f"{m}{rasp.subjectId} {rasp.type} {rasp.group}{f}", f"{room}", f"{good_day}", f"{problematic_hours}"]))

        # Professor collisions
        cnt = sum(professors_occupied[rasp.professorId][day, hour:(hour + rasp.duration)]>1)
        score_professors = round(- cnt * students_estimate[rasp], 2)
        problematic_hours = []
        for i in range(rasp.duration):
            if professors_occupied[rasp.professorId][day, hour+i] > 1:
                problematic_hours.append(hour+i+1)

        if problematic_hours:
            professor_problems.append((score_professors, [f"{score_professors}", f"{m}{rasp.subjectId} {rasp.type} {rasp.group}{f}", f"{rasp.professorId}", f"{good_day}", f"{problematic_hours}"]))

        # Insufficient room capacity
        capacity = bool(students_estimate[rasp] - room_capacity[room]>=0)
        score_capacity = round(- capacity * rasp.duration * students_estimate[rasp], 2)
        if score_capacity != 0:
            capacity_problems.append((score_capacity, [f"{score_capacity}", f"{m}{rasp.subjectId} {rasp.type} {rasp.group}{f}", f"{room}", f"{good_day}", f"{good_hour}"]))

        # Computer room & computer rasp collisions
        if not room in computer_rooms and rasp.needsComputers:
            score_computers = round(- students_estimate[rasp], 2)
            computer_srs_problems.append((score_computers, [f"{score_computers}", f"{m}{rasp.subjectId} {rasp.type} {rasp.group}{f}", f"{room}", f"{good_day}", f"{good_hour}"]))

        if room in computer_rooms and not rasp.needsComputers:
            score_computers = round(- students_estimate[rasp] * 0.1, 2)
            computer_weak_problems.append((score_computers, [f"{score_computers}", f"{m}{rasp.subjectId} {rasp.type} {rasp.group}{f}", f"{room}", f"{good_day}", f"{good_hour}"]))

    chosen_season = True if season == "W" else False
    nasts = seme_api.get_nasts_all_semesters(rasps, winter = chosen_season)
    # Nast collisions
    for semester, the_nasts in nasts.items():
        score_nasts = 0
        for nast in the_nasts:
            nast_taken =  np.zeros((5,16), dtype=np.int32)
            for rasp in nast:
                _, day, hour = timetable[rasp]
                nast_taken[day, hour:(rasp.duration + hour)] += 1
            for rasp in nast:
                _, day, hour = timetable[rasp]
                good_day = day_to_str(day)
                cnt = sum(nast_taken[day, hour:(rasp.duration + hour)]>1)
                score_nasts += cnt * students_estimate[rasp]
                score_nast = round(- cnt * students_estimate[rasp], 2)
                problematic_hours = []
                for i in range(rasp.duration):
                    if nast_taken[day, (hour + i)] > 1:
                        problematic_hours.append(hour+1)

                m = "*" if not rasp.mandatory else ""
                f = " [fixed]" if rasp.fixedAt else ""
                if problematic_hours:
                    nast_problems.append((score_nast, [f"{score_nast}", f"{m}{rasp.subjectId} {rasp.type} {rasp.group}{f}", f"{semester}", f"{good_day}", f"{problematic_hours}"]))

    classroom_problems.sort(key = lambda x: x[0])
    professor_problems.sort(key = lambda x: x[0])
    capacity_problems.sort(key = lambda x: x[0])
    computer_srs_problems.sort(key = lambda x: x[0])
    computer_weak_problems.sort(key = lambda x: x[0])
    nast_problems.sort(key = lambda x: x[0])

    classroom_problems = [room[1] for room in classroom_problems]
    professor_problems = [room[1] for room in professor_problems]
    capacity_problems = [room[1] for room in capacity_problems]
    computer_srs_problems = [room[1] for room in computer_srs_problems]
    computer_weak_problems = [room[1] for room in computer_weak_problems]
    nast_problems = [room[1] for room in nast_problems]

    print("ROOMS OVERLOADED:")
    print(tabulate(classroom_problems, headers=['Score', 'Rasp', 'roomId', 'day', 'hours'], numalign="left", stralign="left", tablefmt='fancy_grid'))

    print("\nPROFESSORS OVERLOADED:")
    print(tabulate(professor_problems, headers=['Score', 'Rasp', 'professorId', 'day', 'hours'], numalign="left", stralign="left", tablefmt='fancy_grid'))

    print("\nCAPACITY PROBLEMS:")
    print(tabulate(capacity_problems, headers=['Score', 'Rasp', 'roomId', 'day', 'hours'], numalign="left", stralign="left", tablefmt='fancy_grid'))

    print("\nRASP NEEDS COMPUTERS, BUT ITS ROOM HAS NO COMPUTERS:")
    print(tabulate(computer_srs_problems, headers=['Score', 'Rasp', 'roomId', 'day', 'hours'], numalign="left", stralign="left", tablefmt='fancy_grid'))

    print("\nRASP DOESN'T NEED COMPUTERS, BUT ITS ROOM HAS COMPUTERS:")
    print(tabulate(computer_weak_problems, headers=['Score', 'Rasp', 'roomId', 'day', 'hours'], numalign="left", stralign="left", tablefmt='fancy_grid'))

    print("\nNASTS OVERLOADED:")
    print(tabulate(nast_problems, headers=['Score', 'Rasp', 'semester', 'day', 'hours'], numalign="left", stralign="left", tablefmt='fancy_grid'))


def analyze_per_professor():
    data = load_timetables()[0]
    professors_occupied = data["professors_occupied"]

    for profId in professors_occupied:
        state = "[problem]" if (professors_occupied[profId] > 1).any() else "[good]"
        print(f"{profId} {state}\n{professors_occupied[profId]}\n")


def analyze_per_classroom():
    data = load_timetables()[0]
    rooms_occupied = data["rooms_occupied"]

    for roomId in rooms_occupied:
        state = "[problem]" if (rooms_occupied[roomId] > 1).any() else "[good]"
        print(f"{roomId} {state}\n{rooms_occupied[roomId]}\n")


def analyze_per_semester():
    data = load_timetables()[0]
    nasts_occupied = data["nasts_occupied"]

    for semester in nasts_occupied:
        sem_id, num_semester, num_students = semester.split(",")
        state = "[problem]" if (nasts_occupied[semester] > 1).any() else "[good]"
        print(f"{sem_id} {num_semester} {num_students} {state}\n{nasts_occupied[semester]}\n")


analyze_timetable()
#analyze_per_professor()
#analyze_per_classroom()
#analyze_per_semester()
