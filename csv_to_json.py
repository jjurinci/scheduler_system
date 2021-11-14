import csv
import json

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
                    if "Ids" in keys[i]:
                        new_row.append(val.split(","))
                    elif val == "":
                        new_row.append(None)
                    else:
                        new_row.append(val)

                obj = dict(zip(keys, new_row))
                json_dict[name].append(obj)

        return json_dict


def dict_to_json(path, dictionary):
    with open(path, "w") as fp:
        json.dump(dictionary, fp)


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
                    if val == "F" or val == "T" or "Id" in keys[i]:
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

faculties  = csv_to_dict("data/faculties.csv",  "faculties")
semesters  = csv_to_dict("data/semesters.csv",  "semesters")
professors = csv_to_dict("data/professors.csv", "professors")
classrooms = csv_to_dict("data/classrooms.csv", "classrooms")
subjects   = csv_to_dict("data/subjects.csv",   "subjects")
rasps      = csv_to_dict("data/rasps.csv",      "rasps")

dict_to_json("data/faculties.json",  faculties)
dict_to_json("data/semesters.json",  semesters)
dict_to_json("data/professors.json", professors)
dict_to_json("data/classrooms.json",  classrooms)
dict_to_json("data/subjects.json",   subjects)
dict_to_json("data/rasps.json",      rasps)

classroom_available = constraints_csv_to_dict("constraints/classroom_available.csv", "classroomAvailable")
professor_available = constraints_csv_to_dict("constraints/professor_available.csv", "professorAvailable")

dict_to_json("constraints/classroom_available.json", classroom_available)
dict_to_json("constraints/professor_available.json", professor_available)
