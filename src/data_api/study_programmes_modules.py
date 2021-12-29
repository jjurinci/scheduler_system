import json
from data_api.utilities.my_types import Study_Programme_Module

def get_study_programmes():
    with open("database/input/study_programmes_modules.json", "r") as fp:
        study_programmes_modules = json.load(fp)["study_programmes_modules"]

    typed_programme_modules = []
    for module in study_programmes_modules:
        module["user_id"] = None
        module = Study_Programme_Module(**{field: module[field] for field in Study_Programme_Module._fields})
        typed_programme_modules.append(module)

    return typed_programme_modules
