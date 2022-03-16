import optimizer.grade_tool as grade_tool

"""
Returns an empty action object.
Used to determine which dates can be skipped (banned).
"""
def init_action():
    return {"ban_dates": set(),
            "ban_capacity": False,
            "ban_computers": False,
            "ban_capacity_with_dates": set(),
            "ban_computers_with_dates": set(),
            "ban_capacity_with_computers": False,
            "ban_dates_with_capacity_with_computers": set()}


"""
Updates action object with knowledge gained from new slot grade and old slot grade.
E.g. if professor + nast grade is worse than the old total grade then we can skip
     that slot in the future because it will have the same problem.
"""
def failure_reason(state, action, slot, rasp, pure_new_slot_grade, pure_old_slot_grade):
    rasp_rrules = state.rasp_rrules

    old_total     = pure_old_slot_grade["totalScore"]
    new_professor = pure_new_slot_grade["professorScore"]
    new_nast      = pure_new_slot_grade["nastScore"]
    new_capacity  = pure_new_slot_grade["capacityScore"]
    new_computer  = pure_new_slot_grade["computerScore"]
    _, week, day, hr = slot

    ban_slot = (day, hr) if rasp_rrules[rasp.id]["FREQ"] == "WEEKLY" else (week, day, hr)

    # <= because values are negative (e.g. -1200 is worse than -1000)
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


"""
Updates action object with knowledge gained from new slot grade and old slot grade.
It's a more rigorous version of the original function where no collisions are allowed.
Any collisions and the slot will be skipped in the future.
Used in special cases where no collisions are allowed.
"""
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


"""
Returns True if slot is skippable by the optimizer algorithm.
"""
def is_skippable(state, slot, rasp, action):
    rasp_rrules = state.rasp_rrules

    room_id, week,day,hr = slot
    ban_slot = (day, hr) if rasp_rrules[rasp.id]["FREQ"] == "WEEKLY" else (week, day, hr)

    if ban_slot in action["ban_dates"]:
        return True
    if action["ban_capacity"] and grade_tool.is_capacity_problematic(state, rasp, room_id):
        return True
    if action["ban_computers"] and grade_tool.is_computer_problematic(state, rasp, room_id):
        return True
    if ban_slot in action["ban_capacity_with_dates"] and grade_tool.is_capacity_problematic(state, rasp, room_id):
        return True
    if ban_slot in action["ban_computers_with_dates"] and grade_tool.is_computer_problematic(state, rasp, room_id):
        return True
    if action["ban_capacity_with_computers"] and grade_tool.is_computer_problematic(state, rasp, room_id) and grade_tool.is_capacity_problematic(state, rasp, room_id):
        return True
    if ban_slot in action["ban_dates_with_capacity_with_computers"] and grade_tool.is_capacity_problematic(state, rasp, room_id) and grade_tool.is_computer_problematic(state, rasp, room_id):
        return True
    return False
