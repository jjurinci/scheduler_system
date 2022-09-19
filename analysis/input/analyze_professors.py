import os
import pandas as pd
from utilities.general_utilities import load_settings

"""
Analyzes professors.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
    5) Duplicate IDs
"""
def analyze_professors():
    settings = load_settings()
    path = settings["path_professors_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path, encoding="utf-8") as csv_file:
        # Is it a properly formatted csv?
        try:
            professors = pd.read_csv(csv_file,
                                     delimiter=",",
                                     usecols=[0,1],
                                     on_bad_lines='error')
            professors = pd.DataFrame(professors).fillna("").astype("str")
            professors.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 3.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if professors.empty:
        print("WARNING: professors.csv has no rows (except header).")

    # Has properties?
    given_properties = professors.columns.tolist()
    required_properties = ["id", "name"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In professors.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"professors.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields? Proper numbers given?
    improper_format = False
    for index, row in professors.iterrows():
        if not row.id or \
           not row.name:
               improper_format = True

        if not row.id:
            print(f"ERROR: In professors.csv -> Row {index} has \"id\" of NULL.")
        if not row.name:
            print(f"ERROR: In professors.csv -> Row {index} has \"name\" of NULL.")

    if improper_format:
        return False

    #  Duplicates?
    seen = set()
    duplicates = False
    for prof_id in professors.id:
        if prof_id in seen:
            print(f"ERROR: In professors.csv -> \"{prof_id}\" is a duplicate id.")
            duplicates = True
        seen.add(prof_id)

    if duplicates:
        return False

    return True
