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

    semesters = [Semester(**{field: sem[field] for field in Semester._fields}) for sem in semesters]
    return semesters


def get_professors():
    with open("data/professors.json", "r") as fp:
        professors = json.load(fp)["professors"]

    professors = [Professor(**{field: prof[field] for field in Professor._fields}) for prof in professors]
    return professors


def get_classrooms():
    with open("data/classrooms.json", "r") as fp:
        classrooms = json.load(fp)["classrooms"]

    classrooms = [Classroom(**{field: classr[field] for field in Classroom._fields}) for classr in classrooms]
    return classrooms


def get_subjects():
    with open("data/subjects.json", "r") as fp:
        subjects = json.load(fp)["subjects"]

    new_subjects = []
    for sub in subjects:
        sub["rasps"] = None
        sub["semesterIds"] = tuple(sub["semesterIds"])
        new_subject = Subject(**{field: sub[field] for field in Subject._fields})
        new_subjects.append(new_subject)

    return new_subjects


def get_rasps():
    with open("data/rasps.json", "r") as fp:
        rasps = json.load(fp)["rasps"]

    rasps = [Rasp(**{field: int(rasp[field]) if field=="duration"
                                             else rasp[field]
                                             for field in Rasp._fields}) for rasp in rasps]
    return rasps


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
