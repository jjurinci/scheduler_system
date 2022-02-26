"""
Detects computer problems and taxes them in grades.
"""
def tax_computers(state, room_id, rasp):
    grades = state.grades
    rooms = state.rooms

    if not rooms[room_id].has_computers and rasp.needs_computers:
        grades["all"]["computerScore"] += -30
        grades["all"]["totalScore"] += -30
        grades["rooms"][room_id]["roomScore"] += -30
        grades["rooms"][room_id]["computerScore"] += -30

    if rooms[room_id].has_computers and not rasp.needs_computers:
        grades["all"]["computerScore"] += -30*0.1
        grades["all"]["totalScore"] += -30*0.1
        grades["rooms"][room_id]["roomScore"] += -30*0.1
        grades["rooms"][room_id]["computerScore"] += -30*0.1


"""
Detects computer problems and untaxes them in grades.
Used to undo the previous tax.
"""
def untax_computers(state, room_id, rasp):
    grades = state.grades
    rooms = state.rooms

    if not rooms[room_id].has_computers and rasp.needs_computers:
        grades["all"]["computerScore"] += 30
        grades["all"]["totalScore"] += 30
        grades["rooms"][room_id]["roomScore"] += 30
        grades["rooms"][room_id]["computerScore"] += 30

    if rooms[room_id].has_computers and not rasp.needs_computers:
        grades["all"]["computerScore"] += 30 * 0.1
        grades["all"]["totalScore"] += 30 * 0.1
        grades["rooms"][room_id]["roomScore"] += 30*0.1
        grades["rooms"][room_id]["computerScore"] += 30*0.1
