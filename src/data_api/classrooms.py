import json
import numpy as np
import pandas as pd
from itertools import product, starmap
from collections import defaultdict
from data_api.utilities.my_types import Classroom, Slot

def get_rooms():
    with open("database/input/classrooms.json", "r") as fp:
        rooms = json.load(fp)["classrooms"]

    typed_rooms = []
    for room in rooms:
        room["capacity"] = int(room["capacity"])
        room["has_computers"] = True if room["has_computers"]=="1" else False
        room["user_id"] = None
        room["used_in_faculty_ids"] = None
        room = Classroom(**{field: room[field] for field in Classroom._fields})
        typed_rooms.append(room)

    return typed_rooms


def get_rooms_constraints():
    with open("database/constraints/classroom_available.json", "r") as fp:
        rooms_available = json.load(fp)["classroom_available"]
    return rooms_available


def get_rooms_dict():
    rooms = get_rooms()
    rooms_dict = {}
    for room in rooms:
        rooms_dict[room.id] = room
    return rooms_dict


def update_rooms(rooms, rooms_occupied):
    return {room.id:room for room in rooms.values() if room.id in rooms_occupied}


def get_rooms_free_terms(NUM_WEEKS, NUM_HOURS, room_available, rooms):
    FREE_TERMS = set()
    done_rooms = {}

    for avail in room_available:
        room_id = avail["room_id"]
        done_rooms[room_id] = True

        monday_terms    = transform_room_time(avail["monday"])
        tuesday_terms   = transform_room_time(avail["tuesday"])
        wednesday_terms = transform_room_time(avail["wednesday"])
        thursday_terms  = transform_room_time(avail["thursday"])
        friday_terms    = transform_room_time(avail["friday"])

        if monday_terms:
            for term in monday_terms:
                FREE_TERMS |= set(starmap(Slot, product([room_id], range(NUM_WEEKS), [0], term)))
        if tuesday_terms:
            for term in tuesday_terms:
                FREE_TERMS |= set(starmap(Slot, product([room_id], range(NUM_WEEKS), [1], term)))
        if wednesday_terms:
            for term in wednesday_terms:
                FREE_TERMS |= set(starmap(Slot, product([room_id], range(NUM_WEEKS), [2], term)))
        if thursday_terms:
            for term in thursday_terms:
                FREE_TERMS |= set(starmap(Slot, product([room_id], range(NUM_WEEKS), [3], term)))
        if friday_terms:
            for term in friday_terms:
                FREE_TERMS |= set(starmap(Slot, product([room_id], range(NUM_WEEKS), [4], term)))

    for room_id in rooms:
        if room_id in done_rooms:
            continue
        FREE_TERMS |= set(starmap(Slot, product([room_id], range(NUM_WEEKS), range(0,5), range(0, NUM_HOURS))))

    return FREE_TERMS


def generate_starting_slots(rooms_occupied, NUM_HOURS):
    starting_slots = set()
    for room_id in rooms_occupied:
        for day in range(5):
            for hour in range(NUM_HOURS):
                if rooms_occupied[room_id][0][day][hour] == 0:
                    starting_slots.add(Slot(room_id, 0, day, hour))
    return starting_slots


def get_rooms_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rooms):
    rooms_constraints = get_rooms_constraints()
    free_slots        = get_rooms_free_terms(NUM_WEEKS, NUM_HOURS, rooms_constraints, rooms)
    #1 = [room][week,day,hour] IS OCCUPIED, 0 = [room][week,day,hour] IS FREE
    rooms_occupied = defaultdict(lambda: np.ones(shape=(NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8))
    for room_id, week, day, hour in free_slots:
        rooms_occupied[room_id][week,day,hour] = 0

    return dict(**rooms_occupied)


def get_rooms_occupied_old(FREE_TERMS, rasps, FIXED):
    #1 = [room][day,hour] IS OCCUPIED, 0 = [room][day,hour] IS FREE
    rooms_occupied = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.uint8))
    for room, day, hour in FREE_TERMS:
        rooms_occupied[room][day,hour] = 0

    for rasp in rasps:
        if not rasp.fixedAt:
            continue
        room_id, day, hour = rasp.fixedAt.split(",")
        day, hour = int(day)-1, int(hour)-1
        FIXED[rasp] = (room_id, day, hour)
        rooms_occupied[room_id][day, hour:(hour+rasp.duration)] += 1

    return rooms_occupied


def get_room_by_id(room_id):
    rooms = get_rooms()
    for room in rooms:
        if room_id == room.id:
            return room
    return -1


def get_rooms_by_ids(room_ids):
    rooms = get_rooms()
    return [room for room in rooms if room.id in room_ids]


def get_computer_rooms(rooms):
    return {room.id for room in rooms if room.has_computers}


def get_rooms_capacity(rooms):
    return {room.id:room.capacity for room in rooms}


def transform_room_time(ugly_time):
    if ugly_time == "F":
        return []
    elif ugly_time == "T":
        return [range(0,16)]
    else:
        ranges = []
        for i in range(0,len(ugly_time), 2):
            start, finish = int(ugly_time[i]), int(ugly_time[i+1])
            ranges.append(range(start-1, finish))
        return ranges


def get_classroom_ids_csv():
    path = "database/input/csvs/classrooms.csv"
    with open(path) as csv_file:
        classrooms = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3,4])

        classrooms = pd.DataFrame(classrooms).astype("str")

    return set(classrooms.id)
