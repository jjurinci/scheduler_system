import json
from data_api.utilities.my_types import Faculty

def get_faculties():
    with open("database/input/faculties.json", "r") as fp:
        faculties = json.load(fp)["faculties"]

    typed_faculties = []
    for faculty in faculties:
        faculty["userId"] = None
        faculty = [Faculty(**{field: fac[field] for field in Faculty._fields}) for fac in faculties]
        typed_faculties.append(faculty)

    return typed_faculties
