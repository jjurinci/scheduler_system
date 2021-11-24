from construct_data import summer_rasps, nasts, FIXED, \
                           FREE_TERMS, professor_occupied, classroom_occupied, \
                           computer_rooms, room_capacity, students_estimate

import pickle
import numpy as np

from tabulate import tabulate


def load_timetables():
    name = "timetable_to_analyze.pickle"
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
    grade, timetable = load_timetables()[0]

    # Which rasps have professor collisions? NEED: valid professor_constraints
    ## I would like to know: (day, hour) of professorId collision AND scheduled rasp(s)->(roomId, day, hour)

    # Which rasps have classrooms collisions? NEED: valid classroom_constraints

    # Which rasps have classroom capacity problems? NEED: valid classrooms

    # Which rasps have computer problems? NEED: valid classrooms

    # Which rasps have nast collisions? NEED: valid nasts

    ### Can do PER professor, PER classroom, PER capacity, PER nast, PER computer analysis
    ### Can also do PER RASP analysis -> For every rasp say exactly the problems it has.

    room_taken = {k:v.copy() for k,v in classroom_occupied.items()}
    prof_taken = {k:v.copy() for k,v in professor_occupied.items()}

    #Loading
    for rasp, (room, day, hour) in timetable.items():
        room_taken[room][day, hour:(hour + rasp.duration)] += 1
        prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)] += 1

    # PER RASP
    professor_problems, classroom_problems, capacity_problems,  = [], [], []
    computer_srs_problems, computer_weak_problems, nast_problems = [], [], []
    for rasp, (room, day, hour) in timetable.items():
        m = "*" if not rasp.mandatory else ""
        f = " [fixed]" if rasp.fixedAt else ""

        good_day = day_to_str(day)
        good_hour = hour + 1

        # Room collisions
        cnt = sum(room_taken[room][day, hour:(hour + rasp.duration)]>1)
        score_rooms = round(- cnt * students_estimate[rasp], 2)
        problematic_hours = []
        for i in range(rasp.duration):
            if room_taken[room][day, hour+i] > 1:
                problematic_hours.append(hour+i+1) #+1 to get range [1-16] instead of [0-15]

        if problematic_hours:
            classroom_problems.append((score_rooms, [f"{score_rooms}", f"{m}{rasp.subjectId}{f}", f"{room}", f"{good_day}", f"{problematic_hours}"]))

        # Professor collisions
        cnt = sum(prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)]>1)
        score_professors = round(- cnt * students_estimate[rasp], 2)
        problematic_hours = []
        for i in range(rasp.duration):
            if prof_taken[rasp.professorId][day, hour+i] > 1:
                problematic_hours.append(hour+i+1)

        if problematic_hours:
            professor_problems.append((score_professors, [f"{score_professors}", f"{m}{rasp.subjectId}{f}", f"{rasp.professorId}", f"{good_day}", f"{problematic_hours}"]))

        # Insufficient room capacity
        capacity = bool(students_estimate[rasp] - room_capacity[room]>=0)
        score_capacity = round(- capacity * rasp.duration * students_estimate[rasp], 2)
        if score_capacity != 0:
            capacity_problems.append((score_capacity, [f"{score_capacity}", f"{m}{rasp.subjectId}{f}", f"{room}", f"{good_day}", f"{good_hour}"]))

        # Computer room & computer rasp collisions
        if not room in computer_rooms and rasp.needsComputers:
            score_computers = round(- students_estimate[rasp], 2)
            computer_srs_problems.append((score_computers, [f"{score_computers}", f"{m}{rasp.subjectId}{f}", f"{room}", f"{good_day}", f"{good_hour}"]))

        if room in computer_rooms and not rasp.needsComputers:
            score_computers = round(- students_estimate[rasp] * 0.1, 2)
            computer_weak_problems.append((score_computers, [f"{score_computers}", f"{m}{rasp.subjectId}{f}", f"{room}", f"{good_day}", f"{good_hour}"]))

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
                    nast_problems.append((score_nast, [f"{score_nast}", f"{m}{rasp.subjectId}{f}", f"{semester}", f"{good_day}", f"{problematic_hours}"]))

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


analyze_timetable()
