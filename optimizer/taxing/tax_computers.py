"""
Detects computer problems and taxes them in grade.
"""
def tax_computers(state, room_id, rasp):
    grade = state.grade
    rooms = state.rooms

    if not rooms[room_id].has_computers and rasp.needs_computers:
        grade["computerScore"] += -30
        grade["totalScore"] += -30

    #if rooms[room_id].has_computers and not rasp.needs_computers:
    #    grade["computerScore"] += -30*0.1
    #    grade["totalScore"] += -30*0.1


"""
Detects computer problems and untaxes them in grade.
Used to undo the previous tax.
"""
def untax_computers(state, room_id, rasp):
    grade = state.grade
    rooms = state.rooms

    if not rooms[room_id].has_computers and rasp.needs_computers:
        grade["computerScore"] += 30
        grade["totalScore"] += 30

    #if rooms[room_id].has_computers and not rasp.needs_computers:
    #    grade["computerScore"] += 30 * 0.1
    #    grade["totalScore"] += 30 * 0.1
