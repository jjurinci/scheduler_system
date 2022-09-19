import os
import pandas as pd
from analysis.input.input_utilities import is_valid_sem_date
from utilities.general_utilities import load_settings

"""
Analyzes start_end_year.csv:
    1) .csv file size (Max. 50 MB)
    2) Header length and property names
    3) Non-NULL requirement for relevant fields
    4) Value checks for relevant fields
"""
def analyze_year():
    settings = load_settings()
    path = settings["path_startendyear_csv"]

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path, encoding="utf-8") as csv_file:
        # Is it a properly formatted csv?
        try:
            year = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1],
                                    on_bad_lines='error')
            year = pd.DataFrame(year).fillna("").astype("str")
            year.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 2.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if year.empty:
        print("WARNING: start_end_year.csv has no rows (except header).")

    # Has properties?
    given_properties = year.columns.tolist()
    required_properties = ["start_semester_date", "end_semester_date"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In start_end_year.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"start_end_year.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?
    #  None in required fields? Proper numbers given?

    improper_format = False
    for index, row in year.iterrows():
        if not is_valid_sem_date(row.start_semester_date) or \
           not is_valid_sem_date(row.end_semester_date):
               improper_format = True

        if not is_valid_sem_date(row.start_semester_date):
            print(f"ERROR: In start_end_year.csv -> Row {index} has \"start_semester_date\" improperly formatted.")
        if not is_valid_sem_date(row.end_semester_date):
            print(f"ERROR: In start_end_year.csv -> Row {index} has \"end_semester_date\" improperly formatted.")

    if improper_format:
        return False

    return True
