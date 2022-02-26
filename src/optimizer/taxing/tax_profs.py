import numpy as np

"""
Detects professor collisions along the rasp's all dates path and taxes them.
"""
def tax_rrule_in_profs(state, rasp):
    all_dates     = state.rasp_rrules[rasp.id]["all_dates"]
    prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id]

    for week, day, hour in all_dates:
        prof_occupied[week, day, hour:(hour + rasp.duration)] += 1
        cnt = np.sum(prof_occupied[week, day, hour:(hour + rasp.duration)]>1)
        if cnt:
            punish = -cnt*30
            update_grades_profs(state, rasp, punish, plus=True)


"""
Detects professor collisions along the rasp's all dates path and untaxes them.
Used to undo the previous tax.
"""
def untax_rrule_in_profs(state, rasp):
    all_dates     = state.rasp_rrules[rasp.id]["all_dates"]
    prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id]

    for week, day, hour in all_dates:
        cnt = np.sum(prof_occupied[week, day, hour:(hour + rasp.duration)]>1)
        prof_occupied[week, day, hour:(hour + rasp.duration)] -= 1
        if cnt:
            punish = -cnt*30
            update_grades_profs(state, rasp, punish, plus=False)


"""
Updates the grade with calculated "punish" score.
"""
def update_grades_profs(state, rasp, punish, plus=True):
    grades = state.grades

    if plus:
        grades["profs"][rasp.professor_id] += punish
        grades["all"]["professorScore"] += punish
        grades["all"]["totalScore"] += punish
    else:
        grades["profs"][rasp.professor_id] -= punish
        grades["all"]["professorScore"] -= punish
        grades["all"]["totalScore"] -= punish

