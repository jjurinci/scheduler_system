def tax_capacity(state, room_id, rasp):
    grades = state.grades
    students_per_rasp = state.students_per_rasp
    rooms = state.rooms

    if bool(students_per_rasp[rasp.id] - rooms[room_id].capacity>0):
        grades["all"]["capacityScore"] += -30
        grades["all"]["totalScore"] += -30
        grades["rooms"][room_id]["roomScore"] += -30
        grades["rooms"][room_id]["capacityScore"] += -30


def untax_capacity(state, room_id, rasp):
    grades = state.grades
    students_per_rasp = state.students_per_rasp
    rooms = state.rooms

    if bool(students_per_rasp[rasp.id] - rooms[room_id].capacity>0):
        grades["all"]["capacityScore"] += 30
        grades["all"]["totalScore"] += 30
        grades["rooms"][room_id]["roomScore"] += 30
        grades["rooms"][room_id]["capacityScore"] += 30
