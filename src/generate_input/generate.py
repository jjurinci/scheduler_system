import csv
import json
import random
import math
import string
from itertools import product

NUM_DAYS, NUM_HOURS = 5, 16


def get_subject_ids():
    ALFABET = string.ascii_uppercase
    names = ["".join(x) for x in product(ALFABET, repeat=4)]
    name_i = 0
    while True:
        yield names[name_i]
        name_i += 1 % len(names)


def get_professor_ids():
    alfabet = string.ascii_lowercase
    names = list(reversed(["".join(x) for x in product(alfabet, repeat=4)]))
    name_i = 0
    while True:
        yield names[name_i]
        name_i += 1 % len(names)


def get_semester_ids():
    ALFABET = string.ascii_uppercase
    names = ["".join(x) for x in product(ALFABET, repeat=4)]
    random.shuffle(names)
    name_i = 0
    while True:
        yield names[name_i]
        name_i += 1 % len(names)


def get_room_ids():
    numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    names = ["".join(x) for x in product(numbers, repeat=5)]
    name_i = 0
    while True:
        yield names[name_i]
        name_i += 1 % len(names)


def get_all_rrules():
    with open("generate_input/rrule_data.json", "r") as j:
        rrules_pool = json.load(j)
    return rrules_pool


def get_one_rrule(rrules_pool):
    roll = random.random()

    # DAILY
    if roll > 0.85:
        return random.choice(rrules_pool["daily"])

    # BIWEEKLY, TRIWEEKLY, etc
    elif roll > 0.80 and roll <= 0.85:
        return random.choice(rrules_pool["weekly_other"])

    # MONTHLY:
    elif roll == 0.80:
        return random.choice(rrules_pool["monthly"])

    # NORMAL WEEKLY
    else:
        return rrules_pool["weekly"][0]


def get_types():
    roll = random.random()
    if roll > 0.9:
        return ["P", "V", "S"]
    else:
        return ["P", "V"]


def get_groups():
    roll = random.random()
    if roll > 0.98:
        return ["1", "2", "3", "4"]
    elif roll > 0.97 and roll <= 0.98:
        return ["1", "2", "3"]
    elif roll > 0.95 and roll <= 0.96:
        return ["1", "2"]
    else:
        return ["1"]


def get_duration():
    roll = random.random()
    if roll > 0.98:
        return "4"
    elif roll > 0.97 and roll <= 0.98:
        return "3"
    elif roll > 0.95 and roll <= 0.96:
        return "1"
    else:
        return "2"


def get_needs_computer():
    roll = random.random()
    if roll > 0.5:
        return "0"
    else:
        return "1"


def get_random_dtstart_weekday(rrule: str):
    freq = find_freq(rrule)
    if freq == "DAILY":
        return "0"
    else:
        roll = random.random()
        if roll > 0.8:
            return "0"
        else:
            return "1"


def get_num_students():
    roll = random.random()

    if roll > 0.8:
        return random.randint(90,120)
    else:
        return random.randint(45,65)


def find_freq(rrule: str):
    parts = rrule.split(";")
    for part in parts:
        idx = part.find("FREQ=")
        if idx != -1:
            return part[idx + len("FREQ=") :]
    raise AssertionError


def generate_professors(NUM_RASPS):
    possible_professors_ratio = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    NUM_PROFESSORS = math.ceil(random.choice(possible_professors_ratio) * NUM_RASPS)
    professors = []
    professor_ids = get_professor_ids()
    for _ in range(NUM_PROFESSORS):
        prof_id = next(professor_ids)
        professor = {"id": prof_id + "_prof", "first_name": prof_id + "_firstName", "last_name": prof_id + "_lastName"}
        professors.append(professor)
    return professors


def generate_rasps(NUM_RASPS):
    rasps = []
    rrules_pool = get_all_rrules()
    subject_ids   = get_subject_ids()
    professors = generate_professors(NUM_RASPS)
    cnt_rasps = 0
    while cnt_rasps < NUM_RASPS:
        subject_id   = next(subject_ids)
        types = get_types()
        for type_ in types:
            groups = get_groups()
            for group in groups:
                rasp_id      = subject_id + "_" + type_ + group
                professor_id = random.choice(professors)["id"]
                duration     = get_duration()
                needs_pc     = get_needs_computer()
                fix_room_id  = None
                rrule        = get_one_rrule(rrules_pool)
                rnd_dt_wday  = get_random_dtstart_weekday(rrule)

                rasp = {"id": rasp_id, "professor_id": professor_id,
                        "subject_id":subject_id, "type":type_, "group":group,
                        "duration":duration, "needs_computers":needs_pc,
                        "fix_at_room_id": fix_room_id, "random_dtstart_weekday":rnd_dt_wday,
                        "rrule":rrule}
                rasps.append(rasp)
                cnt_rasps += 1
                if cnt_rasps >= NUM_RASPS:
                    break
            if cnt_rasps >= NUM_RASPS:
                break
    return rasps, professors


def visualize_rasp_per_prof(rasps):
    rasp_per_prof = {}
    for rasp in rasps:
        if rasp["professor_id"] not in rasp_per_prof:
            rasp_per_prof[rasp["professor_id"]] = 1
        else:
            rasp_per_prof[rasp["professor_id"]] += 1

    print(sorted(rasp_per_prof.items(), key=lambda x: x[1], reverse=True))


def generate_subject_rasps(rasps):
    subject_rasps = {}
    for rasp in rasps:
        if rasp["subject_id"] not in subject_rasps:
            subject_rasps[rasp["subject_id"]] = [rasp]
        else:
            subject_rasps[rasp["subject_id"]].append(rasp)
    return subject_rasps


def generate_semesters(NUM_RASPS):
    possible_semesters_ratio = [0.05, 0.08, 0.1, 0.15, 0.2]
    NUM_SEMESTERS = math.ceil(random.choice(possible_semesters_ratio) * NUM_RASPS)
    semesters, semesters_dict = [], {}
    semester_ids = get_semester_ids()
    for _ in range(NUM_SEMESTERS):
        sem_id = next(semester_ids)
        num_students = get_num_students()
        semester = {"id": sem_id + "_sem", "num_semester": "1", "season": "W",
                    "has_optional_subjects": "0",
                    "num_students": str(num_students),
                    "study_programme_id": "abcd"}
        semesters.append(semester)
        semesters_dict[sem_id + "_sem"] = semester

    return semesters_dict


def visualize_semester_mand_opts(rasps, subjects_dict, semesters_dict):
    subject_rasps = generate_subject_rasps(rasps)
    visualize_nums = {sem_id: (0,0) for sem_id in semesters_dict}
    for subject_id, subject in subjects_dict.items():
        mandatory = bool(subject["mandatory_in_semester_ids"])
        optional  = bool(subject["optional_in_semester_ids"])
        len_rasps   = len(subject_rasps[subject_id])
        if mandatory:
            for sem_id in subject["mandatory_in_semester_ids"]:
                mands, opts = visualize_nums[sem_id]
                visualize_nums[sem_id] = (mands + len_rasps, opts)
        if optional:
            for sem_id in subject["optional_in_semester_ids"]:
                mands, opts = visualize_nums[sem_id]
                visualize_nums[sem_id] = (mands, opts + len_rasps)

    total = sum(mand+opts for mand,opts in visualize_nums.values())
    print(visualize_nums)
    print("TOTAL: ", total)


def generate_subjects(rasps, semesters_dict):
    subjects_dict = {}
    subject_ids = set([rasp["subject_id"] for rasp in rasps])

    for subject_id in subject_ids:
        subject = {"id":subject_id, "name": subject_id + " name", "mandatory_in_semester_ids": [], "optional_in_semester_ids": []}
        subjects_dict[subject_id] = subject

    NUM_SEMESTERS = len(semesters_dict)
    has_optionals = set()
    semesters_id_list = list(semesters_dict.keys())
    semester_idx = 0
    for subject_id in subjects_dict:
        roll = random.random()
        mandatory = False if roll > 0.6 else True
        semester_id = semesters_id_list[semester_idx]
        if mandatory:
            subjects_dict[subject_id]["mandatory_in_semester_ids"].append(semester_id)
        else:
            subjects_dict[subject_id]["optional_in_semester_ids"].append(semester_id)
            has_optionals.add(semester_id)
        semester_idx = (semester_idx + 1) % NUM_SEMESTERS

    for semester_id in has_optionals:
        semesters_dict[semester_id]["has_optional_subjects"] = "1"

    #visualize_semester_mand_opts(rasps, subjects_dict, semesters_dict)
    return subjects_dict


def generate_rooms(NUM_RASPS, semesters_dict):
    room_ids = get_room_ids()
    num_students_range = sorted(list(set(int(semester["num_students"]) for semester in semesters_dict.values())))
    differences = []
    for i, num_students in enumerate(num_students_range):
        if i+1 >= len(num_students_range):
            break
        differences.append(abs(num_students - num_students_range[i+1]))
    avg_diff = math.ceil(sum(diff for diff in differences) / len(differences))

    possible_room_ratios = [0.1, 0.12, 0.15, 0.16, 0.17, 0.18, 0.22, 0.3]
    NUM_ROOMS = math.ceil(random.choice(possible_room_ratios) * NUM_RASPS)
    possible_has_computers_ratios = [0.2, 0.3, 0.35, 0.4, 0.5]
    NUM_COMPUTER_ROOMS = math.ceil(random.choice(possible_has_computers_ratios) * NUM_ROOMS)

    rooms_dict = {}
    for _ in range(NUM_ROOMS):
        room_id = next(room_ids) + "_room"
        capacity = random.choice(num_students_range) + avg_diff
        room = {"id": room_id, "name": room_id, "capacity": str(capacity), "has_computers": "0"}
        rooms_dict[room_id] = room

    computer_rooms = random.sample(list(rooms_dict.keys()), NUM_COMPUTER_ROOMS)
    for room_id in computer_rooms:
        rooms_dict[room_id]["has_computers"] = "1"

    max_capacity_room = random.choice(list(rooms_dict.keys()))
    rooms_dict[max_capacity_room]["capacity"] = str(max(num_students_range) + avg_diff)

    return rooms_dict


def create_csvs(rasps, professors, semesters_dict, subjects_dict, rooms_dict):
    with open("generate_input/csvs/rasps.csv", "w") as f:
        header_rasp = ["id", "professor_id", "subject_id", "type", "group", "duration", "needs_computers", "fix_at_room_id", "random_dtstart_weekday", "rrule"]
        writer = csv.writer(f)
        writer.writerow(header_rasp)
        for rasp in rasps:
            rrule = '\"' + rasp["rrule"] + '\"'
            row = [rasp["id"], rasp["professor_id"], rasp["subject_id"], rasp["type"], rasp["group"], rasp["duration"], rasp["needs_computers"], rasp["fix_at_room_id"], rasp["random_dtstart_weekday"], rrule]
            writer.writerow(row)

    with open("generate_input/csvs/professors.csv", "w") as f:
        header_prof = ["id", "first_name", "last_name"]
        writer = csv.writer(f)
        writer.writerow(header_prof)
        for prof in professors:
            row = [prof["id"], prof["first_name"], prof["last_name"]]
            writer.writerow(row)

    with open("generate_input/csvs/semesters.csv", "w") as f:
        header_semester = ["id", "num_semester", "season", "has_optional_subjects", "num_students", "study_programme_id"]
        writer = csv.writer(f)
        writer.writerow(header_semester)
        for sem in semesters_dict.values():
            row = [sem["id"], sem["num_semester"], sem["season"], sem["has_optional_subjects"], sem["num_students"], sem["study_programme_id"]]
            writer.writerow(row)

    with open("generate_input/csvs/subjects.csv", "w") as f:
        header_subject = ["id", "name", "mandatory_in_semester_ids", "optional_in_semester_ids"]
        writer = csv.writer(f)
        writer.writerow(header_subject)
        for sub in subjects_dict.values():
            mandatory_in_semester_ids = ",".join(sub["mandatory_in_semester_ids"])
            optional_in_semester_ids  = ",".join(sub["optional_in_semester_ids"])
            row = [sub["id"], sub["name"], mandatory_in_semester_ids, optional_in_semester_ids]
            writer.writerow(row)

    with open("generate_input/csvs/classrooms.csv", "w") as f:
        header_classroom = ["id", "name", "capacity", "has_computers"]
        writer = csv.writer(f)
        writer.writerow(header_classroom)
        for room in rooms_dict.values():
            row = [room["id"], room["name"], room["capacity"], room["has_computers"]]
            writer.writerow(row)

    with open("generate_input/csvs/classroom_available.csv", "w") as f:
        header_classroom_available = ["room_id", "monday", "tuesday", "wednesday", "thursday", "friday"]
        writer = csv.writer(f)
        writer.writerow(header_classroom_available)

    with open("generate_input/csvs/professor_available.csv", "w") as f:
        header_professor_available = ["professor_id", "monday", "tuesday", "wednesday", "thursday", "friday"]
        writer = csv.writer(f)
        writer.writerow(header_professor_available)


def create_jsons(rasps, professors, semesters_dict, subjects_dict, rooms_dict):
    with open("generate_input/jsons/rasps.json", "w") as f:
        obj = {"rasps": rasps}
        json.dump(obj, f)

    with open("generate_input/jsons/professors.json", "w") as f:
        obj = {"professors": professors}
        json.dump(obj, f)

    with open("generate_input/jsons/semesters.json", "w") as f:
        obj = {"semesters": list(semesters_dict.values())}
        json.dump(obj, f)

    with open("generate_input/jsons/subjects.json", "w") as f:
        obj = {"subjects": list(subjects_dict.values())}
        json.dump(obj, f)

    with open("generate_input/jsons/classrooms.json", "w") as f:
        obj = {"classrooms": list(rooms_dict.values())}
        json.dump(obj, f)

    with open("generate_input/jsons/classroom_available.json", "w") as f:
        obj = {"classroom_available": []}
        json.dump(obj, f)

    with open("generate_input/jsons/professor_available.json", "w") as f:
        obj = {"professor_available": []}
        json.dump(obj, f)

def get_constraint_range():
    constraint_range = []
    range_pool = list(range(1, NUM_HOURS))

    max_iters = random.choice([1,2,3])

    for _ in range(max_iters):
        first_number = random.choice(range_pool)
        second_range_pool = list(range(first_number+1, NUM_HOURS+1))
        if not second_range_pool:
            break

        second_number = random.choice(second_range_pool)
        constraint_range.append(str(first_number))
        constraint_range.append(str(second_number))

        first_number = second_number + 1
        range_pool = list(range(first_number+1, NUM_HOURS))
        if not range_pool:
            break

    return constraint_range


def tighten_room_free_time():
    with open("generate_input/jsons/classrooms.json", "r") as f:
        rooms = json.load(f)["classrooms"]

    with open("generate_input/jsons/classroom_available.json", "r") as f:
        room_available = json.load(f)["classroom_available"]
        room_available_ids = {room["room_id"] for room in room_available}

    NUM_ROOMS = len(rooms)
    constrain_distribution = [0.05, 0.1, 0.2, 0.3, 0.4]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_ROOMS = math.ceil(NUM_ROOMS * percent)
    CONSTRAIN_ROOMS = random.sample(rooms, NUM_CONSTRAIN_ROOMS)

    header = ["room_id", "monday", "tuesday", "wednesday", "thursday","friday"]
    rows = [header]
    for room in CONSTRAIN_ROOMS:
        if room["id"] in room_available_ids:
            continue

        row = []
        row.append(room["id"])
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            option = "T"
            roll = random.random()
            if roll > 0.5:
                option = "T"
            elif roll > 0.3 and roll <= 0.5:
                option = "F"
            elif roll >= 0 and roll <= 0.3:
                option = get_constraint_range()
            row.append(option)

        obj = {"room_id": row[0], "monday": row[1], "tuesday": row[2], "wednesday": row[3],
               "thursday": row[4], "friday": row[5]}
        room_available.append(obj)

        for i, value in enumerate(row):
            if i==0:
                continue
            if value != "T" and value != "F":
                row[i] = ",".join(value)
        rows.append(row)

    with open("generate_input/jsons/classroom_available.json", "w") as f:
        obj = {"classroom_available": room_available}
        json.dump(obj, f)


def tighten_prof_free_time():
    with open("generate_input/jsons/professors.json", "r") as f:
        profs = json.load(f)["professors"]

    with open("generate_input/jsons/professor_available.json", "r") as f:
        prof_available = json.load(f)["professor_available"]
        prof_available_ids = {prof["professor_id"] for prof in prof_available}

    NUM_PROFS = len(profs)
    constrain_distribution = [0.05, 0.1, 0.2, 0.3, 0.4]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_PROFS = math.ceil(NUM_PROFS * percent)
    CONSTRAIN_PROFS = random.sample(profs, NUM_CONSTRAIN_PROFS)

    header = ["professor_id", "monday", "tuesday", "wednesday", "thursday", "friday"]
    rows = [header]
    for prof in CONSTRAIN_PROFS:
        if prof["id"] in prof_available_ids:
            continue

        row = []
        row.append(prof["id"])
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            option = "T"
            roll = random.random()
            if roll > 0.5:
                option = "T"
            elif roll > 0.3 and roll <= 0.5:
                option = "F"
            elif roll >= 0 and roll <= 0.3:
                option = get_constraint_range()
            row.append(option)

        obj = {"professor_id": row[0], "monday": row[1], "tuesday": row[2], "wednesday": row[3],
               "thursday": row[4], "friday": row[5]}
        prof_available.append(obj)

        for i, value in enumerate(row):
            if i==0:
                continue
            if value != "T" and value != "F":
                row[i] = ",".join(value)
        rows.append(row)

    with open("generate_input/jsons/professor_available.json", "w") as f:
        obj = {"professor_available": prof_available}
        json.dump(obj, f)


def tighten_room_capacity():
    with open("generate_input/jsons/classrooms.json", "r") as f:
        rooms = json.load(f)["classrooms"]

    NUM_ROOMS = len(rooms)
    constrain_distribution = [0.01, 0.02, 0.03, 0.04, 0.05]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_ROOMS = math.ceil(NUM_ROOMS * percent)
    CONSTRAIN_ROOMS = random.sample(rooms, NUM_CONSTRAIN_ROOMS)
    CONSTRAIN_ROOMS_IDS = set(room["id"] for room in CONSTRAIN_ROOMS)

    for i,room in enumerate(rooms):
        if room["id"] not in CONSTRAIN_ROOMS_IDS:
            continue
        capacity_reduce_distr = [0.05, 0.08, 0.1, 0.12, 0.15]
        percent = random.choice(capacity_reduce_distr)
        reduce_by = math.ceil(int(room["capacity"]) * percent)
        new_capacity = int(room["capacity"]) - reduce_by
        room["capacity"] = str(new_capacity)
        rooms[i] = room

    with open("generate_input/jsons/classrooms.json", "w") as f:
        obj = {"classrooms": rooms}
        json.dump(obj, f)


def tighten_room_computers():
    with open("generate_input/jsons/classrooms.json", "r") as f:
        rooms = json.load(f)["classrooms"]
        computer_rooms = [room for room in rooms if room["has_computers"]=="1"]

    NUM_COMPUTER_ROOMS = len(computer_rooms)
    constrain_distribution = [0.01, 0.02, 0.03, 0.04, 0.05]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_ROOMS = math.ceil(NUM_COMPUTER_ROOMS * percent)
    CONSTRAIN_ROOMS = random.sample(computer_rooms, NUM_CONSTRAIN_ROOMS)
    CONSTRAIN_ROOMS_IDS = set(room["id"] for room in CONSTRAIN_ROOMS)

    for i,room in enumerate(rooms):
        if room["id"] not in CONSTRAIN_ROOMS_IDS:
            continue
        room["has_computers"] = "0"
        rooms[i] = room

    with open("generate_input/jsons/classrooms.json", "w") as f:
        obj = {"classrooms": rooms}
        json.dump(obj, f)


def tighten_num_rooms():
    with open("generate_input/jsons/classrooms.json", "r") as f:
        rooms = json.load(f)["classrooms"]

    NUM_ROOMS = len(rooms)
    constrain_distribution = [0.01, 0.02, 0.03, 0.04, 0.05]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_ROOMS = math.ceil(NUM_ROOMS * percent)
    CONSTRAIN_ROOMS = random.sample(rooms, NUM_CONSTRAIN_ROOMS)

    rooms = [room for room in rooms if room not in CONSTRAIN_ROOMS]

    with open("generate_input/jsons/classrooms.json", "w") as f:
        obj = {"classrooms": rooms}
        json.dump(obj, f)


def tighten_semesters_per_subject():
    with open("generate_input/jsons/semesters.json", "r") as f:
        semesters = json.load(f)

    with open("generate_input/jsons/subjects.json", "r") as f:
        subjects = json.load(f)


def tighten_students_per_semester():
    with open("generate_input/jsons/semesters.json", "r") as f:
        semesters = json.load(f)


def tighten_rasp_needs_computers():
    with open("generate_input/jsons/rasps.json", "r") as f:
        rasps = json.load(f)


def tighten_rasp_random_dtstart_weekday():
    with open("generate_input/jsons/rasps.json", "r") as f:
        rasps = json.load(f)


def tighten_constraints():
    tighten_options = ["room_free_time", "prof_free_time", "room_capacity", "room_pc",
                       "num_rooms", "num_semesters_per_subject", "num_students_per_semester",
                       "rasp_needs_computer", "rasp_random_dtstart_weekday"] #TODO: + fix_at_room_id

    tighten_what = random.choice(tighten_options)

    if tighten_what == "room_free_time":
        tighten_room_free_time()
    elif tighten_what == "prof_free_time":
        tighten_prof_free_time()
    elif tighten_what == "room_capacity":
        tighten_room_capacity()
    elif tighten_what == "room_pc":
        tighten_room_computers()
    elif tighten_what == "num_rooms":
        tighten_num_rooms()
    elif tighten_what == "num_semesters_per_subject":
        tighten_semesters_per_subject()
    elif tighten_what == "num_students_per_semester":
        tighten_students_per_semester()
    elif tighten_what == "rasp_needs_computer":
        tighten_rasp_needs_computers()
    elif tighten_what == "rasp_random_dtstart_weekday":
        tighten_rasp_random_dtstart_weekday()



#TODO: Add fixed hours to some of the rrules
def generate_input(NUM_RASPS: int):
    rasps, professors = generate_rasps(NUM_RASPS)
    semesters_dict = generate_semesters(NUM_RASPS)
    subjects_dict  = generate_subjects(rasps, semesters_dict)
    rooms_dict = generate_rooms(NUM_RASPS, semesters_dict)

    #create_csvs(rasps, professors, semesters_dict, subjects_dict, rooms_dict)
    #create_jsons(rasps, professors, semesters_dict, subjects_dict, rooms_dict)
    tighten_room_free_time()
    tighten_prof_free_time()
    tighten_room_capacity()
    tighten_room_computers()
    tighten_num_rooms()

generate_input(100)
