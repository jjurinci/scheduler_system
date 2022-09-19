import os
import pandas as pd
from analysis.input.input_utilities import is_valid_timeblock, is_positive_integer
from utilities.general_utilities import load_settings

"""
Analyzes day_structure.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
"""
def analyze_day_struct():
    settings = load_settings()
    path = settings["path_daystructure_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            day_struct = pd.read_csv(csv_file,
                                     delimiter=",",
                                     usecols=[0,1],
                                     on_bad_lines='error')
            day_struct = pd.DataFrame(day_struct).fillna("").astype("str")
            day_struct.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 2.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if day_struct.empty:
        print("WARNING: day_structure.csv has no rows (except header).")

    # Has properties?
    given_properties = day_struct.columns.tolist()
    required_properties = ["#", "timeblock"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In day_structure.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"day_structure.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?
    #  None in required fields? Proper numbers given?

    improper_format = False
    consecutive = 1
    for index, row in day_struct.iterrows():
        num = row.get("#")
        if not is_positive_integer(num) or (is_positive_integer(num) and int(num) != consecutive) or \
           not is_valid_timeblock(row.timeblock):
               improper_format = True

        if not is_positive_integer(num) or (is_positive_integer(num) and int(num) != consecutive):
            print(f"ERROR: In day_structure.csv -> Row {index} has \"#\" improperly formatted. # need to be consecutive integers starting from 1.")
        if not is_valid_timeblock(row.timeblock):
            print(f"ERROR: In day_structure.csv -> Row {index} has \"timeblock\" improperly formatted.")
        consecutive += 1

    if improper_format:
        return False

    return True
