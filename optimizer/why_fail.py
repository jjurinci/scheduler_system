"""
Returns an empty action object.
Used to determine which dates can be skipped (banned).
"""
def init_action():
    return {"ban_dates": set(), "ban_rooms": set()}


"""
Updates action object with knowledge gained from new slot grade and old slot grade.
E.g. if professor + sem grade is worse than the old total grade then we can skip
     that slot in the future because it will have the same problem.
"""
def failure_reason(action, slot, only_new_slot_grade, only_old_slot_grade):
    old_total     = only_old_slot_grade["totalScore"]
    new_professor = only_new_slot_grade["professorScore"]
    new_sem       = only_new_slot_grade["semScore"]
    new_capacity  = only_new_slot_grade["capacityScore"]
    new_computer  = only_new_slot_grade["computerScore"]
    room_id, week, day, hr = slot
    ban_slot = (week, day, hr)

    # <= because values are negative (e.g. -1200 is worse than -1000)
    if new_professor + new_sem <= old_total:
        action["ban_dates"].add(ban_slot)

    if new_capacity + new_computer <= old_total:
        action["ban_rooms"].add(room_id)


"""
Returns True if slot is skippable by the optimizer algorithm.
"""
def is_skippable(slot, action):
    room_id,week,day,hr = slot
    ban_slot = (week, day, hr)
    return ban_slot in action["ban_dates"] or room_id in action["ban_rooms"]

