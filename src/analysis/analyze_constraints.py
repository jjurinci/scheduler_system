import os
import pandas as pd
import data_api.professors as prof_api
import data_api.time_structure as time_api
import data_api.rasps as rasp_api
import data_api.semesters as seme_api
import data_api.classrooms as room_api


def get_rasps_by_season():
    rasps = rasp_api.get_rasps()
    winter_semesters = seme_api.get_winter_semesters_dict()
    students_estimate = seme_api.get_students_per_rasp_estimate(rasps)

    winter_rasps, summer_rasps = [], []
    for rasp in rasps:
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        if sem_ids[0] in winter_semesters:
            winter_rasps.append(rasp)
        else:
            summer_rasps.append(rasp)

    return winter_rasps, summer_rasps, students_estimate


def get_professor_rasps_duration(rasps, professor_id):
    duration = 0
    for rasp in rasps:
        if rasp.professor_id == professor_id:
            duration += int(rasp.duration)
    return duration


def get_free_time(row, NUM_HOURS):
    keys = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    free_time = 0
    for key in keys:
        if row[key] == "F":
            continue
        elif row[key] == "T":
            free_time += NUM_HOURS
        else:
            times = row[key].split(",")
            for i in range(0, len(times), 2):
                start, end = int(times[i]), int(times[i+1])
                free_time += (end - start + 1)
    return free_time


def check_capacity_free_time(rasps, classrooms, room_available, NUM_DAYS, NUM_HOURS, students_estimate):
    constrained_rooms = {room.room_id : room for _, room in room_available.iterrows()}
    rooms_free_time = []
    for room in classrooms.values():
        free_time = NUM_DAYS * NUM_HOURS
        if room.id in constrained_rooms:
            free_time = get_free_time(constrained_rooms[room.id], NUM_HOURS)

        room_obj = {"id": room.id, "capacity": room.capacity,
                    "has_computers":room.has_computers, "free_time":free_time}
        rooms_free_time.append(room_obj)


    # sort by has_computers=False first, by smallest capacity second
    rooms_free_time.sort(key=lambda room: (room["has_computers"], room["capacity"]))

    fit_rasps_count = 0
    for rasp in rasps:
        for room_obj in rooms_free_time:
            if room_obj["has_computers"] == rasp.needs_computers and \
               room_obj["capacity"] >= students_estimate[rasp.id] and \
               room_obj["free_time"] - rasp.duration >= 0:
                   room_obj["free_time"] -= rasp.duration
                   fit_rasps_count += 1
                   break

    return fit_rasps_count == len(rasps)


def is_positive_integer(value: str, include_zero = False):
    try:
        num = int(value)

        if not include_zero:
            return True if num > 0 else False
        else:
            return True if num >= 0 else False
    except ValueError:
        return False


def is_valid_time(time: str, file_name, index, column, NUM_HOURS):
    if time == "T" or time == "F":
        return []

    errors = []
    times = time.split(",")
    for number in times:
        if not is_positive_integer(number):
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{number}' is not a positive integer (or 'T' or 'F').")

        if is_positive_integer(number) and (int(number)<1 or int(number)>NUM_HOURS):
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{number}' is not in range [1,{NUM_HOURS}].")

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
    path = "database/constraints/csvs/classroom_available.csv"

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
    required_properties = ["room_id", "monday", "tuesday",
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
    classrooms = room_api.get_rooms_dict()
    timeblocks = time_api.get_timeblocks()
    NUM_DAYS, NUM_HOURS = 5,len(timeblocks)
    improper_format = False

    for index, row in room_available.iterrows():
        monday_errors = is_valid_time(row.monday, "classroom_available.csv", index, "monday", NUM_HOURS)
        tuesday_errors = is_valid_time(row.tuesday, "classroom_available.csv", index, "tuesday", NUM_HOURS)
        wednesday_errors = is_valid_time(row.wednesday, "classroom_available.csv", index, "wednesday", NUM_HOURS)
        thursday_errors = is_valid_time(row.thursday, "classroom_available.csv", index, "thursday", NUM_HOURS)
        friday_errors = is_valid_time(row.friday, "classroom_available.csv", index, "friday", NUM_HOURS)

        if row.room_id not in classrooms or \
           monday_errors or \
           tuesday_errors or \
           wednesday_errors or \
           thursday_errors or \
           friday_errors:
               improper_format = True

        if row.room_id not in classrooms:
            print(f"ERROR: In classroom_available.csv -> In Row {index} In column \"room_id\" value '{row.room_id}' doesn't exist as \"id\" in classrooms.")
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

    winter_rasps, summer_rasps, students_estimate = get_rasps_by_season()
    winter_succeeded = check_capacity_free_time(winter_rasps, classrooms, room_available, NUM_DAYS, NUM_HOURS, students_estimate)
    summer_succeeded = check_capacity_free_time(summer_rasps, classrooms, room_available, NUM_DAYS, NUM_HOURS, students_estimate)

    if not winter_succeeded:
        print("Not enough (computer rooms, capacity, free time) given in rooms to schedule WINTER rasps.")
    if not summer_succeeded:
        print("Not enough (computer rooms, capacity, free time) given in rooms to schedule SUMMER rasps.")

    return winter_succeeded and summer_succeeded


def analyze_professor_available():
    path = "database/constraints/csvs/professor_available.csv"

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
    required_properties = ["professor_id", "monday", "tuesday",
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
    professor_ids = prof_api.get_professor_ids_csv()
    timeblocks = time_api.get_timeblocks()
    NUM_DAYS, NUM_HOURS = 5,len(timeblocks)
    improper_format = False

    for index, row in prof_available.iterrows():
        monday_errors    = is_valid_time(row.monday, "professor_available.csv", index, "monday", NUM_HOURS)
        tuesday_errors   = is_valid_time(row.tuesday, "professor_available.csv", index, "tuesday", NUM_HOURS)
        wednesday_errors = is_valid_time(row.wednesday, "professor_available.csv", index, "wednesday", NUM_HOURS)
        thursday_errors  = is_valid_time(row.thursday, "professor_available.csv", index, "thursday", NUM_HOURS)
        friday_errors    = is_valid_time(row.friday, "professor_available.csv", index, "friday", NUM_HOURS)

        if row.professor_id not in professor_ids or \
           monday_errors or \
           tuesday_errors or \
           wednesday_errors or \
           thursday_errors or \
           friday_errors:
               improper_format = True

        if row.professor_id not in professor_ids:
            print(f"ERROR: In professor_available.csv -> In Row {index} In column \"professor_id\" value '{row.professor_id}' doesn't exist as \"id\" in professors.")
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

    winter_rasps, summer_rasps, _ = get_rasps_by_season()

    not_enough_free_time = False
    for index, row in prof_available.iterrows():
        prof_free_time = get_free_time(row, NUM_HOURS)
        prof_winter_rasp_duration = get_professor_rasps_duration(winter_rasps, row.professor_id)
        prof_summer_rasp_duration = get_professor_rasps_duration(summer_rasps, row.professor_id)

        if prof_winter_rasp_duration > prof_free_time:
            not_enough_free_time = True
            print(f"ERROR: In professor_available.csv -> In Row {index} '{row.professor_id}' has total of '{prof_free_time}' hours of free time but their total WINTER rasp duration is '{prof_winter_rasp_duration}' hours.")
        if prof_summer_rasp_duration > prof_free_time:
            not_enough_free_time = True
            print(f"ERROR: In professor_available.csv -> In Row {index} '{row.professor_id}' has total of '{prof_free_time}' hours of free time but their total SUMMER rasp duration is '{prof_summer_rasp_duration}' hours.")

    if not_enough_free_time:
        return False

    return True

print(analyze_classroom_available())
print(analyze_professor_available())
