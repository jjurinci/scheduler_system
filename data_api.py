import json
from my_types import Faculty, Semester, Subject, Classroom, Rasp, Professor


def get_faculties():
    with open("data/faculties.json", "r") as fp:
        faculties = json.load(fp)["faculties"]

    faculties = [Faculty(**{field: fac[field] for field in Faculty._fields}) for fac in faculties]
    return faculties


def get_semesters():
    with open("data/semesters.json", "r") as fp:
        semesters = json.load(fp)["semesters"]

    typed_semesters = []
    for semester in semesters:
        semester["numSemester"] = int(semester["numSemester"])
        semester["hasOptionalSubjects"] = int(semester["hasOptionalSubjects"])
        semester["numStudents"] = int(semester["numStudents"])
        semester = Semester(**{field: semester[field] for field in Semester._fields})
        typed_semesters.append(semester)

    return typed_semesters


def get_professors():
    with open("data/professors.json", "r") as fp:
        professors = json.load(fp)["professors"]

    professors = [Professor(**{field: prof[field] for field in Professor._fields}) for prof in professors]
    return professors


def get_classrooms():
    with open("data/classrooms.json", "r") as fp:
        classrooms = json.load(fp)["classrooms"]

    typed_classrooms = []
    for classroom in classrooms:
        classroom["capacity"] = int(classroom["capacity"])
        classroom["hasComputers"] = True if classroom["hasComputers"]=="1" else False
        classroom = Classroom(**{field: classroom[field] for field in Classroom._fields})
        typed_classrooms.append(classroom)

    return typed_classrooms


def get_subjects():
    with open("data/subjects.json", "r") as fp:
        subjects = json.load(fp)["subjects"]

    typed_subjects = []
    for subject in subjects:
        subject["rasps"] = None
        subject["semesterIds"] = tuple(subject["semesterIds"])
        subject["mandatory"] = True if subject["mandatory"]=="1" else False
        subject = Subject(**{field: subject[field] for field in Subject._fields})
        typed_subjects.append(subject)

    return typed_subjects


def get_rasps():
    with open("data/rasps.json", "r") as fp:
        rasps = json.load(fp)["rasps"]

    typed_rasps = []
    for rasp in rasps:
        rasp["duration"] = int(rasp["duration"])
        rasp["mandatory"] = True if rasp["mandatory"] == "1" else False
        rasp["needsComputers"] = True if rasp["needsComputers"] == "1" else False
        rasp["totalGroups"] = int(rasp["totalGroups"])
        rasp = Rasp(**{field: rasp[field] for field in Rasp._fields})
        typed_rasps.append(rasp)

    return typed_rasps


def get_winter_semesters():
    semesters = get_semesters()
    semesters = [sem for sem in semesters if sem.season == "W"]
    return semesters


def get_summer_semesters():
    semesters = get_semesters()
    semesters = [sem for sem in semesters if sem.season == "S"]
    return semesters


def get_rasps_by_season(winter = False, summer = False):
    chosen_season = "S" if summer else "W"

    semesters = get_semesters()
    rasps = get_rasps()
    subjects = get_subjects()

    subjects_dict = {}
    semesters_dict = {}

    for subject in subjects:
        subjects_dict[subject.id] = subject

    for semester in semesters:
        semesters_dict[semester.id] = semester

    season_rasps = []
    for rasp in rasps:
        subject_id = rasp.subjectId
        semester_ids = subjects_dict[subject_id].semesterIds

        for semester_id in semester_ids:
            semester = semesters_dict[semester_id]
            if semester.season == chosen_season:
                season_rasps.append(rasp)
                break

    return season_rasps


def get_professors_by_ids(professor_ids):
    professors = get_professors()
    professors = [prof for prof in professors if prof.id in professor_ids]
    return professors

def get_subject_by_id(subject_id):
    subjects = get_subjects()
    for sub in subjects:
        if sub.id == subject_id:
            return sub
    return -1
