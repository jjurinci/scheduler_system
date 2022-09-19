import os
import pandas as pd
import data_api.faculties as facu_api
from utilities.general_utilities import load_settings

"""
Analyzes study_programmes.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Foreign key existence in main table check
    5) Duplicate IDs
"""
def analyze_study_programmes():
    settings = load_settings()
    path = settings["path_studyprogrammes_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path, encoding="utf-8") as csv_file:
        # Is it a properly formatted csv?
        try:
            study_programmes = pd.read_csv(csv_file,
                                           delimiter=",",
                                           usecols=[0,1,2],
                                           on_bad_lines='error')
            study_programmes = pd.DataFrame(study_programmes).fillna("").astype("str")
            study_programmes.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 3.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if study_programmes.empty:
        print("WARNING: study_programmes.csv has no rows (except header).")

    # Has properties?
    given_properties = study_programmes.columns.tolist()
    required_properties = ["id", "name", "faculty_id"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In study_programmes.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"study_programmes.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields? Proper numbers given?

    faculty_ids = facu_api.get_faculty_ids_csv()
    improper_format = False
    for index, row in study_programmes.iterrows():
        if not row.id or \
           not row["name"] or \
           not row.faculty_id in faculty_ids:
               improper_format = True

        if not row.id:
            print(f"ERROR: In study_programmes.csv -> Row {index} has \"id\" of NULL.")
        if not row["name"]:
            print(f"ERROR: In study_programmes.csv -> Row {index} has \"name\" of NULL.")
        if not row.faculty_id in faculty_ids:
            print(f"ERROR: In study_programmes.csv -> In Row {index} foreign key \"faculty_id\" with value '{row.faculty_id}' doesn't exist as \"id\" in faculties.")

    if improper_format:
        return False

    #  Duplicates?
    seen = set()
    duplicates = False
    for study_id in study_programmes.id:
        if study_id in seen:
            print(f"ERROR: In study_programmes.csv -> \"{study_id}\" is a duplicate id.")
            duplicates = True
        seen.add(study_id)

    if duplicates:
        return False

    return True
