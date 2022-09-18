import optimizer.grade_tool as grade_tool
from utilities.general_utilities import load_state

"""
Given a timetable: the function iterates through all rasps, finds if they
have room, prof, sem collisions in their slot OR capacity, computer problems
in their room.
"""
def analyze_timetable():
    state = load_state()
    timetable = state.timetable
    rasp_rrules = state.rasp_rrules
    rooms_occupied = state.mutable_constraints.rooms_occupied
    profs_occupied = state.mutable_constraints.profs_occupied
    sems_collisions = state.mutable_constraints.sems_collisions

    for rasp, slot in timetable.items():
        room_id, _, _, _ = slot
        for week, day, hour in rasp_rrules[rasp.id]["all_dates"]:
            if rooms_occupied[room_id][week, day, hour] > 1:
                print(f"{rasp.id} has a room collision at {room_id} {week},{day},{hour}")
            if profs_occupied[rasp.professor_id][week, day, hour] > 1:
                print(f"{rasp.id} has a professor collision at {rasp.professor_id} {week},{day},{hour}")
            sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
            for sem_id in sem_ids:
                if sems_collisions[sem_id][week, day, hour] > 1:
                    print(f"{rasp.id} has a semester collision at {sem_id} at {week},{day},{hour}")

        if grade_tool.is_capacity_problematic(state, rasp, room_id):
            print(f"{rasp.id} has a capacity problem at {room_id}")
        if grade_tool.is_computer_problematic(state, rasp, room_id):
            print(f"{rasp.id} has a computer problem at {room_id}")

analyze_timetable()
