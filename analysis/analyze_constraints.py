import os
import pandas as pd

def get_professor_ids():
    path = "../data/csvs/professors.csv"
    with open(path) as csv_file:
        professors = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3])

        professors = pd.DataFrame(professors).astype("str")

    return set(professors.id)


def get_classroom_ids():
    path = "../data/csvs/classrooms.csv"
    with open(path) as csv_file:
        classrooms = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3,4])

        classrooms = pd.DataFrame(classrooms).astype("str")

    return set(classrooms.id)

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
    classroom_ids = get_classroom_ids()
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

    return True

print(analyze_classroom_available())
print(analyze_professor_available())
