import json
from dateutil.rrule import rrulestr
from data_api.utilities.my_types import Rasp
from data_api.semesters import get_semesters
from data_api.subjects  import get_subjects

def test_rrule(the_rrule_str):
    from dateutil.rrule import rrule, rrulestr

    rrule = rrulestr(the_rrule_str)
    print(rrule)


def get_rasps():
    with open("database/input/rasps.json", "r") as fp:
        rasps = json.load(fp)["rasps"]

    subjects = get_subjects()
    subjects_dict = {s.id:s for s in subjects}

    rasp_groups = {}
    for rasp in rasps:
        key = (rasp["subjectId"], rasp["type"])
        if key not in rasp_groups:
            rasp_groups[key] = 1
        else:
            rasp_groups[key] += 1

    typed_rasps = []
    for rasp in rasps:
        subject = subjects_dict[rasp["subjectId"]]
        total_groups_key = (rasp["subjectId"], rasp["type"])

        rasp["duration"] = int(rasp["duration"])
        rasp["mandatory_in_semesterIds"] = subject.mandatory_in_semesterIds
        rasp["optional_in_semesterIds"] = subject.optional_in_semesterIds
        rasp["needsComputers"] = True if rasp["needsComputers"] == "1" else False
        rasp["totalGroups"] = rasp_groups[total_groups_key]
        rasp["random_dtstart_weekday"] = True if rasp["random_dtstart_weekday"] else False
        rrule = rasp["rrule"]
        rrule = rrule[1:-1].replace("\\n", "\n")
        #test_rrule(rrule)
        rasp["rrule"] = rrule

        rrule_obj = rrulestr(rrule)
        rasp["fixed_hour"] = True if rrule_obj._dtstart.hour != 0 else False
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
        semester_ids = subjects_dict[subject_id].mandatory_in_semesterIds
        semester_ids += subjects_dict[subject_id].optional_in_semesterIds

        for semester_id in semester_ids:
            semester = semesters_dict[semester_id]
            if semester.season == chosen_season:
                season_rasps.append(rasp)
                break

    return season_rasps
