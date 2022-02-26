import json
import pandas as pd
from data_api.utilities.my_types import Faculty

"""
1) Gets faculties from a .json file
2) Fits them into Faculty type
3) Returns the list of faculties
"""
def get_faculties():
    with open("database/input/faculties.json", "r") as fp:
        faculties = json.load(fp)["faculties"]

    typed_faculties = []
    for faculty in faculties:
        faculty["user_id"] = None
        faculty = [Faculty(**{field: fac[field] for field in Faculty._fields}) for fac in faculties]
        typed_faculties.append(faculty)

    return typed_faculties


"""
1) Gets faculties from a .csv file
2) Fits them into a pandas Dataframe and converts every cell to string
3) Returns the pandas Dataframe
"""
def get_faculty_ids_csv():
    path = "database/input/csvs/faculties.csv"
    with open(path) as csv_file:
        faculties = pd.read_csv(csv_file,
                                delimiter=",",
                                usecols=[0,1])

        faculties = pd.DataFrame(faculties).astype("str")

    return set(faculties.id)
