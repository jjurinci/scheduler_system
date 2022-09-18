import json
import numpy as np
import pandas as pd
from itertools import product, starmap
from collections import defaultdict
from utilities.my_types import Classroom, Slot
from utilities.general_utilities import load_settings

"""
1) Gets rooms from a .json file
2) Fits them into Classroom type
3) Returns the list of classrooms
"""
def get_rooms():
    settings = load_settings()
    rooms_path = settings["path_classrooms_json"]

    with open(rooms_path, "r") as fp:
        rooms = json.load(fp)["classrooms"]

    typed_rooms = []
    for room in rooms:
        room["capacity"] = int(room["capacity"])
        room["has_computers"] = True if room["has_computers"]=="1" else False
        room = Classroom(**{field: room[field] for field in Classroom._fields})
        typed_rooms.append(room)

    return typed_rooms


"""
1) Gets rooms from a .csv file
2) Fits them into a pandas Dataframe and converts every cell to string
3) Returns the pandas Dataframe
"""
def get_classroom_ids_csv():
    settings = load_settings()
    rooms_path = settings["path_classrooms_csv"]
    with open(rooms_path) as csv_file:
        classrooms = pd.read_csv(csv_file,
                                 delimiter=",",
                                 usecols=[0,1,2,3])

        classrooms = pd.DataFrame(classrooms).astype("str")

    return set(classrooms.id)


"""
Returns initial room constraints from a .json file.
"""
def get_rooms_constraints():
    settings = load_settings()
    rooms_available_path = settings["path_classroom_available_json"]
    with open(rooms_available_path, "r") as fp:
        rooms_available = json.load(fp)["classroom_available"]
    return rooms_available


"""
Returns a dictionary of all rooms in "[room_id] = Classroom" form.
"""
def get_rooms_dict():
    rooms = get_rooms()
    return {room.id: room for room in rooms}


"""
Returns an updated version of a room dictionary where only rooms with some free space are kept.
"""
def update_rooms(rooms, rooms_occupied):
    return {room.id:room for room in rooms.values() if room.id in rooms_occupied}


"""
Utility function that transforms constraint times (e.g. gotten from .json)
to list of ranges. Each range denotes a block of time.
"""
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


"""
Returns a set of objects of type Slot(room_id, week, day, hour).
The set represents free terms in accordance to initial room constraints.
"""
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


"""
Returns dictionary:
    rooms_occupied[room_id] = np.ones[NUM_WEEKS][NUM_DAYS][NUM_HOURS]
after it is filled with zeros according to the free_slots set.
"""
def get_rooms_occupied(NUM_WEEKS, NUM_DAYS, NUM_HOURS, rooms):
    rooms_constraints = get_rooms_constraints()
    free_slots        = get_rooms_free_terms(NUM_WEEKS, NUM_HOURS, rooms_constraints, rooms)
    #1 = [room][week,day,hour] IS OCCUPIED, 0 = [room][week,day,hour] IS FREE
    rooms_occupied = defaultdict(lambda: np.ones(shape=(NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8))
    for room_id, week, day, hour in free_slots:
        rooms_occupied[room_id][week,day,hour] = 0

    return dict(**rooms_occupied)
