import json
import pandas as pd
from utilities.my_types import Faculty
from utilities.general_utilities import load_settings

"""
1) Gets faculties from a .json file
2) Fits them into Faculty type
3) Returns the list of faculties
"""
def get_faculties():
    settings = load_settings()
    faculties_path = settings["path_faculties_json"]

    with open(faculties_path, "r", encoding="utf-8") as fp:
        faculties = json.load(fp)["faculties"]

    typed_faculties = []
    for faculty in faculties:
        faculty = [Faculty(**{field: fac[field] for field in Faculty._fields}) for fac in faculties]
        typed_faculties.append(faculty)

    return typed_faculties


"""
1) Gets faculties from a .csv file
2) Fits them into a pandas Dataframe and converts every cell to string
3) Returns the pandas Dataframe
"""
def get_faculty_ids_csv():
    settings = load_settings()
    faculties_path = settings["path_faculties_csv"]

    with open(faculties_path, encoding="utf-8") as csv_file:
        faculties = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1])

        faculties = pd.DataFrame(faculties).astype("str")

    return set(faculties.id)
