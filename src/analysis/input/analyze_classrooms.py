import os
import pandas as pd
from utilities.general_utilities import load_settings
from analysis.input.input_utilities import is_positive_integer, is_zero_or_one

"""
Analyzes classrooms.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
    5) Duplicate IDs
"""
def analyze_classrooms():
    settings = load_settings()
    path = settings["path_classrooms_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            classrooms = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1,2,3],
                                    on_bad_lines='error')
            classrooms = pd.DataFrame(classrooms).fillna("").astype("str")
            classrooms.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 4.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if classrooms.empty:
        print("WARNING: classrooms.csv has no rows (except header).")

    # Has properties?
    given_properties = classrooms.columns.tolist()
    required_properties = ["id", "name", "capacity", "has_computers"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In classrooms.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"classrooms.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields? Proper numbers given?
    improper_format = False
    for index, row in classrooms.iterrows():
        if not row.id or \
           not row["name"] or \
           not is_positive_integer(row.capacity) or \
           not is_zero_or_one(row.has_computers):
               improper_format = True

        if not row.id:
            print(f"ERROR: In classrooms.csv -> Row {index} has \"id\" of NULL.")
        if not row["name"]:
            print(f"ERROR: In classrooms.csv -> Row {index} has \"has_computers\" of NULL.")
        if not is_positive_integer(row.capacity):
            print(f"ERROR: In classrooms.csv -> In Row {index} \"capacity\" is not a positive integer.")
        if not is_zero_or_one(row.has_computers):
            print(f"ERROR: In classrooms.csv -> In Row {index} \"has_computers\" is not \"0\" or \"1\".")

    if improper_format:
        return False

    #  Duplicates?
    seen = set()
    duplicates = False
    for room_id in classrooms.id:
        if room_id in seen:
            print(f"ERROR: In classrooms.csv -> \"{room_id}\" is a duplicate id.")
            duplicates = True
        seen.add(room_id)

    if duplicates:
        return False

    return True
