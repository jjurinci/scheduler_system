import csv
import json
import os

"""
Reads a .csv file and converts it to a dictionary [column_name] = list(values).
"""
def csv_to_dict(path, name):
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")

        json_dict = {name: []}
        keys = []
        for index, row in enumerate(csv_reader):
            if index == 0:
                keys = row

            else:
                new_row = []
                for i, val in enumerate(row):
                    if "rrule" == keys[i]:
                        val = val[1:-1]
                    if "_ids" in keys[i]:
                        new_row.append(val.split(","))
                    elif val == "":
                        new_row.append(None)
                    else:
                        new_row.append(val)

                obj = dict(zip(keys, new_row))
                json_dict[name].append(obj)

        return json_dict


"""
Reads a .csv file and converts it to a dictionary [column_name] = list(values).
Specifically designed for .csvs with initial constraints.
"""
def constraints_csv_to_dict(path, name):
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")

        json_dict = {name: []}
        keys = []
        for index, row in enumerate(csv_reader):
            if index == 0:
                keys = row

            else:
                new_row = []
                for i, val in enumerate(row):
                    if val == "F" or val == "T" or "_id" in keys[i]:
                        new_row.append(val)
                    else:
                        all_times = []
                        times = val.split(",")
                        for time_i in range(0, len(times), 2):
                            first_hour, last_hour = times[time_i], times[time_i+1]
                            all_times.extend([first_hour, last_hour])
                        new_row.append(all_times)

                obj = dict(zip(keys, new_row))
                json_dict[name].append(obj)

        return json_dict


"""
Dumps a dictionary into a .json file.
"""
def dict_to_json(path, dictionary):
    with open(path, "w") as fp:
        json.dump(dictionary, fp)

def run():
    #university                  = csv_to_dict("database/input/universities.csv",       "university")
    #faculties                    = csv_to_dict("database/input/faculties.csv",          "faculties")
    #study_programmes             = csv_to_dict("database/input/study_programmes.csv",   "study_programmes")
    semesters                    = csv_to_dict("database/input/semesters.csv",          "semesters")
    subjects                     = csv_to_dict("database/input/subjects.csv",           "subjects")
    rasps                        = csv_to_dict("database/input/rasps.csv",              "rasps")
    classrooms                   = csv_to_dict("database/input/classrooms.csv",         "classrooms")
    professors                   = csv_to_dict("database/input/professors.csv",         "professors")
    day_structure                = csv_to_dict("database/input/day_structure.csv",      "day_structure")
    start_end_year               = csv_to_dict("database/input/start_end_year.csv",     "start_end_year")

    dir_path = "temp_storage/database/input"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    dir_path = "temp_storage/database/constraints"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    #dict_to_json("database/input/university.json",              university)
    #dict_to_json("temp_storage/database/input/faculties.json",          faculties)
    #dict_to_json("temp_storage/database/input/study_programmes.json",   study_programmes)
    dict_to_json("temp_storage/database/input/semesters.json",          semesters)
    dict_to_json("temp_storage/database/input/subjects.json",           subjects)
    dict_to_json("temp_storage/database/input/rasps.json",              rasps)
    dict_to_json("temp_storage/database/input/classrooms.json",         classrooms)
    dict_to_json("temp_storage/database/input/professors.json",         professors)
    dict_to_json("temp_storage/database/input/day_structure.json",      day_structure)
    dict_to_json("temp_storage/database/input/start_end_year.json", start_end_year)

    classroom_available = constraints_csv_to_dict("database/constraints/classroom_available.csv", "classroom_available")
    professor_available = constraints_csv_to_dict("database/constraints/professor_available.csv", "professor_available")

    dict_to_json("temp_storage/database/constraints/classroom_available.json", classroom_available)
    dict_to_json("temp_storage/database/constraints/professor_available.json", professor_available)
