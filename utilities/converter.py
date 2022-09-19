import json
import pickle
import numpy as np
from utilities.my_types import Semester, Timeblock, TimeStructure, Rasp, Classroom, InitialConstraints, MutableConstraints, Slot, State
from datetime import datetime

def json_to_pickle(json_path, pickle_path):
    with open(json_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    is_winter = state["is_winter"]

    # {sem_id : Semester}
    semesters = {}
    for sem_id, sem in state["semesters"].items():
       semester = Semester(sem_id, sem["season"], sem["num_semester"], sem["num_students"], sem["study_programme_id"])
       semesters[sem_id] = semester


    # time structure
    START_SEMESTER_DATE     = state["time_structure"]["START_SEMESTER_DATE"]
    END_SEMESTER_DATE       = state["time_structure"]["END_SEMESTER_DATE"]
    NUM_WEEKS               = state["time_structure"]["NUM_WEEKS"]
    NUM_DAYS                = state["time_structure"]["NUM_DAYS"]
    NUM_HOURS               = state["time_structure"]["NUM_HOURS"]
    tblocks                 = state["time_structure"]["timeblocks"]
    hour_to_index           = state["time_structure"]["hour_to_index"]
    index_to_hour           = state["time_structure"]["index_to_hour"]

    year, month, day = int(START_SEMESTER_DATE[:4]), int(START_SEMESTER_DATE[5:7]), int(START_SEMESTER_DATE[8:10])
    START_SEMESTER_DATE = datetime(year, month, day)
    year, month, day = int(END_SEMESTER_DATE[:4]), int(END_SEMESTER_DATE[5:7]), int(END_SEMESTER_DATE[8:10])
    END_SEMESTER_DATE = datetime(year, month, day)

    # [Timeblock, ...]
    timeblocks = []
    for element in tblocks:
        index, tblock = element["index"], element["timeblock"]
        timeblock = Timeblock(index, tblock)
        timeblocks.append(timeblock)

    index_to_hour = {int(key):value for key,value in index_to_hour.items()}
    time_structure = TimeStructure(START_SEMESTER_DATE, END_SEMESTER_DATE, NUM_WEEKS, NUM_DAYS, NUM_HOURS, timeblocks, hour_to_index, index_to_hour)


    # rasps
    rasps, rasp_dict = [], {}
    for r in state["rasps"]:
        rasp = Rasp(r["id"], r["subject_id"], r["professor_id"], r["type"], r["group"], r["duration"], tuple(r["mandatory_in_semester_ids"]), tuple(r["optional_in_semester_ids"]), r["needs_computers"], r["total_groups"], r["fix_at_room_id"], r["random_dtstart_weekday"], r["fixed_hour"], r["rrule"])
        rasps.append(rasp)
        rasp_dict[rasp.id] = rasp

    # rooms {room_id : Classroom}
    rooms = {}
    for room_id, room in state["rooms"].items():
        typed_room = Classroom(room["id"], room["name"], room["capacity"], room["has_computers"])
        rooms[room_id] = typed_room


    # students_per_rasp {rasp_id : int}
    students_per_rasp = dict()
    for rasp_id, num_students in state["students_per_rasp"].items():
        students_per_rasp[rasp_id] = num_students

    #initial_constraints
    def typed_dict_3Darray(dictionary):
        new_dictionary = {}
        for obj_id, array3D in dictionary.items():
            numpy_3D = np.zeros(shape=(NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8)
            for week in range(NUM_WEEKS):
                for day in range(NUM_DAYS):
                    for hour in range(NUM_HOURS):
                        numpy_3D[week, day, hour] = array3D[week][day][hour]

            new_dictionary[obj_id] = numpy_3D
        return new_dictionary

    rooms_occupied     = typed_dict_3Darray(state["initial_constraints"]["rooms_occupied"])
    profs_occupied     = typed_dict_3Darray(state["initial_constraints"]["profs_occupied"])
    sems_occupied      = typed_dict_3Darray(state["initial_constraints"]["sems_occupied"])
    optionals_occupied = typed_dict_3Darray(state["initial_constraints"]["optionals_occupied"])
    sems_collisions    = typed_dict_3Darray(state["initial_constraints"]["sems_collisions"])

    initial_constraints = InitialConstraints(rooms_occupied, profs_occupied, sems_occupied, optionals_occupied, sems_collisions)

    #mutable_constraints
    rooms_occupied     = typed_dict_3Darray(state["mutable_constraints"]["rooms_occupied"])
    profs_occupied     = typed_dict_3Darray(state["mutable_constraints"]["profs_occupied"])
    sems_occupied      = typed_dict_3Darray(state["mutable_constraints"]["sems_occupied"])
    optionals_occupied = typed_dict_3Darray(state["mutable_constraints"]["optionals_occupied"])
    sems_collisions    = typed_dict_3Darray(state["mutable_constraints"]["sems_collisions"])

    mutable_constraints = MutableConstraints(rooms_occupied, profs_occupied, sems_occupied, optionals_occupied, sems_collisions)

    #groups
    groups = {key : set(value) for key, value in state["groups"].items()}

    #subject_types
    subject_types = {key : set(value) for key, value in state["subject_types"].items()}

    #timetable {Rasp : Slot}
    timetable = {}
    for rasp_id, the_slot in state["timetable"].items():
        rasp = rasp_dict[rasp_id]
        slot = Slot(the_slot["room_id"], the_slot["week"], the_slot["day"], the_slot["hour"])
        timetable[rasp] = slot


    grade = state["grade"]

    #rasp rrules {rasp_id : RaspRRULES}
    rasp_rrules = {}
    for rasp_id, the_rasp_rrules in state["rasp_rrules"].items():
        typed_rasp_rrule = {
                "DTSTART": tuple(the_rasp_rrules["DTSTART"]),
                "UNTIL":   tuple(the_rasp_rrules["UNTIL"]),
                "FREQ": the_rasp_rrules["FREQ"],
                "all_dates": [(week, day, hour) for week, day, hour in the_rasp_rrules["all_dates"]],
                "dtstart_weekdays": [(week, day) for week, day in the_rasp_rrules["dtstart_weekdays"]],
                "rrule_table_index": the_rasp_rrules["rrule_table_index"]
        }

        rasp_rrules[rasp_id] = typed_rasp_rrule

    #rrule_table ["(X,Y)" : [ all_dates1, all_dates2, ... ], ... ,"(X2,Y2)": [...]]
    rrule_table = []

    for element in state["rrule_table"]:
        typed_element = {}
        for key_str, all_dates in element.items():
            key_first  = int(key_str[1:key_str.index(",")])
            key_second = int(key_str[key_str.index(" ")+1:key_str.index(")")])
            key_tuple = (key_first, key_second)
            typed_element[key_tuple] = [(week, day) for week, day in all_dates]
        rrule_table.append(typed_element)

    new_state = State(is_winter, semesters, time_structure, rasps, rooms, students_per_rasp, initial_constraints, groups, subject_types, mutable_constraints, timetable, grade, rasp_rrules, rrule_table)

    with open(pickle_path, "wb") as p:
        pickle.dump(new_state, p)


def pickle_to_json(pickle_path, json_path):
    with open(pickle_path, "rb") as f:
        state = pickle.load(f)

    time_structure = {
            "START_SEMESTER_DATE": state.time_structure.START_SEMESTER_DATE.isoformat(),
            "END_SEMESTER_DATE": state.time_structure.END_SEMESTER_DATE.isoformat(),
            "NUM_WEEKS": state.time_structure.NUM_WEEKS,
            "NUM_DAYS": state.time_structure.NUM_DAYS,
            "NUM_HOURS": state.time_structure.NUM_HOURS,
            "timeblocks": [block._asdict() for block in state.time_structure.timeblocks],
            "hour_to_index": state.time_structure.hour_to_index,
            "index_to_hour": state.time_structure.index_to_hour
    }

    initial_constraints = {
        "rooms_occupied"     : {room_id : matrix3D.tolist() for room_id, matrix3D in state.initial_constraints.rooms_occupied.items()},
        "profs_occupied"     : {prof_id : matrix3D.tolist() for prof_id, matrix3D in state.initial_constraints.profs_occupied.items()},
        "sems_occupied"      : {sem_id  : matrix3D.tolist() for sem_id, matrix3D  in state.initial_constraints.sems_occupied.items()},
        "optionals_occupied" : {sem_id  : matrix3D.tolist() for sem_id, matrix3D  in state.initial_constraints.optionals_occupied.items()},
        "sems_collisions"    : {sem_id  : matrix3D.tolist() for sem_id, matrix3D  in state.initial_constraints.sems_collisions.items()}
    }

    mutable_constraints = {
        "rooms_occupied"     : {room_id : matrix3D.tolist() for room_id, matrix3D in state.mutable_constraints.rooms_occupied.items()},
        "profs_occupied"     : {prof_id : matrix3D.tolist() for prof_id, matrix3D in state.mutable_constraints.profs_occupied.items()},
        "sems_occupied"      : {sem_id  : matrix3D.tolist() for sem_id, matrix3D  in state.mutable_constraints.sems_occupied.items()},
        "optionals_occupied" : {sem_id  : matrix3D.tolist() for sem_id, matrix3D  in state.mutable_constraints.optionals_occupied.items()},
        "sems_collisions"    : {sem_id  : matrix3D.tolist() for sem_id, matrix3D  in state.mutable_constraints.sems_collisions.items()}
    }

    rrule_table = []
    for obj in state.rrule_table:
        new_obj = {}
        for key, the_list in obj.items():
            new_obj[str(key)] = the_list
        rrule_table.append(new_obj)

    for key, val in state.grade.items():
        state.grade[key] = int(val)

    state_json = {
            "is_winter": state.is_winter,
            "semesters": {sem_id : sem._asdict() for sem_id, sem in state.semesters.items()},
            "time_structure": time_structure,
            "rasps": [rasp._asdict() for rasp in state.rasps],
            "rooms": {room_id : room._asdict() for room_id, room in state.rooms.items()},
            "students_per_rasp": dict(state.students_per_rasp),
            "initial_constraints": initial_constraints,
            "mutable_constraints": mutable_constraints,
            "groups": {id_ : list(group_set) for id_, group_set in state.groups.items()},
            "subject_types": {id_ : list(type_set) for id_, type_set in state.subject_types.items()},
            "timetable": {rasp.id : slot._asdict() for rasp, slot in state.timetable.items()},
            "grade": state.grade,
            "rasp_rrules": state.rasp_rrules,
            "rrule_table": rrule_table
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(state_json, f)

