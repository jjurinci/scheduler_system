import json
import numpy as np
from itertools import product
from collections import defaultdict
from data_api.utilities.my_types import Classroom

def get_rooms():
    with open("database/input/classrooms.json", "r") as fp:
        rooms = json.load(fp)["classrooms"]

    typed_rooms = []
    for room in rooms:
        room["capacity"] = int(room["capacity"])
        room["hasComputers"] = True if room["hasComputers"]=="1" else False
        room = Classroom(**{field: room[field] for field in Classroom._fields})
        typed_rooms.append(room)

    return typed_rooms


def get_rooms_available():
    with open("database/constraints/classroom_available.json", "r") as fp:
        rooms_available = json.load(fp)["classroomAvailable"]
    return rooms_available


def get_rooms_free_terms(room_available, rooms):
    FREE_TERMS = set()
    done_rooms = {}

    for avail in room_available:
        room_id = avail["classroomId"]
        done_rooms[room_id] = True

        monday_terms    = transform_room_time(avail["monday"])
        tuesday_terms   = transform_room_time(avail["tuesday"])
        wednesday_terms = transform_room_time(avail["wednesday"])
        thursday_terms  = transform_room_time(avail["thursday"])
        friday_terms    = transform_room_time(avail["friday"])

        if monday_terms:
            for term in monday_terms:
                FREE_TERMS |= set(product([room_id], [0], term))
        if tuesday_terms:
            for term in tuesday_terms:
                FREE_TERMS |= set(product([room_id], [1], term))
        if wednesday_terms:
            for term in wednesday_terms:
                FREE_TERMS |= set(product([room_id], [2], term))
        if thursday_terms:
            for term in thursday_terms:
                FREE_TERMS |= set(product([room_id], [3], term))
        if friday_terms:
            for term in friday_terms:
                FREE_TERMS |= set(product([room_id], [4], term))

    for room in rooms:
        if room.id in done_rooms:
            continue
        FREE_TERMS |= set(product([room.id], range(0,5), range(0,16)))

    return FREE_TERMS


def get_rooms_occupied(FREE_TERMS, rasps, FIXED):
    #1 = [room][day,hour] IS OCCUPIED, 0 = [room][day,hour] IS FREE
    rooms_occupied = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.int32))
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
    return {room.id for room in rooms if room.hasComputers}


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
