import json
from data_api.utilities.my_types import Study_Programme

def get_study_programmes():
    with open("database/input/study_programmes.json", "r") as fp:
        study_programmes = json.load(fp)["study_programmes"]

    typed_programmes = []
    for programme in study_programmes:
        programme["user_id"] = None
        programme = Study_Programme(**{field: programme[field] for field in Study_Programme._fields})
        typed_programmes.append(programme)

    return typed_programmes
