import numpy as np

"""
Detects room collisions along the rasp's all dates path and taxes them.
"""
def tax_rrule_in_rooms(state, room_id, rasp):
    all_dates      = state.rasp_rrules[rasp.id]["all_dates"]
    room_occupied  = state.mutable_constraints.rooms_occupied[room_id]

    for week, day, hour in all_dates:
        room_occupied[week, day, hour:(hour + rasp.duration)] += 1
        cnt = np.sum(room_occupied[week, day, hour:(hour + rasp.duration)]>1)
        if cnt:
            punish = -cnt*30
            update_grades_rooms(state, room_id, punish, plus=True)


"""
Detects room collisions along the rasp's all dates path and untaxes them.
Used to undo the previous tax.
"""
def untax_rrule_in_rooms(state, room_id, rasp):
    all_dates      = state.rasp_rrules[rasp.id]["all_dates"]
    room_occupied  = state.mutable_constraints.rooms_occupied[room_id]

    for week, day, hour in all_dates:
        cnt = np.sum(room_occupied[week, day, hour:(hour + rasp.duration)]>1)
        room_occupied[week, day, hour:(hour + rasp.duration)] -= 1
        if cnt:
            punish = -cnt*30
            update_grades_rooms(state, room_id, punish, plus=False)


"""
Updates the grade with calculated "punish" score.
"""
def update_grades_rooms(state, room_id, punish, plus=True):
    grades = state.grades
    if plus:
        grades["rooms"][room_id]["roomScore"] += punish
        grades["all"]["roomScore"] += punish
        grades["all"]["totalScore"] += punish
    else:
        grades["rooms"][room_id]["roomScore"] -= punish
        grades["all"]["roomScore"] -= punish
        grades["all"]["totalScore"] -= punish

