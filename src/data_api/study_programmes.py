import json
import pandas as pd
from data_api.utilities.my_types import StudyProgramme

def get_study_programmes():
    with open("database/input/study_programmes.json", "r") as fp:
        study_programmes = json.load(fp)["study_programmes"]

    typed_programmes = []
    for programme in study_programmes:
        programme["user_id"] = None
        programme = StudyProgramme(**{field: programme[field] for field in StudyProgramme._fields})
        typed_programmes.append(programme)

    return typed_programmes


def get_study_programme_ids_csv():
    path = "database/input/csvs/study_programmes.csv"
    with open(path) as csv_file:
        study_programmes = pd.read_csv(csv_file,
                                       delimiter=",",
                                       usecols=[0,1,2])

        study_programmes = pd.DataFrame(study_programmes).astype("str")

    return set(study_programmes.id)

