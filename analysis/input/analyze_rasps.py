import os
import pandas as pd
import data_api.subjects as subj_api
import data_api.time_structure as time_api
import data_api.professors as prof_api
import data_api.classrooms as room_api
from datetime import datetime
from utilities.general_utilities import load_settings
from analysis.input.input_utilities import is_positive_integer, is_zero_or_one, is_valid_rrule

"""
Analyzes rasps.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
    5) Foreign key existence in main table check
    6) Duplicate IDs
"""
def analyze_rasps():
    settings = load_settings()
    path = settings["path_rasps_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            rasps = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1,2,3,4,5,6,7,8,9],
                                on_bad_lines='error')
            rasps = pd.DataFrame(rasps).fillna("").astype("str")
            rasps.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 10.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if rasps.empty:
        print("WARNING: rasps.csv has no rows (except header).")

    # Has properties?
    given_properties = rasps.columns.tolist()
    required_properties = ["id", "professor_id", "subject_id", "type", "group", \
                           "duration","needs_computers", "fix_at_room_id",
                           "random_dtstart_weekday", "rrule"]


    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In rasps.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"rasps.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields? Proper numbers given?
    START_SEMESTER_DATE, END_SEMESTER_DATE = time_api.get_start_end_semester()
    START_SEMESTER_DATE = datetime(START_SEMESTER_DATE.year, START_SEMESTER_DATE.month, START_SEMESTER_DATE.day, 0, 0, 0)
    END_SEMESTER_DATE   = datetime(END_SEMESTER_DATE.year, END_SEMESTER_DATE.month, END_SEMESTER_DATE.day, 23, 59, 59)
    timeblocks          = time_api.get_timeblocks()
    hour_to_index, _    = time_api.get_hour_index_structure(timeblocks)
    professor_ids = prof_api.get_professor_ids_csv()
    classroom_ids = room_api.get_classroom_ids_csv()
    subject_ids = subj_api.get_subject_ids_csv()
    improper_format = False

    for index, row in rasps.iterrows():
        if not row.id or \
           row.professor_id not in professor_ids or \
           row.subject_id not in subject_ids or \
           not row.type or \
           not row.group or \
           not is_positive_integer(row.duration) or \
           not is_zero_or_one(row.needs_computers) or \
           not is_zero_or_one(row.random_dtstart_weekday) or \
           not row.fix_at_room_id in classroom_ids and row.fix_at_room_id or \
           not is_valid_rrule(row.rrule, START_SEMESTER_DATE, END_SEMESTER_DATE, hour_to_index, row, index):
               improper_format = True

        if not row.id:
            print(f"ERROR: In rasps.csv -> Row {index} has \"id\" of NULL.")
        if row.professor_id not in professor_ids:
            print(f"ERROR: In rasps.csv -> In Row {index} In column \"professor_id\" value '{row.professor_id}' doesn't exist as \"id\" in professors.")
        if row.subject_id not in subject_ids:
            print(f"ERROR: In rasps.csv -> In Row {index} In column \"subject_id\" value '{row.subject_id}' doesn't exist as \"id\" in subjects.")
        if not row.type:
            print(f"ERROR: In rasps.csv -> Row {index} has \"type\" of NULL.")
        if not row.group:
            print(f"ERROR: In rasps.csv -> Row {index} has \"group\" of NULL.")
        if not is_positive_integer(row.duration):
            print(f"ERROR: In rasps.csv -> In Row {index} \"duration\" is not a positive integer.")
        if not is_zero_or_one(row.needs_computers):
            print(f"ERROR: In rasps.csv -> In Row {index} \"needs_computers\" is not \"0\" or \"1\".")
        if not is_zero_or_one(row.random_dtstart_weekday):
            print(f"ERROR: In rasps.csv -> In Row {index} \"random_dtstart_weekday\" is not \"0\" or \"1\".")
        if not row.fix_at_room_id in classroom_ids and row.fix_at_room_id:
            print(f"ERROR: In rasps.csv -> In Row {index} \"fix_at_room_id\" doesn't exist as an ID in classrooms.")
        if not row.rrule:
            print(f"ERROR: In rasps.csv -> Row {index} has \"rrule\" of NULL.")

    if improper_format:
        return False

    #  Duplicates?
    seen = set()
    duplicates = False
    for rasp_id in rasps.id:
        if rasp_id in seen:
            print(f"ERROR: In rasps_id.csv -> \"{rasp_id}\" is a duplicate id.")
            duplicates = True
        seen.add(rasp_id)

    if duplicates:
        return False

    return True
