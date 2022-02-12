def failure_reason(state, action, slot, rasp, pure_new_slot_grade, pure_old_slot_grade):
    rasp_rrules = state.rasp_rrules

    old_total     = pure_old_slot_grade["totalScore"]
    new_professor = pure_new_slot_grade["professorScore"]
    new_nast      = pure_new_slot_grade["nastScore"]
    new_capacity  = pure_new_slot_grade["capacityScore"]
    new_computer  = pure_new_slot_grade["computerScore"]
    _, week, day, hr = slot

    ban_slot = (day, hr) if rasp_rrules[rasp.id]["FREQ"] == "WEEKLY" else (week, day, hr)

    if new_professor + new_nast <= old_total:
        action["ban_dates"].add(ban_slot)

    if new_capacity <= old_total:
        action["ban_capacity"] = True

    if new_computer <= old_total:
        action["ban_computers"] = True

    if new_professor + new_nast + new_capacity <= old_total:
        action["ban_capacity_with_dates"].add(ban_slot)

    if new_professor + new_nast + new_computer <= old_total:
        action["ban_computers_with_dates"].add(ban_slot)

    if new_capacity + new_computer <= old_total:
        action["ban_capacity_with_computers"] = True

    if new_professor + new_nast + new_capacity + new_computer <= old_total:
        action["ban_dates_with_capacity_with_computers"].add(ban_slot)


def failure_reason_rigorous(state, action, slot, rasp, pure_new_slot_grade):
    rasp_rrules = state.rasp_rrules

    new_professor = pure_new_slot_grade["professorScore"]
    new_nast      = pure_new_slot_grade["nastScore"]
    new_capacity  = pure_new_slot_grade["capacityScore"]
    new_computer  = pure_new_slot_grade["computerScore"]
    _, week, day, hr = slot

    ban_slot = (day, hr) if rasp_rrules[rasp.id]["FREQ"] == "WEEKLY" else (week, day, hr)

    if new_professor + new_nast:
        action["ban_dates"].add(ban_slot)

    if new_capacity:
        action["ban_capacity"] = True

    if new_computer:
        action["ban_computers"] = True

    if new_professor + new_nast + new_capacity:
        action["ban_capacity_with_dates"].add(ban_slot)

    if new_professor + new_nast + new_computer:
        action["ban_computers_with_dates"].add(ban_slot)

    if new_capacity + new_computer:
        action["ban_capacity_with_computers"] = True

    if new_professor + new_nast + new_capacity + new_computer:
        action["ban_dates_with_capacity_with_computers"].add(ban_slot)


def insufficient_capacity(state, rasp, room_id):
    rooms = state.rooms
    students_per_rasp = state.students_per_rasp
    return students_per_rasp[rasp.id] - rooms[room_id].capacity>0


def insufficient_computers(state, rasp, room_id):
    rooms = state.rooms
    return ((not rooms[room_id].has_computers and rasp.needs_computers) or (rooms[room_id].has_computers and not rasp.needs_computers))


def insufficient_strong_computers(state, rasp, room_id):
    rooms = state.rooms
    return not rooms[room_id].has_computers and rasp.needs_computers


def insufficient_weak_computers(state, rasp, room_id):
    rooms = state.rooms
    return rooms[room_id].has_computers and not rasp.needs_computers


def is_skippable(state, slot, rasp, action):
    rasp_rrules = state.rasp_rrules

    room_id, week,day,hr = slot
    ban_slot = (day, hr) if rasp_rrules[rasp.id]["FREQ"] == "WEEKLY" else (week, day, hr)

    if ban_slot in action["ban_dates"]:
        return True
    if action["ban_capacity"] and insufficient_capacity(state, rasp, room_id):
        return True
    if action["ban_computers"] and insufficient_computers(state, rasp, room_id):
        return True
    if ban_slot in action["ban_capacity_with_dates"] and insufficient_capacity(state, rasp, room_id):
        return True
    if ban_slot in action["ban_computers_with_dates"] and insufficient_computers(state, rasp, room_id):
        return True
    if action["ban_capacity_with_computers"] and insufficient_computers(state, rasp, room_id) and insufficient_capacity(state, rasp, room_id):
        return True
    if ban_slot in action["ban_dates_with_capacity_with_computers"] and insufficient_capacity(state, rasp, room_id) and insufficient_computers(state, rasp, room_id):
        return True
    return False


def init_action():
    return {"ban_dates": set(),
            "ban_capacity": False,
            "ban_computers": False,
            "ban_capacity_with_dates": set(),
            "ban_computers_with_dates": set(),
            "ban_capacity_with_computers": False,
            "ban_dates_with_capacity_with_computers": set()}

