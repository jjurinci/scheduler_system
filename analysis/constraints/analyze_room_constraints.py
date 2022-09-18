import os
import pandas as pd
import data_api.rasps          as rasp_api
import data_api.classrooms     as room_api
import data_api.rasps          as rasp_api
import data_api.time_structure as time_api
from utilities.general_utilities import load_settings
from analysis.constraints.constraints_utilities import check_capacity_free_time, is_valid_time

"""
Analyzes classroom_available.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
    5) Foreign key existence in main table check
    6) Free time check (all rasp.duration VS room free time)
"""
def analyze_room_available():
    settings = load_settings()
    path = settings["path_classroom_available_csv"]

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

    winter_rasps, summer_rasps, students_per_rasp = rasp_api.get_rasps_with_students()
    winter_succeeded = check_capacity_free_time(winter_rasps, classrooms, room_available, NUM_DAYS, NUM_HOURS, students_per_rasp)
    summer_succeeded = check_capacity_free_time(summer_rasps, classrooms, room_available, NUM_DAYS, NUM_HOURS, students_per_rasp)

    if not winter_succeeded:
        print("Not enough (computer rooms, capacity, free time) given in rooms to schedule WINTER rasps.")
    if not summer_succeeded:
        print("Not enough (computer rooms, capacity, free time) given in rooms to schedule SUMMER rasps.")

    return winter_succeeded and summer_succeeded
