"""
Detects room collisions along the rasp's all dates path and taxes them.
"""
def tax_rrule_in_rooms(state, room_id, rasp):
    all_dates      = state.rasp_rrules[rasp.id]["all_dates"]
    room_occupied  = state.mutable_constraints.rooms_occupied[room_id]

    cnt = 0
    for week, day, hour in all_dates:
        room_occupied[week, day, hour] += 1
        cnt += room_occupied[week, day, hour] if room_occupied[week, day, hour] > 1 else 0
    if cnt:
        punish = -cnt*30
        update_grade_rooms(state, punish, plus=True)


"""
Detects room collisions along the rasp's all dates path and untaxes them.
Used to undo the previous tax.
"""
def untax_rrule_in_rooms(state, room_id, rasp):
    all_dates      = state.rasp_rrules[rasp.id]["all_dates"]
    room_occupied  = state.mutable_constraints.rooms_occupied[room_id]

    cnt = 0
    for week, day, hour in all_dates:
        cnt += room_occupied[week, day, hour] if room_occupied[week, day, hour] > 1 else 0
        room_occupied[week, day, hour] -= 1
    if cnt:
        punish = -cnt*30
        update_grade_rooms(state, punish, plus=False)


"""
Updates the grade with calculated "punish" score.
"""
def update_grade_rooms(state, punish, plus=True):
    grade = state.grade
    if plus:
        grade["roomScore"] += punish
        grade["totalScore"] += punish
    else:
        grade["roomScore"] -= punish
        grade["totalScore"] -= punish

