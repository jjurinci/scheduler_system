import numpy as np
import data_api.constraints as cons_api

def tax_rrule_in_nasts(state, rasp):
    semesters = state.semesters
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        parallel_optionals = True if semesters[sem_id].has_optional_subjects == 1 else False
        if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
            tax_rrule_in_nasts_mandatory(state, sem_id, rasp)
        elif not rasp_mandatory and parallel_optionals:
            tax_rrule_in_nasts_optional(state, sem_id, rasp)


def untax_rrule_in_nasts(state, rasp):
    semesters = state.semesters
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        parallel_optionals = True if semesters[sem_id].has_optional_subjects == 1 else False
        if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
            untax_rrule_in_nasts_mandatory(state, sem_id, rasp)
        elif not rasp_mandatory and parallel_optionals:
            untax_rrule_in_nasts_optional(state, sem_id, rasp)


def tax_rrule_in_nasts_mandatory(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)

    for week, day, hour in all_dates:
        cnt = 0
        for hr in range(hour, hour + rasp.duration):
            # If (week, day, hour) is not taken by a group
            if (week, day, hr) not in own_group_dates:
                nast_occupied[week, day, hr] += 1
                cnt += np.sum(nast_occupied[week, day, hr]>1)
        if cnt:
            punish = -cnt*30
            update_grades_nasts(state, sem_id, punish, plus=True)


def untax_rrule_in_nasts_mandatory(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)

    for week, day, hour in all_dates:
        cnt = 0
        for hr in range(hour, hour + rasp.duration):
            if (week, day, hr) not in own_group_dates:
                cnt += np.sum(nast_occupied[week, day, hr]>1)
                nast_occupied[week, day, hr] -= 1
        if cnt:
            punish = -cnt*30
            update_grades_nasts(state, sem_id, punish, plus=False)


def untax_rrule_in_nasts_optional(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    optionals_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)

    for week, day, hour in all_dates:
        cnt = 0
        for hr in range(hour, hour + rasp.duration):
            if optionals_occupied[week, day, hr] == 1 or (week, day, hr) in other_groups_dates:
                cnt += np.sum(nast_occupied[week, day, hr]>1)
                nast_occupied[week, day, hr] -= 1
        if cnt:
            punish = -cnt*30
            update_grades_nasts(state, sem_id, punish, plus=False)
        optionals_occupied[week, day, hour:(hour + rasp.duration)] -= 1


def tax_rrule_in_nasts_optional(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    optional_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)

    for week, day, hour in all_dates:
        cnt = 0
        for hr in range(hour, hour + rasp.duration):
            if optional_occupied[week, day, hr] == 0 or (week, day, hr) in other_groups_dates:
                nast_occupied[week, day, hr] += 1
                cnt += np.sum(nast_occupied[week, day, hr]>1)
        if cnt:
            punish = -cnt*30
            update_grades_nasts(state, sem_id, punish, plus=True)
        optional_occupied[week, day, hour:(hour + rasp.duration)] += 1


def update_grades_nasts(state, sem_id, punish, plus=True):
    grades = state.grades
    if plus:
        grades["nasts"][sem_id] += punish
        grades["all"]["nastScore"] += punish
        grades["all"]["totalScore"] += punish
    else:
        grades["nasts"][sem_id] -= punish
        grades["all"]["nastScore"] -= punish
        grades["all"]["totalScore"] -= punish
