import os
import pandas as pd
import data_api.semesters as seme_api
from utilities.general_utilities import load_settings
from analysis.input.input_utilities import invalid_semesterIds

"""
Analyzes subjects.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
    5) Foreign key existence in main table check
    6) Duplicate IDs
"""
def analyze_subjects():
    settings = load_settings()
    path = settings["path_subjects_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path, encoding="utf-8") as csv_file:
        # Is it a properly formatted csv?
        try:
            subjects = pd.read_csv(csv_file,
                                   delimiter=",",
                                   usecols=[0,1,2,3],
                                   on_bad_lines='error')
            subjects = pd.DataFrame(subjects).fillna("").astype("str")
            subjects.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 4.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if subjects.empty:
        print("WARNING: subjects.csv has no rows (except header).")

    # Has properties?
    given_properties = subjects.columns.tolist()
    required_properties = ["id", "name", "mandatory_in_semester_ids", "optional_in_semester_ids"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In subjects.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"subjects.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields? Proper numbers given?
    real_semester_ids = seme_api.get_semester_ids_csv()
    improper_format = False
    for index, row in subjects.iterrows():
        invalid_mandatory_sem_fks = invalid_semesterIds(row.mandatory_in_semester_ids, real_semester_ids)
        invalid_optional_sem_fks  = invalid_semesterIds(row.optional_in_semester_ids, real_semester_ids)

        if not row.id or \
           not row["name"] or \
           invalid_mandatory_sem_fks or \
           invalid_optional_sem_fks:
               improper_format = True

        if not row.id:
            print(f"ERROR: In subjects.csv -> Row {index} has \"id\" of NULL.")
        if not row["name"]:
            print(f"ERROR: In subjects.csv -> Row {index} has \"name\" of NULL.")
        if invalid_mandatory_sem_fks:
            for invalid_fk in invalid_mandatory_sem_fks:
                print(f"ERROR: In subjects.csv -> In Row {index} In column \"mandatory_in_semester_ids\" value '{invalid_fk}' doesn't exist as \"id\" in semesters.")
        if invalid_optional_sem_fks:
            for invalid_fk in invalid_optional_sem_fks:
                print(f"ERROR: In subjects.csv -> In Row {index} In column \"optional_in_semester_ids\" value '{invalid_fk}' doesn't exist as \"id\" in semesters.")

    if improper_format:
        return False

    #  Duplicates?
    seen = set()
    duplicates = False
    for sub_id in subjects.id:
        if sub_id in seen:
            print(f"ERROR: In subjects.csv -> \"{sub_id}\" is a duplicate id.")
            duplicates = True
        seen.add(sub_id)

    if duplicates:
        return False

    #  Duplicates in FKs?
    duplicate_fks = False

    for index, row in subjects.iterrows():
        mandatory_in_semester_ids = row.mandatory_in_semester_ids.split(",")
        optional_in_semester_ids  = row.optional_in_semester_ids.split(",")
        sem_fks = mandatory_in_semester_ids + optional_in_semester_ids
        seen = set()
        for fk in sem_fks:
            if fk in seen:
                duplicates = True
                print(f"ERROR: In subjects.csv -> In Row {index} In column \"mandatory_in_semester_ids\" or in column \"optional_in_semester_ids\" value '{fk}' is a duplicate.")
            seen.add(fk)

    if duplicate_fks:
        return False

    return True
