import json
from data_api.utilities.my_types import Rasp
from data_api.semesters import get_semesters
from data_api.subjects  import get_subjects

def get_rasps():
    with open("database/input/rasps.json", "r") as fp:
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


def get_rasps_by_season(winter = False):
    chosen_season = "W" if winter else "S"

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
