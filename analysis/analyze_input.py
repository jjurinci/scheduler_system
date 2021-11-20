import pandas as pd
import os

def is_positive_float(number: str):
    try:
        float_num = float(number)
        return True if int(float_num) > 0 else False
    except ValueError:
        return False

# Valid is number > 0.
def is_valid_number(number: str):
    upper_limit = 10**6
    return True if is_positive_float(number) and float(number) < upper_limit else False

def is_zero_or_one(number: str):
    if number=="0" or number=="1" or number=="0.0" or number=="1.0":
        return True
    return False

def analyze_faculties():
    path = "../data/csvs/faculties.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            faculties = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1,2],
                                    on_bad_lines='error')
            faculties = pd.DataFrame(faculties)
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 3.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if faculties.empty:
        print("WARNING: faculties.csv has no rows (except header).")

    # Has properties?
    given_properties = faculties.columns.tolist()
    required_properties = ["id", "name", "userId"]

    missing = False
    for required_property in required_properties:
        if required_property not in given_properties:
            print(f"ERROR: In faculties.csv -> Property \"{required_property}\" is missing.")
            missing = True

    if missing:
        print(f"faculties.csv only has these properties: {given_properties}")
        return False

    # Has properly formated properties?

    #  None in required fields?
    improper_format = False
    for index, row in faculties.iterrows():
        if pd.isna(row.id) or pd.isna(row["name"]):
            improper_format = True

        if pd.isna(row.id):
            print(f"ERROR: In faculties.csv -> Row {index+1} has \"id\" of NULL.")
        if pd.isna(row["name"]):
            print(f"ERROR: In faculties.csv -> Row {index+1} has \"name\" of NULL.")

    if improper_format:
        return False

    #  Duplicates?
    seen = set()
    duplicates = False
    for fac_id in faculties.id:
        if fac_id in seen:
            print(f"ERROR: In faculties.csv -> \"{fac_id}\" is a duplicate id.")
            duplicates = True
        seen.add(fac_id)

    if duplicates:
        return False

    return True


def analyze_classrooms():
    path = "../data/csvs/editclassrooms.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            classrooms = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1,2,3,4],
                                    on_bad_lines='error')
            classrooms = pd.DataFrame(classrooms)
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 3.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if classrooms.empty:
        print("WARNING: classrooms.csv has no rows (except header).")

    # Has properties?
    given_properties = classrooms.columns.tolist()
    required_properties = ["id", "name", "capacity", "hasComputers" ,"userId"]

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
    classrooms = classrooms.astype({'capacity': 'str', 'hasComputers': 'str'})
    improper_format = False
    for index, row in classrooms.iterrows():
        if pd.isna(row.id) or \
           pd.isna(row["name"]) or \
           not is_valid_number(row.capacity) or \
           not is_zero_or_one(row.hasComputers):
               improper_format = True

        if pd.isna(row.id):
            print(f"ERROR: In classrooms.csv -> Row {index+1} has \"id\" of NULL.")
        if pd.isna(row["name"]):
            print(f"ERROR: In classrooms.csv -> Row {index+1} has \"hasComputers\" of NULL.")
        if not is_valid_number(row.capacity):
            print(f"ERROR: In classrooms.csv -> In Row {index+1} \"capacity\" is not a valid number.")
        if not is_zero_or_one(row.hasComputers):
            print(f"ERROR: In classrooms.csv -> In Row {index+1} \"hasComputers\" is not 0 or 1.")

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

print(analyze_classrooms())

def analyze_professors():
    pass

def analyze_semesters():
    pass

def analyze_subjects():
    pass

def analyze_rasps():
    pass
