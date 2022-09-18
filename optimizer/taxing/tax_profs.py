"""
Detects professor collisions along the rasp's all dates path and taxes them.
"""
def tax_rrule_in_profs(state, rasp):
    all_dates     = state.rasp_rrules[rasp.id]["all_dates"]
    prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id]

    cnt = 0
    for week, day, hour in all_dates:
        prof_occupied[week, day, hour] += 1
        cnt += prof_occupied[week, day, hour] if prof_occupied[week, day, hour]>1 else 0
    if cnt:
        punish = -cnt*30
        update_grade_profs(state, punish, plus=True)


"""
Detects professor collisions along the rasp's all dates path and untaxes them.
Used to undo the previous tax.
"""
def untax_rrule_in_profs(state, rasp):
    all_dates     = state.rasp_rrules[rasp.id]["all_dates"]
    prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id]

    cnt = 0
    for week, day, hour in all_dates:
        cnt += prof_occupied[week, day, hour] if prof_occupied[week, day, hour]>1 else 0
        prof_occupied[week, day, hour] -= 1

    if cnt:
        punish = -cnt*30
        update_grade_profs(state, punish, plus=False)


"""
Updates the grade with calculated "punish" score.
"""
def update_grade_profs(state, punish, plus=True):
    grade = state.grade

    if plus:
        grade["professorScore"] += punish
        grade["totalScore"] += punish
    else:
        grade["professorScore"] -= punish
        grade["totalScore"] -= punish

