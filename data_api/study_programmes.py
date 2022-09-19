import json
import pandas as pd
from utilities.my_types import StudyProgramme
from utilities.general_utilities import load_settings

"""
1) Gets study programmes from a .json file
2) Fits them into StudyProgramme type
3) Returns the list of study programmes
"""
def get_study_programmes():
    settings = load_settings()
    study_programmes_path = settings["path_study_programmes_json"]

    with open(study_programmes_path, "r", encoding="utf-8") as fp:
        study_programmes = json.load(fp)["study_programmes"]

    typed_programmes = []
    for programme in study_programmes:
        programme = StudyProgramme(**{field: programme[field] for field in StudyProgramme._fields})
        typed_programmes.append(programme)

    return typed_programmes


"""
1) Gets study programmes from a .csv file
2) Fits them into a pandas Dataframe and converts every cell to string
3) Returns the pandas Dataframe
"""
def get_study_programme_ids_csv():
    settings = load_settings()
    study_programmes_path = settings["path_study_programmes_csv"]
    with open(study_programmes_path, encoding="utf-8") as csv_file:
        study_programmes = pd.read_csv(csv_file,
                                       delimiter=",",
                                       usecols=[0,1,2])

        study_programmes = pd.DataFrame(study_programmes).astype("str")

    return set(study_programmes.id)
