import csv
import json
import os
import random
import math
import string
from itertools import product

with open("generate_input/generate_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
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
    with open("generate_input/rrule_data.json", "r", encoding="utf-8") as j:
        rrules_pool = json.load(j)
    return rrules_pool


def get_one_rrule(rrules_pool):
    options = ["NORMAL_WEEKLY", "SPECIAL_WEEKLY", "DAILY", "MONTHLY"]
    weight_WEEKLY   = config["initial_input"]["rasps"]["NORMAL_WEEKLY_rrule"]
    weight_S_WEEKLY = config["initial_input"]["rasps"]["SPECIAL_WEEKLY_rrule"]
    weight_DAILY    = config["initial_input"]["rasps"]["DAILY_rrule"]
    weight_MONTHLY  = config["initial_input"]["rasps"]["MONTHLY_rrule"]
    weights = [weight_WEEKLY, weight_S_WEEKLY, weight_DAILY, weight_MONTHLY]

    rrule_type  = random.choices(options, weights, k=1)[0]

    if rrule_type == "NORMAL_WEEKLY":
        return rrules_pool["weekly"][0]
    elif rrule_type == "SPECIAL_WEEKLY":
        return random.choice(rrules_pool["weekly_other"])
    elif rrule_type == "DAILY":
        return random.choice(rrules_pool["daily"])
    elif rrule_type == "MONTHLY":
        return random.choice(rrules_pool["monthly"])



def get_types():
    options = [["P","V"], ["P", "V", "S"]]
    weight_PV  = config["initial_input"]["rasps"]["type_PV"]
    weight_PVS = config["initial_input"]["rasps"]["type_PVS"]
    weights = [weight_PV, weight_PVS]
    the_type = random.choices(options, weights, k=1)[0]
    return the_type


def get_groups():
    options = [["1"], ["1", "2"], ["1", "2", "3"], ["1", "2", "3", "4"]]
    weight_G1 = config["initial_input"]["rasps"]["group_1"]
    weight_G2 = config["initial_input"]["rasps"]["group_2"]
    weight_G3 = config["initial_input"]["rasps"]["group_3"]
    weight_G4 = config["initial_input"]["rasps"]["group_4"]
    weights = [weight_G1, weight_G2, weight_G3, weight_G4]
    group = random.choices(options, weights, k=1)[0]
    return group


def get_duration():
    options = ["1", "2", "3", "4"]
    weight_D1 = config["initial_input"]["rasps"]["duration_1"]
    weight_D2 = config["initial_input"]["rasps"]["duration_2"]
    weight_D3 = config["initial_input"]["rasps"]["duration_3"]
    weight_D4 = config["initial_input"]["rasps"]["duration_4"]
    weights = [weight_D1, weight_D2, weight_D3, weight_D4]
    duration = random.choices(options, weights, k=1)[0]
    return duration


def get_needs_computer():
    options = ["0", "1"]
    weight_0 = config["initial_input"]["rasps"]["not_needs_computers"]
    weight_1 = config["initial_input"]["rasps"]["needs_computers"]
    weights = [weight_0, weight_1]
    needs_computers = random.choices(options, weights, k=1)[0]
    return needs_computers


def get_random_dtstart_weekday(rrule):
    freq = find_freq(rrule)
    if freq == "DAILY":
        return "0"
    else:
        options = ["0", "1"]
        weight_0 = config["initial_input"]["rasps"]["not_random_dtstart"]
        weight_1 = config["initial_input"]["rasps"]["random_dtstart"]
        weights = [weight_0, weight_1]
        random_dtstart = random.choices(options, weights, k=1)[0]
        return random_dtstart


def get_num_students():
    options = ["high_number", "low_number"]
    weight_H  = config["initial_input"]["semesters"]["num_students_high_probability"]
    weight_L  = config["initial_input"]["semesters"]["num_students_low_probability"]
    weights = [weight_H, weight_L]
    number_type = random.choices(options, weights, k=1)[0]

    if number_type == "high_number":
        high_interval = config["initial_input"]["semesters"]["num_students_high_interval"]
        left, right = high_interval
        return random.randint(left, right)
    elif number_type == "low_number":
        low_interval  = config["initial_input"]["semesters"]["num_students_low_interval"]
        left, right = low_interval
        return random.randint(left, right)


def get_subject_mandatory():
    options = ["mandatory", "optional"]
    weight_M = config["initial_input"]["subjects"]["mandatory"]
    weight_O = config["initial_input"]["subjects"]["optional"]
    weights = [weight_M, weight_O]
    option = random.choices(options, weights, k=1)[0]
    return True if option == "mandatory" else False


def find_freq(rrule: str):
    parts = rrule.split(";")
    for part in parts:
        idx = part.find("FREQ=")
        if idx != -1:
            return part[idx + len("FREQ=") :]
    raise AssertionError


def generate_start_end():
    obj = {"start_semester_date": "4.10.2021", "end_semester_date": "28.1.2022"}
    return obj

def generate_day_structure():
    obj = [
        { "#": "1", "timeblock": "08:00-08:45" },
        { "#": "2", "timeblock": "08:50-09:35" },
        { "#": "3", "timeblock": "09:40-10:25" },
        { "#": "4", "timeblock": "10:30-11:15" },
        { "#": "5", "timeblock": "11:20-12:05" },
        { "#": "6", "timeblock": "12:10-12:55" },
        { "#": "7", "timeblock": "13:00-13:45" },
        { "#": "8", "timeblock": "14:00-14:40" },
        { "#": "9", "timeblock": "14:45-15:25" },
        { "#": "10", "timeblock": "15:30-16:10" },
        { "#": "11", "timeblock": "16:15-16:55" },
        { "#": "12", "timeblock": "17:00-17:40" },
        { "#": "13", "timeblock": "17:45-18:25" },
        { "#": "14", "timeblock": "18:30-19:10" },
        { "#": "15", "timeblock": "19:15-20:00" },
        { "#": "16", "timeblock": "20:05-20:50" }
    ]
    return obj

def generate_professors(NUM_RASPS):
    possible_professors_ratio = config["initial_input"]["rasps"]["possible_prof_to_rasp_ratios"]
    NUM_PROFESSORS = math.ceil(random.choice(possible_professors_ratio) * NUM_RASPS)
    professors = []
    professor_ids = get_professor_ids()
    for _ in range(NUM_PROFESSORS):
        prof_id = next(professor_ids)
        professor = {"id": prof_id + "_prof", "name": prof_id + "_name"}
        professors.append(professor)
    return professors


def generate_rasps(NUM_RASPS):
    rasps = []
    rrules_pool = get_all_rrules()
    subject_ids = get_subject_ids()
    professors = generate_professors(NUM_RASPS)
    cnt_rasps = 0
    while cnt_rasps < NUM_RASPS:
        subject_id = next(subject_ids)
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
    possible_semesters_ratio = config["initial_input"]["semesters"]["possible_sem_to_rasp_ratios"]
    NUM_SEMESTERS = math.ceil(random.choice(possible_semesters_ratio) * NUM_RASPS)
    semesters, semesters_dict = [], {}
    semester_ids = get_semester_ids()
    for _ in range(NUM_SEMESTERS):
        sem_id = next(semester_ids)
        num_students = get_num_students()
        semester = {"id": sem_id + "_sem", "num_semester": "1", "season": "W",
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
    semesters_id_list = list(semesters_dict.keys())
    semester_idx = 0
    for subject_id in subjects_dict:
        mandatory = get_subject_mandatory()
        semester_id = semesters_id_list[semester_idx]
        if mandatory:
            subjects_dict[subject_id]["mandatory_in_semester_ids"].append(semester_id)
        else:
            subjects_dict[subject_id]["optional_in_semester_ids"].append(semester_id)
        semester_idx = (semester_idx + 1) % NUM_SEMESTERS

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

    possible_room_ratios = config["initial_input"]["rooms"]["possible_room_to_rasp_ratios"]
    NUM_ROOMS = math.ceil(random.choice(possible_room_ratios) * NUM_RASPS)
    possible_has_computers_ratios = config["initial_input"]["rooms"]["possible_computer_room_percentages"]
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


def create_csvs(rasps, professors, semesters_dict, subjects_dict, rooms_dict, start_end_dict, day_struct_dict):
    dir_path = "generate_input/csvs"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open("generate_input/csvs/rasps.csv", "w", encoding="utf-8") as f:
        header_rasp = ["id", "professor_id", "subject_id", "type", "group", "duration", "needs_computers", "fix_at_room_id", "random_dtstart_weekday", "rrule"]
        writer = csv.writer(f)
        writer.writerow(header_rasp)
        for rasp in rasps:
            rrule = '\"' + rasp["rrule"] + '\"'
            row = [rasp["id"], rasp["professor_id"], rasp["subject_id"], rasp["type"], rasp["group"], rasp["duration"], rasp["needs_computers"], rasp["fix_at_room_id"], rasp["random_dtstart_weekday"], rrule]
            writer.writerow(row)

    with open("generate_input/csvs/professors.csv", "w", encoding="utf-8") as f:
        header_prof = ["id", "name"]
        writer = csv.writer(f)
        writer.writerow(header_prof)
        for prof in professors:
            row = [prof["id"], prof["name"]]
            writer.writerow(row)

    with open("generate_input/csvs/semesters.csv", "w", encoding="utf-8") as f:
        header_semester = ["id", "num_semester", "season", "num_students", "study_programme_id"]
        writer = csv.writer(f)
        writer.writerow(header_semester)
        for sem in semesters_dict.values():
            row = [sem["id"], sem["num_semester"], sem["season"], sem["num_students"], sem["study_programme_id"]]
            writer.writerow(row)

    with open("generate_input/csvs/subjects.csv", "w", encoding="utf-8") as f:
        header_subject = ["id", "name", "mandatory_in_semester_ids", "optional_in_semester_ids"]
        writer = csv.writer(f)
        writer.writerow(header_subject)
        for sub in subjects_dict.values():
            mandatory_in_semester_ids = ",".join(sub["mandatory_in_semester_ids"])
            optional_in_semester_ids  = ",".join(sub["optional_in_semester_ids"])
            mandatory_in_semester_ids = "" if sub["mandatory_in_semester_ids"] == [] else mandatory_in_semester_ids
            optional_in_semester_ids  = "" if sub["optional_in_semester_ids"]  == [] else optional_in_semester_ids
            row = [sub["id"], sub["name"], mandatory_in_semester_ids, optional_in_semester_ids]
            writer.writerow(row)

    with open("generate_input/csvs/classrooms.csv", "w", encoding="utf-8") as f:
        header_classroom = ["id", "name", "capacity", "has_computers"]
        writer = csv.writer(f)
        writer.writerow(header_classroom)
        for room in rooms_dict.values():
            row = [room["id"], room["name"], room["capacity"], room["has_computers"]]
            writer.writerow(row)

    with open("generate_input/csvs/classroom_available.csv", "w", encoding="utf-8") as f:
        header_classroom_available = ["room_id", "monday", "tuesday", "wednesday", "thursday", "friday"]
        writer = csv.writer(f)
        writer.writerow(header_classroom_available)

    with open("generate_input/csvs/professor_available.csv", "w", encoding="utf-8") as f:
        header_professor_available = ["professor_id", "monday", "tuesday", "wednesday", "thursday", "friday"]
        writer = csv.writer(f)
        writer.writerow(header_professor_available)

    with open("generate_input/csvs/start_end_year.csv", "w", encoding="utf-8") as f:
        header_start_end = ["start_semester_date", "end_semester_date"]
        writer = csv.writer(f)
        writer.writerow(header_start_end)
        row = [start_end_dict["start_semester_date"], start_end_dict["end_semester_date"]]
        writer.writerow(row)

    with open("generate_input/csvs/day_structure.csv", "w", encoding="utf-8") as f:
        header_daystruct = ["#", "timeblock"]
        writer = csv.writer(f)
        writer.writerow(header_daystruct)
        for dayobj in day_struct_dict:
            row = [dayobj["#"], dayobj["timeblock"]]
            writer.writerow(row)


def create_jsons(rasps, professors, semesters_dict, subjects_dict, rooms_dict, start_end_dict, day_struct_dict):
    dir_path = "generate_input/jsons"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open("generate_input/jsons/rasps.json", "w", encoding="utf-8") as f:
        obj = {"rasps": rasps}
        json.dump(obj, f)

    with open("generate_input/jsons/professors.json", "w", encoding="utf-8") as f:
        obj = {"professors": professors}
        json.dump(obj, f)

    with open("generate_input/jsons/semesters.json", "w", encoding="utf-8") as f:
        obj = {"semesters": list(semesters_dict.values())}
        json.dump(obj, f)

    with open("generate_input/jsons/subjects.json", "w", encoding="utf-8") as f:
        obj = {"subjects": list(subjects_dict.values())}
        json.dump(obj, f)

    with open("generate_input/jsons/classrooms.json", "w", encoding="utf-8") as f:
        obj = {"classrooms": list(rooms_dict.values())}
        json.dump(obj, f)

    with open("generate_input/jsons/classroom_available.json", "w", encoding="utf-8") as f:
        obj = {"classroom_available": []}
        json.dump(obj, f)

    with open("generate_input/jsons/professor_available.json", "w", encoding="utf-8") as f:
        obj = {"professor_available": []}
        json.dump(obj, f)

    with open("generate_input/jsons/start_end_year.json", "w", encoding="utf-8") as f:
        obj = {"start_end_year": [start_end_dict]}
        json.dump(obj, f)

    with open("generate_input/jsons/day_structure.json", "w", encoding="utf-8") as f:
        obj = {"day_structure": day_struct_dict}
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
    with open("generate_input/jsons/classrooms.json", "r", encoding="utf-8") as f:
        rooms = json.load(f)["classrooms"]

    with open("generate_input/jsons/classroom_available.json", "r", encoding="utf-8") as f:
        room_available = json.load(f)["classroom_available"]
        room_available_ids = {room["room_id"] for room in room_available}

    NUM_ROOMS = len(rooms)
    constrain_distribution = config["later_constraints"]["room_free_time"]["possible_num_rooms"]
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
            options = ["T", "F", "range"]
            weight_T = config["later_constraints"]["room_free_time"]["room_T"]
            weight_F = config["later_constraints"]["room_free_time"]["room_F"]
            weight_R = config["later_constraints"]["room_free_time"]["room_range"]
            weights  = [weight_T, weight_F, weight_R]
            option = random.choices(options, weights, k=1)[0]
            if option == "range":
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

    with open("generate_input/jsons/classroom_available.json", "w", encoding="utf-8") as f:
        obj = {"classroom_available": room_available}
        json.dump(obj, f)


def tighten_prof_free_time():
    with open("generate_input/jsons/professors.json", "r", encoding="utf-8") as f:
        profs = json.load(f)["professors"]

    with open("generate_input/jsons/professor_available.json", "r", encoding="utf-8") as f:
        prof_available = json.load(f)["professor_available"]
        prof_available_ids = {prof["professor_id"] for prof in prof_available}

    NUM_PROFS = len(profs)
    constrain_distribution = config["later_constraints"]["prof_free_time"]["possible_num_profs"]
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
            options = ["T", "F", "range"]
            weight_T = config["later_constraints"]["prof_free_time"]["prof_T"]
            weight_F = config["later_constraints"]["prof_free_time"]["prof_F"]
            weight_R = config["later_constraints"]["prof_free_time"]["prof_range"]
            weights  = [weight_T, weight_F, weight_R]
            option = random.choices(options, weights, k=1)[0]
            if option == "range":
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

    with open("generate_input/jsons/professor_available.json", "w", encoding="utf-8") as f:
        obj = {"professor_available": prof_available}
        json.dump(obj, f)


def tighten_room_capacity():
    with open("generate_input/jsons/classrooms.json", "r", encoding="utf-8") as f:
        rooms = json.load(f)["classrooms"]

    NUM_ROOMS = len(rooms)
    constrain_distribution = config["later_constraints"]["room_capacity"]["possible_num_rooms"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_ROOMS = math.ceil(NUM_ROOMS * percent)
    CONSTRAIN_ROOMS = random.sample(rooms, NUM_CONSTRAIN_ROOMS)
    CONSTRAIN_ROOMS_IDS = set(room["id"] for room in CONSTRAIN_ROOMS)

    for i,room in enumerate(rooms):
        if room["id"] not in CONSTRAIN_ROOMS_IDS:
            continue
        capacity_reduce_distr = config["later_constraints"]["room_capacity"]["possible_capacity_reduce_by"]
        percent = random.choice(capacity_reduce_distr)
        reduce_by = math.ceil(int(room["capacity"]) * percent)
        new_capacity = int(room["capacity"]) - reduce_by
        room["capacity"] = str(new_capacity)
        rooms[i] = room

    with open("generate_input/jsons/classrooms.json", "w", encoding="utf-8") as f:
        obj = {"classrooms": rooms}
        json.dump(obj, f)


def tighten_room_computers():
    with open("generate_input/jsons/classrooms.json", "r", encoding="utf-8") as f:
        rooms = json.load(f)["classrooms"]
        computer_rooms = [room for room in rooms if room["has_computers"]=="1"]

    NUM_COMPUTER_ROOMS = len(computer_rooms)
    constrain_distribution = config["later_constraints"]["room_computers"]["possible_num_rooms"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_ROOMS = math.ceil(NUM_COMPUTER_ROOMS * percent)
    CONSTRAIN_ROOMS = random.sample(computer_rooms, NUM_CONSTRAIN_ROOMS)
    CONSTRAIN_ROOMS_IDS = set(room["id"] for room in CONSTRAIN_ROOMS)

    for i,room in enumerate(rooms):
        if room["id"] not in CONSTRAIN_ROOMS_IDS:
            continue
        room["has_computers"] = "0"
        rooms[i] = room

    with open("generate_input/jsons/classrooms.json", "w", encoding="utf-8") as f:
        obj = {"classrooms": rooms}
        json.dump(obj, f)


def tighten_num_rooms():
    with open("generate_input/jsons/classrooms.json", "r", encoding="utf-8") as f:
        rooms = json.load(f)["classrooms"]
        if len(rooms) == 1:
            return

    with open("generate_input/jsons/classroom_available.json", "r", encoding="utf-8") as f:
        room_available = json.load(f)["classroom_available"]

    with open("generate_input/jsons/rasps.json", "r", encoding="utf-8") as f:
        rasps = json.load(f)["rasps"]

    NUM_ROOMS = len(rooms)
    constrain_distribution = config["later_constraints"]["remove_rooms"]["possible_num_rooms"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_ROOMS = math.ceil(NUM_ROOMS * percent)
    CONSTRAIN_ROOMS = random.sample(rooms, NUM_CONSTRAIN_ROOMS)
    CONSTRAIN_ROOMS_IDS = set(room["id"] for room in CONSTRAIN_ROOMS)

    rooms = [room for room in rooms if room not in CONSTRAIN_ROOMS]
    room_available = [room for room in room_available if room["room_id"] not in CONSTRAIN_ROOMS_IDS]

    for rasp in rasps:
        if rasp["fix_at_room_id"] in CONSTRAIN_ROOMS_IDS:
            rasp["fix_at_room_id"] = None

    with open("generate_input/jsons/classrooms.json", "w", encoding="utf-8") as f:
        obj = {"classrooms": rooms}
        json.dump(obj, f)

    with open("generate_input/jsons/classroom_available.json", "w", encoding="utf-8") as f:
        obj = {"classroom_available": room_available}
        json.dump(obj, f)

    with open("generate_input/jsons/rasps.json", "w", encoding="utf-8") as f:
        obj = {"rasps": rasps}
        json.dump(obj, f)


def tighten_semesters_per_subject():
    with open("generate_input/jsons/subjects.json", "r", encoding="utf-8") as f:
        subjects = json.load(f)["subjects"]

    with open("generate_input/jsons/semesters.json", "r", encoding="utf-8") as f:
        semesters = json.load(f)["semesters"]

    NUM_SUBJECTS = len(subjects)
    constrain_distribution = config["later_constraints"]["semesters_per_subject"]["possible_num_subjects"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_SUBS = math.ceil(NUM_SUBJECTS * percent)
    CONSTRAIN_SUBS = random.sample(subjects, NUM_CONSTRAIN_SUBS)
    CONSTRAIN_SUBS_IDS = set(subject["id"] for subject in CONSTRAIN_SUBS)

    for i,subject in enumerate(subjects):
        if subject["id"] not in CONSTRAIN_SUBS_IDS:
            continue
        options = config["later_constraints"]["semesters_per_subject"]["possible_num_semester_increase"]
        how_many_semesters = random.choice(options)
        for _ in range(how_many_semesters):
            semester = random.choice(semesters)
            if semester["id"] not in subject["mandatory_in_semester_ids"] and \
               semester["id"] not in subject["optional_in_semester_ids"]:
                   options = ["mandatory", "optional"]
                   weight_M = config["later_constraints"]["semesters_per_subject"]["subject_mandatory_in_semester"]
                   weight_O = config["later_constraints"]["semesters_per_subject"]["subject_optional_in_semester"]
                   weights = [weight_M, weight_O]
                   option = random.choices(options, weights, k=1)[0]
                   mandatory = True if option == "mandatory" else False
                   if mandatory:
                       subject["mandatory_in_semester_ids"].append(semester["id"])
                   else:
                       subject["optional_in_semester_ids"].append(semester["id"])
        subjects[i] = subject

    with open("generate_input/jsons/subjects.json", "w", encoding="utf-8") as f:
        obj = {"subjects": subjects}
        json.dump(obj, f)


def tighten_students_per_semester():
    with open("generate_input/jsons/semesters.json", "r", encoding="utf-8") as f:
        semesters = json.load(f)["semesters"]

    NUM_SEMESTERS = len(semesters)
    constrain_distribution = config["later_constraints"]["num_students_per_semester"]["possible_num_semester"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_SEMS = math.ceil(NUM_SEMESTERS * percent)
    CONSTRAIN_SEMESTERS = random.sample(semesters, NUM_CONSTRAIN_SEMS)
    CONSTRAIN_SEM_IDS = set(sem["id"] for sem in CONSTRAIN_SEMESTERS)

    for i,semester in enumerate(semesters):
        if semester["id"] not in CONSTRAIN_SEM_IDS:
            continue
        numstudents_reduce_distr = config["later_constraints"]["num_students_per_semester"]["possible_num_students_reduce_by"]
        percent = random.choice(numstudents_reduce_distr)
        reduce_by = math.ceil(int(semester["num_students"]) * percent)
        new_num_students = int(semester["num_students"]) + reduce_by
        semester["num_students"] = str(new_num_students)
        semesters[i] = semester

    with open("generate_input/jsons/semesters.json", "w", encoding="utf-8") as f:
        obj = {"semesters": semesters}
        json.dump(obj, f)


def tighten_rasp_needs_computers():
    with open("generate_input/jsons/rasps.json", "r", encoding="utf-8") as f:
        rasps = json.load(f)["rasps"]
        computer_rasps = [rasp for rasp in rasps if rasp["needs_computers"] == "0"]

    NUM_COMPUTER_RASPS = len(computer_rasps)
    constrain_distribution = config["later_constraints"]["rasp_needs_computer"]["possible_num_rasps"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_RASPS = math.ceil(NUM_COMPUTER_RASPS * percent)
    CONSTRAIN_RASPS = random.sample(computer_rasps, NUM_CONSTRAIN_RASPS)
    CONSTRAIN_RASPS_IDS = set(rasp["id"] for rasp in CONSTRAIN_RASPS)

    for i,rasp in enumerate(rasps):
        if rasp["id"] not in CONSTRAIN_RASPS_IDS:
            continue
        rasp["needs_computers"] = "1"
        rasps[i] = rasp

    with open("generate_input/jsons/rasps.json", "w", encoding="utf-8") as f:
        obj = {"rasps": rasps}
        json.dump(obj, f)


def tighten_rasp_random_dtstart_weekday():
    with open("generate_input/jsons/rasps.json", "r", encoding="utf-8") as f:
        rasps = json.load(f)["rasps"]
        no_rnd_dt_rasps = [rasp for rasp in rasps if rasp["random_dtstart_weekday"] == "1"]

    NUM_NODT_RASPS = len(no_rnd_dt_rasps)
    constrain_distribution = config["later_constraints"]["rasp_random_dtstart_weekday"]["possible_num_rasps"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_RASPS = math.ceil(NUM_NODT_RASPS * percent)
    CONSTRAIN_RASPS = random.sample(no_rnd_dt_rasps, NUM_CONSTRAIN_RASPS)
    CONSTRAIN_RASPS_IDS = set(rasp["id"] for rasp in CONSTRAIN_RASPS)

    for i,rasp in enumerate(rasps):
        if rasp["id"] not in CONSTRAIN_RASPS_IDS:
            continue
        rasp["random_dtstart_weekday"] = "0"
        rasps[i] = rasp

    with open("generate_input/jsons/rasps.json", "w", encoding="utf-8") as f:
        obj = {"rasps": rasps}
        json.dump(obj, f)


def tighten_rasp_fix_at_room_id():
    with open("generate_input/jsons/rasps.json", "r", encoding="utf-8") as f:
        rasps = json.load(f)["rasps"]

    with open("generate_input/jsons/classrooms.json", "r", encoding="utf-8") as f:
        classrooms = json.load(f)["classrooms"]

    NUM_RASPS = len(rasps)
    constrain_distribution = config["later_constraints"]["rasp_fix_at_room_id"]["possible_num_rasps"]
    percent = random.choice(constrain_distribution)
    NUM_CONSTRAIN_RASPS = math.ceil(NUM_RASPS * percent)
    CONSTRAIN_RASPS = random.sample(rasps, NUM_CONSTRAIN_RASPS)
    CONSTRAIN_RASPS_IDS = set(rasp["id"] for rasp in CONSTRAIN_RASPS)

    target_len_pool = config["later_constraints"]["rasp_fix_at_room_id"]["num_room_pool"]
    len_pool = target_len_pool if target_len_pool <= len(classrooms) else len(classrooms)
    room_pool = random.sample(classrooms, len_pool)
    room_pool = sorted(room_pool, key=lambda x: (int(x["capacity"]), int(x["has_computers"])), reverse=True)

    for rasp in rasps:
        if rasp["id"] not in CONSTRAIN_RASPS_IDS:
            continue
        rnd_room_id = random.choice(room_pool)["id"]
        rasp["fix_at_room_id"] = rnd_room_id

    with open("generate_input/jsons/rasps.json", "w", encoding="utf-8") as f:
        obj = {"rasps": rasps}
        json.dump(obj, f)


def tighten_a_constraint():
    tighten_options = ["room_free_time", "prof_free_time", "room_capacity", "room_pc",
                       "num_rooms", "num_semesters_per_subject", "num_students_per_semester",
                       "rasp_needs_computer", "rasp_random_dtstart_weekday", "rasp_fix_at_room_id"]

    weight_room_free_time = config["later_constraints"]["constrain_what"]["room_free_time"]
    weight_prof_free_time = config["later_constraints"]["constrain_what"]["prof_free_time"]
    weight_capacity       = config["later_constraints"]["constrain_what"]["room_capacity"]
    weight_pc             = config["later_constraints"]["constrain_what"]["room_pc"]
    weight_num_rooms      = config["later_constraints"]["constrain_what"]["num_rooms"]
    weight_sem_per_sub    = config["later_constraints"]["constrain_what"]["num_semesters_per_subject"]
    weight_stu_per_sem    = config["later_constraints"]["constrain_what"]["num_students_per_semester"]
    weight_rasp_pc        = config["later_constraints"]["constrain_what"]["rasp_needs_computer"]
    weight_rasp_dtwday    = config["later_constraints"]["constrain_what"]["rasp_random_dtstart_weekday"]
    weight_rasp_fix_room  = config["later_constraints"]["constrain_what"]["rasp_fix_at_room_id"]

    weights = [weight_room_free_time, weight_prof_free_time, weight_capacity,
               weight_pc, weight_num_rooms, weight_sem_per_sub, weight_stu_per_sem,
               weight_rasp_pc, weight_rasp_dtwday, weight_rasp_fix_room]

    tighten_what = random.choices(tighten_options, weights, k=1)[0]

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
    elif tighten_what == "rasp_fix_at_room_id":
        tighten_rasp_fix_at_room_id()


def generate_input():
    NUM_RASPS = config["NUM_RASPS"]
    rasps, professors = generate_rasps(NUM_RASPS)
    semesters_dict = generate_semesters(NUM_RASPS)
    subjects_dict  = generate_subjects(rasps, semesters_dict)
    rooms_dict = generate_rooms(NUM_RASPS, semesters_dict)
    start_end_dict = generate_start_end()
    day_struct_dict = generate_day_structure()

    create_csvs(rasps, professors, semesters_dict, subjects_dict, rooms_dict, start_end_dict, day_struct_dict)
    create_jsons(rasps, professors, semesters_dict, subjects_dict, rooms_dict, start_end_dict, day_struct_dict)

    iters = random.randint(0,4)
    for _ in range(iters):
        tighten_a_constraint()

generate_input()
