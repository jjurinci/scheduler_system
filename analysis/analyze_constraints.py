import os
import pandas as pd
from collections import defaultdict

#TODO: Check if there is enough time allowed -> Prof for all their rasps and rooms for all rasps (take computer into account)

def get_professor_ids():
    path = "../data/csvs/professors.csv"
    with open(path) as csv_file:
        professors = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3])

        professors = pd.DataFrame(professors).astype("str")

    return set(professors.id)


def get_classrooms():
    path = "../data/csvs/classrooms.csv"
    with open(path) as csv_file:
        classrooms = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3,4])

        classrooms = pd.DataFrame(classrooms).astype("str")

    return classrooms


def get_rasps():
    path_sem = "../data/csvs/semesters.csv"
    with open(path_sem) as csv_file:
        semesters = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1,2,3,4,5,6,7],
                                on_bad_lines='error')
        semesters = pd.DataFrame(semesters).fillna("").astype("str")

    path_sub = "../data/csvs/subjects.csv"
    with open(path_sub) as csv_file:
        subjects = pd.read_csv(csv_file,
                               delimiter=",",
                               usecols=[0,1,2,3,4],
                               on_bad_lines='error')
        subjects = pd.DataFrame(subjects).fillna("").astype("str")

    path_rasps = "../data/csvs/rasps.csv"
    with open(path_rasps) as csv_file:
        rasps = pd.read_csv(csv_file,
                            delimiter=",",
                            usecols=[0,1,2,3,4,5,6,7,8,9,10,11],
                            on_bad_lines='error')
        rasps = pd.DataFrame(rasps).fillna("").astype("str")
        rasps.index += 1

    sem_students = defaultdict(lambda: 0.0)
    sem_season = defaultdict(lambda: "W")
    for _, sem in semesters.iterrows():
        sem_students[sem.id] = int(sem.numStudents)
        sem_season[sem.id] = sem.season

    sem_num_optionals = defaultdict(lambda: 0.0)
    sub_season = defaultdict(lambda: "W")
    for _, subject in subjects.iterrows():
        if subject.mandatory == "0":
            for sem_id in subject.semesterIds.split(","):
                sem_num_optionals[sem_id] += 1

        for sem_id in subject.semesterIds.split(","):
            sub_season[subject.id] = sem_season[sem_id]

    sub_students = defaultdict(lambda: 0.0)
    for _, subject in subjects.iterrows():
        for sem_id in subject.semesterIds.split(","):
            if subject.mandatory == "1":
                sub_students[subject.id] += sem_students[sem_id]
            elif subject.mandatory == "0":
                sub_students[subject.id] += (sem_students[sem_id] / sem_num_optionals[sem_id])

    for index, rasp in rasps.iterrows():
        rasps.at[index, "numStudents"] = sub_students[rasp.subjectId] // int(rasp.totalGroups)
        rasps.at[index, "season"] = sub_season[rasp.subjectId]

    winter_rasps = rasps[rasps['season'] == 'W']
    summer_rasps = rasps[rasps['season'] == 'S']

    return winter_rasps, summer_rasps


def get_professor_rasps_duration(rasps, professor_id):
    duration = 0
    for _, row in rasps.iterrows():
        if row.professorId == professor_id:
            duration += int(row.duration)
    return duration


def get_free_time(row):
    keys = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    free_time = 0
    for key in keys:
        if row[key] == "F":
            continue
        elif row[key] == "T":
            free_time += 16
        else:
            times = row[key].split(",")
            for i in range(0, len(times), 2):
                start, end = int(times[i]), int(times[i+1])
                free_time += (end - start + 1)
    return free_time


def check_capacity_free_time(rasps, classrooms, room_available):
    pc_rasps =   [rasp for _, rasp in rasps.iterrows() if rasp.needsComputers == "1"]
    nopc_rasps = [rasp for _, rasp in rasps.iterrows() if rasp.needsComputers == "0"]

    pc_rooms =   [room for _, room in classrooms.iterrows() if room.hasComputers == "1"]
    nopc_rooms = [room for _, room in classrooms.iterrows() if room.hasComputers == "0"]

    constrained_room_ids = {room.classroomId for _, room in room_available.iterrows()}
    constrained_rooms = {room.classroomId : room for _, room in room_available.iterrows()}

    pc_rooms_formatted = []
    for room in pc_rooms:
        free_time = 5 * 16
        if room.id in constrained_room_ids:
            free_time = get_free_time(constrained_rooms[room.id])

        form_room = {"capacity": int(room.capacity), "free_time": free_time, "room_id": room.id}
        pc_rooms_formatted.append(form_room)

    nopc_rooms_formatted = []
    for room in nopc_rooms:
        free_time = 5 * 16
        if room.id in constrained_room_ids:
            free_time = get_free_time(constrained_rooms[room.id])

        form_room = {"capacity": int(room.capacity), "free_time": free_time, "room_id": room.id}
        nopc_rooms_formatted.append(form_room)

    pc_rooms_formatted.sort(key=lambda x: x["capacity"])
    nopc_rooms_formatted.sort(key=lambda x: x["capacity"])

    problems = False
    for rasp in pc_rasps:
        can_fit_rasp = False
        for room in pc_rooms_formatted:
            if rasp.numStudents <= room["capacity"] and room["free_time"] >= int(rasp.duration):
                room["free_time"] -= int(rasp.duration)
                can_fit_rasp = True
                break
        if not can_fit_rasp:
            problems = True
            print(f"Cannot fit computer rasp {rasp.subjectId} {rasp.type} {rasp.group}")

    for rasp in nopc_rasps:
        can_fit_rasp = False
        for room in nopc_rooms_formatted:
            if rasp.numStudents <= room["capacity"] and room["free_time"] >= int(rasp.duration):
                room["free_time"] -= int(rasp.duration)
                can_fit_rasp = True
                break

        if not can_fit_rasp:
            for room in pc_rooms_formatted:
                if rasp.numStudents <= room["capacity"] and room["free_time"] >= int(rasp.duration):
                    room["free_time"] -= int(rasp.duration)
                    can_fit_rasp = True
                    break

        if not can_fit_rasp:
            problems = True
            print(f"Cannot fit non-computer rasp {rasp.subjectId} {rasp.type} {rasp.group}")

    if problems:
        return False

    return True


def is_positive_integer(value: str, include_zero = False):
    try:
        #float_num = float(value)
        #if not float_num.is_integer():
        #    return False

        num = int(value)

        if not include_zero:
            return True if num > 0 else False
        else:
            return True if num >= 0 else False
    except ValueError:
        return False


def is_valid_time(time: str, file_name, index, column):
    if time == "T" or time == "F":
        return []

    errors = []
    times = time.split(",")
    for number in times:
        if not is_positive_integer(number):
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{number}' is not a positive integer (or 'T' or 'F').")

        if is_positive_integer(number) and (int(number)<1 or int(number)>16):
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{number}' is not in range [1,16].")

    if errors:
        return errors

    if len(times) % 2 == 1:
        errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{time}' does not have an even number of integers. {len(times)} integers given.")
        return errors

    for i in range(0, len(times), 2):
        start, end = int(times[i]), int(times[i+1])
        if end - start <= 0:
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" values '{start}' (start) and '{end}' (end) don't make a valid time block.")

    return errors


def analyze_classroom_available():
    path = "../constraints/csvs/editclassroom_available.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            room_available = pd.read_csv(csv_file,
                                         delimiter=",",
                                         usecols=[0,1,2,3,4,5],
                                         on_bad_lines='error')
            room_available = pd.DataFrame(room_available).fillna("").astype("str")
            room_available.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 6.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if room_available.empty:
        print("WARNING: classroom_available.csv has no rows (except header).")

    # Has properties?
    given_properties = room_available.columns.tolist()
    required_properties = ["classroomId", "monday", "tuesday",
                           "wednesday", "thursday", "friday"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In classroom_available.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"classroom_available.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields? Proper numbers given?
    classrooms = get_classrooms()
    classroom_ids = {room.id for _, room in classrooms.iterrows()}
    improper_format = False

    for index, row in room_available.iterrows():
        monday_errors = is_valid_time(row.monday, "classroom_available.csv", index, "monday")
        tuesday_errors = is_valid_time(row.tuesday, "classroom_available.csv", index, "tuesday")
        wednesday_errors = is_valid_time(row.wednesday, "classroom_available.csv", index, "wednesday")
        thursday_errors = is_valid_time(row.thursday, "classroom_available.csv", index, "thursday")
        friday_errors = is_valid_time(row.friday, "classroom_available.csv", index, "friday")

        if row.classroomId not in classroom_ids or \
           monday_errors or \
           tuesday_errors or \
           wednesday_errors or \
           thursday_errors or \
           friday_errors:
               improper_format = True

        if row.classroomId not in classroom_ids:
            print(f"ERROR: In classroom_available.csv -> In Row {index} In column \"classroomId\" value '{row.classroomId}' doesn't exist as \"id\" in classrooms.")
        if monday_errors:
            for error in monday_errors:
                print(error)
        if tuesday_errors:
            for error in tuesday_errors:
                print(error)
        if wednesday_errors:
            for error in wednesday_errors:
                print(error)
        if thursday_errors:
            for error in thursday_errors:
                print(error)
        if friday_errors:
            for error in friday_errors:
                print(error)

    if improper_format:
        return False

    winter_rasps, summer_rasps = get_rasps()
    winter_succeeded = check_capacity_free_time(winter_rasps, classrooms, room_available)
    summer_succeeded = check_capacity_free_time(summer_rasps, classrooms, room_available)

    if not winter_succeeded:
        print("Winter rasps couldn't be scheduled with given classroom constraints (capacity, free time).")
        return False
    if not summer_succeeded:
        print("Summer rasps couldn't be scheduled with given classroom constraints (capacity, free time).")
        return False

    return True


def analyze_professor_available():
    path = "../constraints/csvs/editprofessor_available.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            prof_available = pd.read_csv(csv_file,
                                         delimiter=",",
                                         usecols=[0,1,2,3,4,5],
                                         on_bad_lines='error')
            prof_available = pd.DataFrame(prof_available).fillna("").astype("str")
            prof_available.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 6.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if prof_available.empty:
        print("WARNING: professor_available.csv has no rows (except header).")

    # Has properties?
    given_properties = prof_available.columns.tolist()
    required_properties = ["professorId", "monday", "tuesday",
                           "wednesday", "thursday", "friday"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In professor_available.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"professor_available.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields? Proper numbers given?
    professor_ids = get_professor_ids()
    improper_format = False

    for index, row in prof_available.iterrows():
        monday_errors = is_valid_time(row.monday, "professor_available.csv", index, "monday")
        tuesday_errors = is_valid_time(row.tuesday, "professor_available.csv", index, "tuesday")
        wednesday_errors = is_valid_time(row.wednesday, "professor_available.csv", index, "wednesday")
        thursday_errors = is_valid_time(row.thursday, "professor_available.csv", index, "thursday")
        friday_errors = is_valid_time(row.friday, "professor_available.csv", index, "friday")

        if row.professorId not in professor_ids or \
           monday_errors or \
           tuesday_errors or \
           wednesday_errors or \
           thursday_errors or \
           friday_errors:
               improper_format = True

        if row.professorId not in professor_ids:
            print(f"ERROR: In professor_available.csv -> In Row {index} In column \"professorId\" value '{row.professorId}' doesn't exist as \"id\" in professors.")
        if monday_errors:
            for error in monday_errors:
                print(error)
        if tuesday_errors:
            for error in tuesday_errors:
                print(error)
        if wednesday_errors:
            for error in wednesday_errors:
                print(error)
        if thursday_errors:
            for error in thursday_errors:
                print(error)
        if friday_errors:
            for error in friday_errors:
                print(error)

    if improper_format:
        return False

    winter_rasps, summer_rasps = get_rasps()
    not_enough_free_time = False
    for index, row in prof_available.iterrows():
        prof_free_time = get_free_time(row)
        prof_winter_rasp_duration = get_professor_rasps_duration(winter_rasps, row.professorId)
        prof_summer_rasp_duration = get_professor_rasps_duration(summer_rasps, row.professorId)

        if prof_winter_rasp_duration > prof_free_time:
            not_enough_free_time = True
            print(f"ERROR: In professor_available.csv -> In Row {index} '{row.professorId}' has total of '{prof_free_time}' units of free time but their total WINTER rasp duration is '{prof_winter_rasp_duration}' units of time.")

        if prof_summer_rasp_duration > prof_free_time:
            not_enough_free_time = True
            print(f"ERROR: In professor_available.csv -> In Row {index} '{row.professorId}' has total of '{prof_free_time}' units of free time but their total SUMMER rasp duration is '{prof_summer_rasp_duration}' units of time.")

    if not_enough_free_time:
        return False

    return True

print(analyze_classroom_available())
print(analyze_professor_available())
