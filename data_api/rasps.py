import json
from dateutil.rrule import rrulestr
from utilities.my_types import Rasp
import data_api.semesters as seme_api
import data_api.time_structure as time_api
from data_api.subjects  import get_subjects
from utilities.general_utilities import load_settings

"""
1) Gets rasps from a .json file
2) Fits them into Rasp type
3) Returns the list of rasps
"""
def get_rasps():
    settings = load_settings()
    rasp_path = settings["path_rasps_json"]
    with open(rasp_path, "r") as fp:
        rasps = json.load(fp)["rasps"]

    subjects = get_subjects()
    subjects_dict = {s.id:s for s in subjects}

    rasp_groups = {}
    for rasp in rasps:
        key = (rasp["subject_id"], rasp["type"])
        if key not in rasp_groups:
            rasp_groups[key] = 1
        else:
            rasp_groups[key] += 1

    time_structure = time_api.get_time_structure()

    typed_rasps = []
    for rasp in rasps:
        subject = subjects_dict[rasp["subject_id"]]
        total_groups_key = (rasp["subject_id"], rasp["type"])

        rasp["duration"] = int(rasp["duration"])
        rasp["mandatory_in_semester_ids"] = subject.mandatory_in_semester_ids
        rasp["optional_in_semester_ids"] = subject.optional_in_semester_ids
        rasp["needs_computers"] = True if rasp["needs_computers"] == "1" else False
        rasp["total_groups"] = rasp_groups[total_groups_key]
        rasp["random_dtstart_weekday"] = True if rasp["random_dtstart_weekday"] == "1" else False
        rrule = rasp["rrule"]
        rrule = rrule.replace("\\n", "\n")
        rasp["rrule"] = rrule
        rrule_obj = rrulestr(rrule)

        rasp["fixed_hour"] = None
        if rrule_obj._dtstart.hour != 0:
            first_date = list(rrule_obj)[0]
            hour = time_api.date_to_index(first_date, time_structure)[2]
            rasp["fixed_hour"] = hour

        rasp = Rasp(**{field: rasp[field] for field in Rasp._fields})
        typed_rasps.append(rasp)

    return typed_rasps


"""
Returns rasps filtered by season (winter/summer).
"""
def get_rasps_by_season(winter = False):
    rasps = get_rasps()

    semesters = seme_api.get_winter_semesters_dict() if winter else \
                seme_api.get_summer_semesters_dict()

    season_rasps = []
    for rasp in rasps:
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        sem_id = sem_ids[0]
        if sem_id in semesters:
            season_rasps.append(rasp)

    return season_rasps

"""
Returns:
    1) rasps held in winter semesters
    2) rasps held in summer semesters
    3) approximate number of students per rasp
"""
def get_rasps_with_students():
    rasps = get_rasps()
    winter_semesters = seme_api.get_winter_semesters_dict()
    students_per_rasp = seme_api.get_students_per_rasp_estimate(rasps)

    winter_rasps, summer_rasps = [], []
    for rasp in rasps:
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        if sem_ids[0] in winter_semesters:
            winter_rasps.append(rasp)
        else:
            summer_rasps.append(rasp)

    return winter_rasps, summer_rasps, students_per_rasp

