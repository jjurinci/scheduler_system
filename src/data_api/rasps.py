import json
from dateutil.rrule import rrulestr
from data_api.utilities.my_types import Rasp
import data_api.semesters as seme_api
from data_api.subjects  import get_subjects

"""
1) Gets rasps from a .json file
2) Fits them into Rasp type
3) Returns the list of rasps
"""
def get_rasps():
    with open("database/input/rasps.json", "r") as fp:
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

    typed_rasps = []
    for rasp in rasps:
        subject = subjects_dict[rasp["subject_id"]]
        total_groups_key = (rasp["subject_id"], rasp["type"])

        rasp["duration"] = int(rasp["duration"])
        rasp["mandatory_in_semester_ids"] = subject.mandatory_in_semester_ids
        rasp["optional_in_semester_ids"] = subject.optional_in_semester_ids
        rasp["needs_computers"] = True if rasp["needs_computers"] == "1" else False
        rasp["total_groups"] = rasp_groups[total_groups_key]
        rasp["random_dtstart_weekday"] = True if rasp["random_dtstart_weekday"] else False
        rasp["user_id"] = None
        rrule = rasp["rrule"]
        rrule = rrule[1:-1].replace("\\n", "\n")
        rasp["rrule"] = rrule
        rrule_obj = rrulestr(rrule)
        rasp["fixed_hour"] = True if rrule_obj._dtstart.hour != 0 else False
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
