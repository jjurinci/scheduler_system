import pandas as pd
import os

def get_faculty_ids():
    path = "../data/csvs/faculties.csv"
    with open(path) as csv_file:
        faculties = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1,2])

        faculties = pd.DataFrame(faculties).astype("str")

    return set(faculties.id)

def get_semester_ids():
    path = "../data/csvs/semesters.csv"
    with open(path) as csv_file:
        semesters = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1,2,3,4,5,6,7])

        semesters = pd.DataFrame(semesters).astype("str")

    return set(semesters.id)

def get_professor_ids():
    path = "../data/csvs/professors.csv"
    with open(path) as csv_file:
        professors = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3])

        professors = pd.DataFrame(professors).astype("str")

    return set(professors.id)


def get_subject_ids():
    path = "../data/csvs/subjects.csv"
    with open(path) as csv_file:
        subjects = pd.read_csv(csv_file,
                               delimiter=",",
                               usecols=[0,1,2,3,4])

        subjects = pd.DataFrame(subjects).astype("str")

    return set(subjects.id)

def get_classroom_ids():
    path = "../data/csvs/classrooms.csv"
    with open(path) as csv_file:
        classrooms = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3,4])

        classrooms = pd.DataFrame(classrooms).astype("str")

    return set(classrooms.id)

def invalid_fixedAt(raw_fixedAt, index):
    if not raw_fixedAt:
        return []

    classroom_ids = get_classroom_ids()
    fixedAt = raw_fixedAt.split(",")
    if len(fixedAt) != 3:
        return [f"ERROR: In rasps.csv -> In Row {index} In column \"fixedAt\" value '{raw_fixedAt}' has invalid format."]

    errors = []
    room_id, day, hour = fixedAt
    if room_id not in classroom_ids:
        errors.append(f"ERROR: In rasps.csv -> In Row {index} In column \"fixedAt\" room value '{room_id}' doesn't exist as \"id\" in classrooms.")
    if not is_positive_integer(day) or is_positive_integer(day) and (int(day)<1 or int(day)>5):
        errors.append(f"ERROR: In rasps.csv -> In Row {index} In column \"fixedAt\" day value '{day}' must be in range [1,5].")
    if not is_positive_integer(hour) or is_positive_integer(hour) and (int(hour)<1 or int(hour)>16):
        errors.append(f"ERROR: In rasps.csv -> In Row {index} In column \"fixedAt\" hour value '{hour}' must be in range [1,16].")

    return errors

def invalid_semesterIds(semesterIds: str):
    real_semester_ids = get_semester_ids()
    foreign_keys = semesterIds.split(",")

    return [fk for fk in foreign_keys if fk not in real_semester_ids]

def is_float(number: str):
    try:
        float(number)
        return True
    except ValueError:
        return False

def is_positive_integer(value: str, include_zero = False):
    try:
        num = int(value)

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
    path = "../data/csvs/editfaculties.csv"

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
    improper_format = False
    for index, row in classrooms.iterrows():
        if not row.id or \
           not row["name"] or \
           not is_valid_number(row.capacity) or \
           not is_zero_or_one(row.hasComputers):
               improper_format = True

        if not row.id:
            print(f"ERROR: In classrooms.csv -> Row {index} has \"id\" of NULL.")
        if not row["name"]:
            print(f"ERROR: In classrooms.csv -> Row {index} has \"hasComputers\" of NULL.")
        if not is_valid_number(row.capacity):
            print(f"ERROR: In classrooms.csv -> In Row {index} \"capacity\" is not a valid number.")
        if not is_zero_or_one(row.hasComputers):
            print(f"ERROR: In classrooms.csv -> In Row {index} \"hasComputers\" is not \"0\" or \"1\".")

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
    path = "../data/csvs/editprofessors.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            professors = pd.read_csv(csv_file,
                                     delimiter=",",
                                     usecols=[0,1,2,3],
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
    required_properties = ["id", "firstName", "lastName","userId"]

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
           not row.firstName or \
           not row.lastName:
               improper_format = True

        if not row.id:
            print(f"ERROR: In professors.csv -> Row {index} has \"id\" of NULL.")
        if not row.firstName:
            print(f"ERROR: In professors.csv -> Row {index} has \"firstName\" of NULL.")
        if not row.lastName:
            print(f"ERROR: In professors.csv -> Row {index} has \"lastName\" of NULL.")

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


def analyze_semesters():
    path = "../data/csvs/editsemesters.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            semesters = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1,2,3,4,5,6,7],
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
    required_properties = ["id", "name", "season","numSemester", \
                           "hasOptionalSubjects", "numStudents", "facultyId", \
                           "userId"]

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

    faculty_ids = get_faculty_ids()
    improper_format = False
    for index, row in semesters.iterrows():
        if not row.id or \
           not row["name"] or \
           not is_valid_season(row.season) or \
           not is_positive_integer(row.numSemester) or \
           not is_positive_integer(row.hasOptionalSubjects, include_zero=True) or \
           not is_valid_number(row.numStudents) or \
           not row.facultyId in faculty_ids:
               improper_format = True

        if not row.id:
            print(f"ERROR: In semesters.csv -> Row {index} has \"id\" of NULL.")
        if not row["name"]:
            print(f"ERROR: In semesters.csv -> Row {index} has \"name\" of NULL.")
        if not is_valid_season(row.season):
            print(f"ERROR: In semesters.csv -> In Row {index} \"season\" is not \"W\" or \"S\".")
        if not is_valid_number(row.numSemester):
            print(f"ERROR: In semesters.csv -> In Row {index} \"numSemester\" is not a valid number.")
        if not is_positive_integer(row.hasOptionalSubjects, include_zero=True):
            print(f"ERROR: In semesters.csv -> In Row {index} \"hasOptionalSubjects\" is not a positive integer.")
        if not is_valid_number(row.numStudents):
            print(f"ERROR: In semesters.csv -> In Row {index} \"numStudents\" is not a valid number.")
        if not row.facultyId in faculty_ids:
            print(f"ERROR: In semesters.csv -> In Row {index} foreign key \"facultyId\" with value '{row.facultyId}' doesn't exist as \"id\" in faculties.")

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
    path = "../data/csvs/editsubjects.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            subjects = pd.read_csv(csv_file,
                                   delimiter=",",
                                   usecols=[0,1,2,3,4],
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
    required_properties = ["id", "name", "mandatory", "semesterIds", "userId"]

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
    improper_format = False
    for index, row in subjects.iterrows():
        invalid_sem_fks = invalid_semesterIds(row.semesterIds)

        if not row.id or \
           not row["name"] or \
           not is_zero_or_one(row.mandatory) or \
           invalid_sem_fks:
               improper_format = True

        if not row.id:
            print(f"ERROR: In subjects.csv -> Row {index} has \"id\" of NULL.")
        if not row["name"]:
            print(f"ERROR: In subjects.csv -> Row {index} has \"name\" of NULL.")
        if not is_zero_or_one(row.mandatory):
            print(f"ERROR: In subjects.csv -> In Row {index} \"mandatory\" is not \"0\" or \"1\".")
        if invalid_sem_fks:
            for invalid_fk in invalid_sem_fks:
                print(f"ERROR: In subjects.csv -> In Row {index} In column \"semesterIds\" value '{invalid_fk}' doesn't exist as \"id\" in semesters.")

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
    for semester_fks in subjects.semesterIds:
        sem_fks = semester_fks.split(",")
        seen = set()
        for fk in sem_fks:
            if fk in seen:
                duplicates = True
                print(f"ERROR: In subjects.csv -> In Row {index} In column \"semesterIds\" value '{fk}' is a duplicate.")
            seen.add(fk)

    if duplicate_fks:
        return False

    return True


def analyze_rasps():
    path = "../data/csvs/editrasps.csv"

    # File size below 50 MB?
    file_size = os.path.getsize(path) / (10**6) #MB
    if file_size > 50:
        print(f"ERROR: Maximum file size is 50 MB.")
        return False

    with open(path) as csv_file:
        # Is it a properly formatted csv?
        try:
            rasps = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1,2,3,4,5,6,7,8,9,10,11],
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
    required_properties = ["id", "professorId", "subjectId", "type", "group", \
                           "duration", "mandatory", "needsComputers", "totalGroups",
                           "color", "fixedAt", "userId"]

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
    professor_ids = get_professor_ids()
    subject_ids = get_subject_ids()
    improper_format = False

    for index, row in rasps.iterrows():
        fixedAt_errors = invalid_fixedAt(row.fixedAt, index)
        if not row.id or \
           row.professorId not in professor_ids or \
           row.subjectId not in subject_ids or \
           not row.type or \
           not row.group or \
           not is_positive_integer(row.duration) or \
           not is_zero_or_one(row.mandatory) or \
           not is_zero_or_one(row.needsComputers) or \
           not row.totalGroups or \
           fixedAt_errors:
               improper_format = True

        if not row.id:
            print(f"ERROR: In rasps.csv -> Row {index} has \"id\" of NULL.")
        if row.professorId not in professor_ids:
            print(f"ERROR: In rasps.csv -> In Row {index} In column \"professorId\" value '{row.professorId}' doesn't exist as \"id\" in professors.")
        if row.subjectId not in subject_ids:
            print(f"ERROR: In rasps.csv -> In Row {index} In column \"subjectId\" value '{row.subjectId}' doesn't exist as \"id\" in subjects.")
        if not row.type:
            print(f"ERROR: In rasps.csv -> Row {index} has \"type\" of NULL.")
        if not row.group:
            print(f"ERROR: In rasps.csv -> Row {index} has \"group\" of NULL.")
        if not is_positive_integer(row.duration):
            print(f"ERROR: In rasps.csv -> In Row {index} \"duration\" is not a positive integer.")
        if not is_zero_or_one(row.mandatory):
            print(f"ERROR: In rasps.csv -> In Row {index} \"mandatory\" is not \"0\" or \"1\".")
        if not is_zero_or_one(row.needsComputers):
            print(f"ERROR: In rasps.csv -> In Row {index} \"needsComputer\" is not \"0\" or \"1\".")
        if not row.totalGroups:
            print(f"ERROR: In rasps.csv -> Row {index} has \"totalGroups\" of NULL.")
        if fixedAt_errors:
            for error in fixedAt_errors:
                print(error)

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
print(analyze_classrooms())
print(analyze_professors())
print(analyze_semesters())
print(analyze_subjects())
print(analyze_rasps())
