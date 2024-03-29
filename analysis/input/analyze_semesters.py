import os
import pandas as pd
from analysis.input.input_utilities import is_positive_integer, is_valid_season
from utilities.general_utilities import load_settings

"""
Analyzes semesters.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
    5) Foreign key existence in main table check
    6) Duplicate IDs
"""
def analyze_semesters():
    settings = load_settings()
    path = settings["path_semesters_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path, encoding="utf-8") as csv_file:
        # Is it a properly formatted csv?
        try:
            semesters = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1,2,3,4],
                                    on_bad_lines='error')
            semesters = pd.DataFrame(semesters).fillna("").astype("str")
            semesters.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 6.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if semesters.empty:
        print("WARNING: semesters.csv has no rows (except header).")

    # Has properties?
    given_properties = semesters.columns.tolist()
    required_properties = ["id", "num_semester","season", "num_students", "study_programme_id"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In semesters.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"semesters.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?
    #  None in required fields? Proper numbers given?

    improper_format = False
    for index, row in semesters.iterrows():
        if not row.id or \
           not is_positive_integer(row.num_semester) or \
           not is_valid_season(row.season) or \
           not is_positive_integer(row.num_students):
               improper_format = True

        if not row.id:
            print(f"ERROR: In semesters.csv -> Row {index} has \"id\" of NULL.")
        if not is_valid_season(row.season):
            print(f"ERROR: In semesters.csv -> In Row {index} \"season\" is not \"W\" or \"S\".")
        if not is_positive_integer(row.num_semester):
            print(f"ERROR: In semesters.csv -> In Row {index} \"num_semester\" is not a positive integer.")
        if not is_positive_integer(row.num_students):
            print(f"ERROR: In semesters.csv -> In Row {index} \"num_students\" is not a positive integer.")

    if improper_format:
        return False

    #  Duplicates?
    seen = set()
    duplicates = False
    for sem_id in semesters.id:
        if sem_id in seen:
            print(f"ERROR: In semesters.csv -> \"{sem_id}\" is a duplicate id.")
            duplicates = True
        seen.add(sem_id)

    if duplicates:
        return False

    return True
