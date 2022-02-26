import os
import pandas as pd
import data_api.rasps as rasp_api
import data_api.professors as prof_api
import data_api.time_structure as time_api
from analysis.constraints.constraints_utilities import get_free_time, get_professor_rasps_duration, is_valid_time


"""
Analyzes professor_available.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
    5) Foreign key existence in main table check
    6) Free time check (prof's all rasp.duration VS prof's free time)
"""
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

    winter_rasps, summer_rasps, _ = rasp_api.get_rasps_with_students()

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
