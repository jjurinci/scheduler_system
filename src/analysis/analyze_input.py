import pandas as pd
import os
from dateutil.rrule import rrulestr
import data_api.time_structure as time_api
import data_api.faculties as facu_api
import data_api.study_programmes as stud_api
import data_api.semesters as seme_api
import data_api.professors as prof_api
import data_api.subjects as subj_api
from datetime import datetime


def is_valid_rrule(rrule_str: str, START_SEMESTER_DATE: datetime, END_SEMESTER_DATE: datetime, hour_to_index: dict, index):
    rrule_str = rrule_str[1:-1].replace("\\n", "\n")
    try:
        rrule_obj = rrulestr(rrule_str)
    except Exception:
        print(f"ERROR: In rasps.csv -> In Row {index} cannot parse \"rrule\".")
        return False

    start_sem_date_repr = START_SEMESTER_DATE.strftime("%d/%m/%Y,%H:%M")
    end_sem_date_repr   = END_SEMESTER_DATE.strftime("%d/%m/%Y,%H:%M")

    all_dates = list(rrule_obj)
    for rrule_date in all_dates:
        rrule_date_repr = rrule_date.strftime("%d/%m/%Y,%H:%M")
        hour_min = rrule_date.strftime("%H:%M")

        if rrule_date < START_SEMESTER_DATE:
            print(f"ERROR: In rasps.csv -> In Row {index} invalid \"rrule\" because rrule date={rrule_date_repr} is lesser than START_SEMESTER_DATE={start_sem_date_repr}.")
            return False
        if rrule_date > END_SEMESTER_DATE:
            print(f"ERROR: In rasps.csv -> In Row {index} invalid \"rrule\" because rrule date={rrule_date_repr} is bigger than END_SEMESTER_DATE={end_sem_date_repr}.")
            return False
        if hour_min != "00:00" and hour_min not in hour_to_index:
            print(f"ERROR: In rasps.csv -> In Row {index} invalid \"rrule\" because rrule date={rrule_date_repr} has hour:min which is not an academic hour:min.")
            return False
    return True


def invalid_semesterIds(semesterIds: str, real_semester_ids: set):
    foreign_keys = semesterIds.split(",")
    return [fk for fk in foreign_keys if fk != "" and fk not in real_semester_ids]


def is_float(number: str):
    try:
        float(number)
        return True
    except ValueError:
        return False


# Problem if "1.0" is passed as value
def is_positive_integer(value: str, include_zero = False):
    try:
        float_num = float(value)
        if not float_num.is_integer():
            return False

        num = int(float_num)

        if not include_zero:
            return True if num > 0 else False
        else:
            return True if num >= 0 else False
    except ValueError:
        return False


# Valid number is number > 0.
def is_valid_number(number: str):
    upper_limit = 10**6
    if is_float(number):
        float_num = float(number)
        if float_num > 0 and float_num < upper_limit:
            return True
    return False


def is_zero_or_one(number: str):
    if number=="0" or number=="1" or number=="0.0" or number=="1.0":
        return True
    return False


def is_valid_season(value: str):
    return True if value=="W" or value=="S" else False


def analyze_faculties():
    path = "database/input/csvs/faculties.csv"

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            faculties = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1],
                                    on_bad_lines='error')
            faculties = pd.DataFrame(faculties).fillna("").astype("str")
            faculties.index += 1
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
    required_properties = ["id", "name"]

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
        if not row.id or not row["name"]:
            improper_format = True

        if not row.id:
            print(f"ERROR: In faculties.csv -> Row {index} has \"id\" of NULL.")
        if not row["name"]:
            print(f"ERROR: In faculties.csv -> Row {index} has \"name\" of NULL.")

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
    path = "database/input/csvs/classrooms.csv"

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
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 5.")
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


def analyze_professors():
    path = "database/input/csvs/professors.csv"

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            professors = pd.read_csv(csv_file,
                                     delimiter=",",
                                     usecols=[0,1,2],
                                     on_bad_lines='error')
            professors = pd.DataFrame(professors).fillna("").astype("str")
            professors.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 4.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if professors.empty:
        print("WARNING: professors.csv has no rows (except header).")

    # Has properties?
    given_properties = professors.columns.tolist()
    required_properties = ["id", "first_name", "last_name"]

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
           not row.first_name or \
           not row.last_name:
               improper_format = True

        if not row.id:
            print(f"ERROR: In professors.csv -> Row {index} has \"id\" of NULL.")
        if not row.first_name:
            print(f"ERROR: In professors.csv -> Row {index} has \"first_name\" of NULL.")
        if not row.last_name:
            print(f"ERROR: In professors.csv -> Row {index} has \"last_name\" of NULL.")

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


def analyze_study_programmes():
    path = "database/input/csvs/study_programmes.csv"

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
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


def analyze_semesters():
    path = "database/input/csvs/semesters.csv"

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            semesters = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1,2,3,4,5],
                                    on_bad_lines='error')
            semesters = pd.DataFrame(semesters).fillna("").astype("str")
            semesters.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 8.")
            return False
        except Exception as e:
            print(f"ERROR: Bad CSV format. {e}")
            return False

    # CSV has header and 0 rows.
    if semesters.empty:
        print("WARNING: semesters.csv has no rows (except header).")

    # Has properties?
    given_properties = semesters.columns.tolist()
    required_properties = ["id", "num_semester","season", \
                           "has_optional_subjects", "num_students", \
                           "study_programme_id"]

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

    study_programme_ids = stud_api.get_study_programme_ids_csv()
    improper_format = False
    for index, row in semesters.iterrows():
        if not row.id or \
           not is_positive_integer(row.num_semester) or \
           not is_valid_season(row.season) or \
           not is_positive_integer(row.has_optional_subjects, include_zero=True) or \
           not is_positive_integer(row.num_students) or \
           not row.study_programme_id in study_programme_ids:
               improper_format = True

        if not row.id:
            print(f"ERROR: In semesters.csv -> Row {index} has \"id\" of NULL.")
        if not is_valid_season(row.season):
            print(f"ERROR: In semesters.csv -> In Row {index} \"season\" is not \"W\" or \"S\".")
        if not is_positive_integer(row.num_semester):
            print(f"ERROR: In semesters.csv -> In Row {index} \"num_semester\" is not a positive integer.")
        if not is_positive_integer(row.has_optional_subjects, include_zero=True):
            print(f"ERROR: In semesters.csv -> In Row {index} \"has_optional_subjects\" is not a positive integer.")
        if not is_positive_integer(row.num_students):
            print(f"ERROR: In semesters.csv -> In Row {index} \"num_students\" is not a positive integer.")
        if not row.study_programme_id in study_programme_ids:
            print(f"ERROR: In semesters.csv -> In Row {index} foreign key \"study_programme_id\" with value '{row.study_programme_id}' doesn't exist as \"id\" in study programmes.")

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


def analyze_subjects():
    path = "database/input/csvs/subjects.csv"

    # File size above 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            subjects = pd.read_csv(csv_file,
                                   delimiter=",",
                                   usecols=[0,1,2,3],
                                   on_bad_lines='error')
            subjects = pd.DataFrame(subjects).fillna("").astype("str")
            subjects.index += 1
        except ValueError:
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 5.")
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


def analyze_rasps():
    path = "database/input/csvs/rasps.csv"

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
            print(f"ERROR: Bad CSV format. Expected header length to be exactly 12.")
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
           not is_valid_rrule(row.rrule, START_SEMESTER_DATE, END_SEMESTER_DATE, hour_to_index, index):
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

print(analyze_faculties())
print(analyze_study_programmes())
print(analyze_classrooms())
print(analyze_professors())
print(analyze_semesters())
print(analyze_subjects())
print(analyze_rasps())
