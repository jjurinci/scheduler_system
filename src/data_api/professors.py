import json
import numpy as np
import pandas as pd
from collections import defaultdict
from utilities.my_types import Professor

"""
1) Gets professors from a .json file
2) Fits them into Professor type
3) Returns the list of professors
"""
def get_professors():
    with open("database/input/professors.json", "r") as fp:
        professors = json.load(fp)["professors"]

    typed_professors = []
    for prof in professors:
        prof["user_id"] = None
        prof = Professor(**{field: prof[field] for field in Professor._fields})
        typed_professors.append(prof)

    return typed_professors


"""
1) Gets professors from a .csv file
2) Fits them into a pandas Dataframe and converts every cell to string
3) Returns the pandas Dataframe
"""
def get_professor_ids_csv():
    path = "database/input/csvs/professors.csv"
    with open(path) as csv_file:
        professors = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2])

        professors = pd.DataFrame(professors).astype("str")

    return set(professors.id)


"""
Returns initial professors constraints from a .json file.
"""
def get_professors_constraints():
    with open("database/constraints/professor_available.json", "r") as fp:
        prof_available = json.load(fp)["professor_available"]
    return prof_available


"""
Utility function that transforms constraint times (e.g. gotten from .json)
to list of integers. The list denotes a block of time.
"""
def transform_prof_time(ugly_time):
    if ugly_time == "F":
        return [1]*16
    elif ugly_time == "T":
        return [0]*16
    else:
        pretty_time = [1]*16
        for i in range(0,len(ugly_time), 2):
            start, finish = int(ugly_time[i]), int(ugly_time[i+1])
            for j in range(start, finish+1):
                pretty_time[j-1] = 0
        return pretty_time


"""
Returns dictionary:
    profs_occupued[prof_id] = np.ones[NUM_WEEKS][NUM_DAYS][NUM_HOURS]
after it is filled with zeros according to the initial constraints.
"""
def get_professors_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rasps):
    professor_ids = set(rasp.professor_id for rasp in rasps)
    prof_constraints  = get_professors_constraints()

    #1 = [prof.id][week,day,hour] IS OCCUPIED, 0 = [prof.id][week,day,hour] IS FREE
    profs_occupied = defaultdict(lambda: np.ones(shape=(NUM_WEEKS,NUM_DAYS,NUM_HOURS), dtype=np.uint8))
    done_professors = {}
    for avail in prof_constraints:
        prof_id = avail["professor_id"]
        if prof_id not in professor_ids:
            continue

        done_professors[prof_id] = True

        monday    = transform_prof_time(avail["monday"])
        tuesday   = transform_prof_time(avail["tuesday"])
        wednesday = transform_prof_time(avail["wednesday"])
        thursday  = transform_prof_time(avail["thursday"])
        friday    = transform_prof_time(avail["friday"])

        for week in range(NUM_WEEKS):
            profs_occupied[prof_id][week][0] = monday
            profs_occupied[prof_id][week][1] = tuesday
            profs_occupied[prof_id][week][2] = wednesday
            profs_occupied[prof_id][week][3] = thursday
            profs_occupied[prof_id][week][4] = friday

    for prof_id in professor_ids:
        if prof_id not in done_professors:
            for week in range(NUM_WEEKS):
                profs_occupied[prof_id][week][0] = [0]*16
                profs_occupied[prof_id][week][1] = [0]*16
                profs_occupied[prof_id][week][2] = [0]*16
                profs_occupied[prof_id][week][3] = [0]*16
                profs_occupied[prof_id][week][4] = [0]*16

    return dict(**profs_occupied)
