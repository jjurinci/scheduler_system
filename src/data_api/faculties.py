import json
from data_api.utilities.my_types import Faculty

def get_faculties():
    with open("database/input/faculties.json", "r") as fp:
        faculties = json.load(fp)["faculties"]

    faculties = [Faculty(**{field: fac[field] for field in Faculty._fields}) for fac in faculties]
    return faculties
