import data_api.constraints as cons_api

"""
Taxes rasp in all of its semesters
1) Enumerates all semesters of a rasp.
2) Checks if rasp is mandatory or optional in that semester
3) Calls the appropriate tax function
"""
def tax_rrule_in_sems(state, rasp):
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        if rasp_mandatory:
            tax_rrule_in_sems_mandatory(state, sem_id, rasp)
        else:
            tax_rrule_in_sems_optional(state, sem_id, rasp)


"""
Untaxes rasp in all of its semesters
1) Enumerates all semesters of a rasp.
2) Checks if rasp is mandatory or optional in that semester
3) Calls the appropriate untax function
"""
def untax_rrule_in_sems(state, rasp):
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        if rasp_mandatory:
            untax_rrule_in_sems_mandatory(state, sem_id, rasp)
        else:
            untax_rrule_in_sems_optional(state, sem_id, rasp)


"""
Detects semester collisions along the mandatory rasp's all dates path and taxes them.
It does NOT tax parallel mandatory groups.
"""
def tax_rrule_in_sems_mandatory(state, sem_id, rasp):
    all_dates       = state.rasp_rrules[rasp.id]["all_dates"]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    sem_occupied    = state.mutable_constraints.sems_occupied[sem_id]
    sem_collisions  = state.mutable_constraints.sems_collisions[sem_id]

    punish = 0
    for week, day, hour in all_dates:
        old_cnt_occ, old_cnt_colls = sem_occupied[week, day, hour], sem_collisions[week, day, hour]

        # If (week, day, hour) is not taken by a group (allow parallel groups)
        if (week, day, hour) not in own_group_dates:
            sem_collisions[week, day, hour] += 1

        new_cnt_colls = sem_collisions[week, day, hour]
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls)
        sem_occupied[week, day, hour] += 1

    if punish:
        update_grade_sems(state, punish, plus=True)


"""
Detects semester collisions along the mandatory rasp's all dates path and untaxes them.
It does NOT untax parallel groups.
"""
def untax_rrule_in_sems_mandatory(state, sem_id, rasp):
    all_dates       = state.rasp_rrules[rasp.id]["all_dates"]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    sem_occupied    = state.mutable_constraints.sems_occupied[sem_id]
    sem_collisions  = state.mutable_constraints.sems_collisions[sem_id]

    punish = 0
    for week, day, hour in all_dates:
        old_cnt_occ, old_cnt_colls = sem_occupied[week, day, hour], sem_collisions[week, day, hour]

        if (week, day, hour) not in own_group_dates:
            sem_collisions[week, day, hour] -= 1

        new_cnt_colls = sem_collisions[week, day, hour]
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ-1, new_cnt_colls)
        sem_occupied[week, day, hour] -= 1

    if punish:
        update_grade_sems(state, punish, plus=False)


"""
Detects semester collisions along the optional rasp's all dates path and taxes them.
It does NOT tax parallel optionals.
"""
def tax_rrule_in_sems_optional(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)
    sem_occupied    = state.mutable_constraints.sems_occupied[sem_id]
    optional_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    sem_collisions  = state.mutable_constraints.sems_collisions[sem_id]

    punish = 0
    for week, day, hour in all_dates:
        old_cnt_occ, old_cnt_colls = sem_occupied[week, day, hour], sem_collisions[week, day, hour]

        if not (week, day, hour) in own_group_dates and (optional_occupied[week, day, hour] == 0 or (week, day, hour) in other_groups_dates):
            sem_collisions[week, day, hour] += 1

        new_cnt_colls = sem_collisions[week, day, hour]
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls)
        sem_occupied[week, day, hour] += 1
        optional_occupied[week, day, hour] += 1

    if punish:
        update_grade_sems(state, punish, plus=True)


"""
Detects semester collisions along the optional rasp's all dates path and untaxes them.
It does NOT untax parallel optionals.
"""
def untax_rrule_in_sems_optional(state, sem_id, rasp):
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)
    sem_occupied    = state.mutable_constraints.sems_occupied[sem_id]
    optionals_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    sem_collisions = state.mutable_constraints.sems_collisions[sem_id]

    punish = 0
    for week, day, hour in all_dates:
        old_cnt_occ, old_cnt_colls = sem_occupied[week, day, hour], sem_collisions[week, day, hour]

        if (week, day, hour) not in own_group_dates and (optionals_occupied[week, day, hour] == 1 or (week, day, hour) in other_groups_dates):
            sem_collisions[week, day, hour] -= 1

        new_cnt_colls = sem_collisions[week, day, hour]
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ-1, new_cnt_colls)
        sem_occupied[week, day, hour] -= 1
        optionals_occupied[week, day, hour] -= 1

    if punish:
        update_grade_sems(state, punish, plus=False)


def sems_tax_punish(old_cnt_occ, old_cnt_colls, new_cnt_occ, new_cnt_colls):
    old_score = 0 if old_cnt_colls <= 1  else old_cnt_occ * -30
    new_score = 0 if new_cnt_colls <= 1  else new_cnt_occ * -30
    return -abs(old_score - new_score)


"""
Updates the grade with calculated "punish" score.
"""
def update_grade_sems(state, punish, plus=True):
    grade = state.grade
    if plus:
        grade["semScore"] += punish
        grade["totalScore"] += punish
    else:
        grade["semScore"] -= punish
        grade["totalScore"] -= punish

