import json
import pandas as pd
from utilities.my_types import Subject
from utilities.general_utilities import load_settings

"""
1) Gets subjects from a .json file
2) Fits them into Subject type
3) Returns the list of subjects
"""
def get_subjects():
    settings = load_settings()
    subjects_path = settings["path_subjects_json"]
    with open(subjects_path, "r", encoding="utf-8") as fp:
        subjects = json.load(fp)["subjects"]

    typed_subjects = []
    for subject in subjects:
        subject["rasps"] = None
        subject["mandatory_in_semester_ids"] = tuple(subject["mandatory_in_semester_ids"]) if subject["mandatory_in_semester_ids"] != [''] else ()
        subject["optional_in_semester_ids"] = tuple(subject["optional_in_semester_ids"]) if subject["optional_in_semester_ids"] != [''] else ()
        subject = Subject(**{field: subject[field] for field in Subject._fields})
        typed_subjects.append(subject)

    return typed_subjects


"""
1) Gets subjects from a .csv file
2) Fits them into a pandas Dataframe and converts every cell to string
3) Returns the pandas Dataframe
"""
def get_subject_ids_csv():
    settings = load_settings()
    subjects_path = settings["path_subjects_csv"]
    with open(subjects_path, encoding="utf-8") as csv_file:
        subjects = pd.read_csv(csv_file,
                               delimiter=",",
                               usecols=[0,1,2,3])

        subjects = pd.DataFrame(subjects).astype("str")

    return set(subjects.id)
