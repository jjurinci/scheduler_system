import optimizer.grade_tool as grade_tool
import pickle

"""
Returns complete state from a .pickle file.
"""
def load_state():
    name = "saved_timetables/errors_timetable.pickle"
    with open(name, "rb") as f:
        state = pickle.load(f)
    return state

"""
Given a timetable: the function iterates through all rasps, finds if they
have room, prof, nast collisions in their slot OR capacity, computer problems
in their room.
"""
def analyze_timetable():
    state = load_state()
    timetable = state.timetable

    for rasp, slot in timetable.items():
        room_id, week, day, hour = slot
        send_slot = (week, day, hour)
        if grade_tool.is_room_problematic(state, rasp, room_id, send_slot):
            print(f"{rasp.id} has a room collision at {room_id} {week},{day},{hour}")
        if grade_tool.is_prof_problematic(state, rasp, send_slot):
            print(f"{rasp.id} has a professor collision at {rasp.professor_id} {week},{day},{hour}")
        if grade_tool.is_nast_problematic(state, rasp, send_slot):
            sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
            print(f"{rasp.id} has a semester collision at some of the {sem_ids} {week},{day},{hour}")
        if grade_tool.is_capacity_problematic(state, rasp, room_id):
            print(f"{rasp.id} has a capacity problem at {room_id} {week},{day},{hour}")
        if grade_tool.is_computer_problematic(state, rasp, room_id):
            print(f"{rasp.id} has a computer problem at {room_id} {week},{day},{hour}")

analyze_timetable()
