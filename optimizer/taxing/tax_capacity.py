"""
Detects capacity problems and taxes them in grade.
"""
def tax_capacity(state, room_id, rasp):
    grade = state.grade
    students_per_rasp = state.students_per_rasp
    rooms = state.rooms

    if bool(students_per_rasp[rasp.id] - rooms[room_id].capacity>0):
        grade["capacityScore"] += -30
        grade["totalScore"] += -30


"""
Detects capacity problems and untaxes them in grade.
Used to undo the previous tax.
"""
def untax_capacity(state, room_id, rasp):
    grade = state.grade
    students_per_rasp = state.students_per_rasp
    rooms = state.rooms

    if bool(students_per_rasp[rasp.id] - rooms[room_id].capacity>0):
        grade["capacityScore"] += 30
        grade["totalScore"] += 30
