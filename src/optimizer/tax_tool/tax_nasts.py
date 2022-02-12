import numpy as np

def tax_rrule_in_nasts(state, slot, rasp):
    groups_occupied = state.mutable_constraints.groups_occupied
    semesters = state.semesters

    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    key = str(rasp.subject_id) + str(rasp.type)
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        parallel_optionals = True if semesters[sem_id].has_optional_subjects == 1 else False
        if rasp.total_groups == 1:
            if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                # Tax semester fully
                tax_rrule_in_nasts_mandatory(state, sem_id, rasp)
            elif not rasp_mandatory and parallel_optionals:
                # Tax only if it's the first optional at that slot
                tax_rrule_in_nasts_optional(state, sem_id, rasp)

        elif rasp.total_groups > 1:
            if slot not in groups_occupied[key]:
                groups_occupied[key][slot] = 0
            if rasp_mandatory and groups_occupied[key][slot] == 0:
                # Tax only if it's the first "subject_id + type" at that slot
                tax_rrule_in_nasts_mandatory(state, sem_id, rasp)
            elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                # Tax only if it's the first "subject_id + type" at that slot AND first optional at that slot
                tax_rrule_in_nasts_optional(state, sem_id, rasp)
            #assert groups_occupied[key][slot] >= 0
            groups_occupied[key][slot] += 1


def untax_rrule_in_nasts(state, slot, rasp):
    groups_occupied = state.mutable_constraints.groups_occupied
    semesters = state.semesters

    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    key = str(rasp.subject_id) + str(rasp.type)
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        parallel_optionals = True if semesters[sem_id].has_optional_subjects == 1 else False
        if rasp.total_groups == 1:
            if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                # Untax semester
                untax_rrule_in_nasts_mandatory(state, sem_id, rasp)
            elif not rasp_mandatory and parallel_optionals:
                # Untax only if it's the last optional at that slot
                untax_rrule_in_nasts_optional(state, sem_id, rasp)

        elif rasp.total_groups > 1:
            groups_occupied[key][slot] -= 1
            #assert groups_occupied[key][slot] >= 0
            if rasp_mandatory and groups_occupied[key][slot] == 0:
                # Untax only if it's the last "subject_id + type" at that slot
                untax_rrule_in_nasts_mandatory(state, sem_id, rasp)
            elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                # Untax only if it's the last "subject_id + type" at that slot AND last optional at that slot
                untax_rrule_in_nasts_optional(state, sem_id, rasp)


def tax_rrule_in_nasts_mandatory(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]

    for week, day, hour in all_dates:
        nast_occupied[week, day, hour:(hour + rasp.duration)] += 1
        cnt = np.sum(nast_occupied[week, day, hour:(hour + rasp.duration)]>1)
        if cnt:
            punish = -cnt*30
            update_grades_nasts(state, sem_id, punish, plus=True)


def untax_rrule_in_nasts_mandatory(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]

    for week, day, hour in all_dates:
        cnt = np.sum(nast_occupied[week, day, hour:(hour + rasp.duration)]>1)
        nast_occupied[week, day, hour:(hour + rasp.duration)] -= 1
        if cnt:
            punish = -cnt*30
            update_grades_nasts(state, sem_id, punish, plus=False)


def untax_rrule_in_nasts_optional(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    optionals_occupied = state.mutable_constraints.optionals_occupied[sem_id]

    for week, day, hour in all_dates:
        optionals_occupied[week, day, hour:(hour + rasp.duration)] -= 1
    for week, day, hour in all_dates:
        cnt = 0
        for hr in range(hour, hour + rasp.duration):
            if optionals_occupied[week, day, hr] == 0.0:
                nast_occupied[week, day, hr] -= 1
                if nast_occupied[week, day, hr]>=1:
                    cnt += 1
        if cnt:
            punish = -cnt*30
            update_grades_nasts(state, sem_id, punish, plus=False)


def tax_rrule_in_nasts_optional(state, sem_id, rasp):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    optional_occupied = state.mutable_constraints.optionals_occupied[sem_id]

    for week, day, hour in all_dates:
        cnt = 0
        for hr in range(hour, hour + rasp.duration):
            if optional_occupied[week, day, hr] == 0.0:
                nast_occupied[week, day, hr] += 1
                if nast_occupied[week, day, hr]>1:
                    cnt += 1
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
