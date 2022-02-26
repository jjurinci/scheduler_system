import pickle
import optimizer.grade_tool as grade_tool
import analysis.analyze_movement as move_tool

"""
Returns complete state from a .pickle file.
"""
def load_state():
    name = "saved_timetables/zero_timetable.pickle"
    with open(name, "rb") as f:
        state = pickle.load(f)
    return state


"""
Given a rasp, function prints which rooms are available for the rasp to be moved to.
Available means that there are capacity or computer problems AND that there is
at least one free slot there (no rrule collisions of rooms, profs, and semesters).

Function iterates through all rasps and prints available rooms for illustrative purposes.
In practice, user would click on 1 rasp and function would return available rooms
just for that rasp.
"""
def analyze_room_change():
    state = load_state()
    timetable = state.timetable
    rooms = state.rooms
    students_per_rasp = state.students_per_rasp

    for rasp, _ in timetable.items():
        found = False
        for room in rooms.values():
            if not grade_tool.is_capacity_problematic(state, rasp, room.id) and \
               not grade_tool.is_computer_problematic(state, rasp, room.id):
                   other_free_slots = move_tool.get_other_free_slots(state, rasp, room.id)
                   if other_free_slots:
                       found = True
                       print(rasp.id, students_per_rasp[rasp.id], "|", room.id, room.capacity, room.has_computers, other_free_slots)
        if not found:
            print(rasp.id, students_per_rasp[rasp.id], "| didn't find a room.")

analyze_room_change()
