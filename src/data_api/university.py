import json
from data_api.utilities.my_types import University

def get_university():
    with open("database/input/university.json", "r") as fp:
        university = json.load(fp)["university"]

    university["user_id"] = None
    typed_university = University(**{field: university[field] for field in University._fields})

    return typed_university
