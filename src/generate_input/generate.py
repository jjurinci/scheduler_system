import csv
import json
import random
import string
from itertools import product


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
    if roll > 0.6:
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


def find_freq(rrule: str):
    parts = rrule.split(";")
    for part in parts:
        idx = part.find("FREQ=")
        if idx != -1:
            return part[idx + len("FREQ=") :]
    raise AssertionError


def generate_input(N: int):
    professors, subjects, semesters = set(), set(), set()
    rasps = []

    rrules_pool = get_all_rrules()
    subject_ids   = get_subject_ids()
    professor_ids = get_professor_ids()
    num_rasps = 0
    while num_rasps < N:
        subject_id   = next(subject_ids)
        types = get_types()
        for type_ in types:
            groups = get_groups()
            for group in groups:
                rasp_id      = subject_id + "_" + type_ + group
                professor_id = next(professor_ids) + "_prof"
                duration     = get_duration()
                needs_pc     = get_needs_computer()
                fix_room_id  = None
                rrule        = get_one_rrule(rrules_pool)
                rnd_dt_wday  = get_random_dtstart_weekday(rrule)
                #print(f"{rasp_id=} {duration=} {needs_pc=} {rnd_dt_wday=} {rrule=}")
                #print("")

                professors.add(professor_id)
                num_rasps += 1
                rasp = {"id": rasp_id, "professor_id": professor_id,
                        "subject_id":subject_id, "type":type_, "group":group,
                        "duration":duration, "needs_computers":needs_pc,
                        "fix_at_room_id": fix_room_id, "random_dtstart_weekday":rnd_dt_wday,
                        "rrule":rrule}
                rasps.append(rasp)
                print(rasp)

        subjects.add(subject_id)

    room_ids      = get_room_ids()

generate_input(100)
