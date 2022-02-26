import numpy as np
import data_api.constraints as cons_api

"""
Returns True if entire new_all_dates path has no collisions in given 3D matrix.
"""
def any_collisions_in_matrix3D(rasp, new_all_dates, matrix3D):
    return any(np.any(matrix3D[week, day, hour:(hour + rasp.duration)]>0)
               for week,day,hour in new_all_dates)


"""
Returns True if entire new_all_dates path has no collisions in nast_occupied.
Only activated when rasp is mandatory in given semester.
"""
def any_collisions_in_mandatory_rasp(state, new_all_dates, rasp, nast_occupied):
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    for week, day, hour in new_all_dates:
        for hr in range(hour, hour + rasp.duration):
            if (week, day, hr) not in own_group_dates and nast_occupied[week, day, hr] > 0:
                return True
            elif (week, day, hr) in own_group_dates and nast_occupied[week, day, hr] > 1:
                return True
    return False


"""
Returns True if entire new_all_dates path has no collisions in nast_occupied.
Only activated when rasp is optional in given semester.
"""
def any_collisions_in_optional_rasp(state, new_all_dates, rasp, sem_id):
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    optional_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)

    for week, day, hour in new_all_dates:
        for hr in range(hour, hour + rasp.duration):
            if optional_occupied[week, day, hr] == 0 or (week, day, hr) in other_groups_dates:
                if nast_occupied[week, day, hr] > 0:
                    return True
            elif nast_occupied[week, day, hr] > 1:
                return True
    return False


"""
Returns True if entire new_all_dates path has no collisions in nasts_occupied.
It checks all semesters of a rasp.
"""
def any_collisions_in_nasts(state, rasp, new_all_dates):
    nasts_occupied = state.mutable_constraints.nasts_occupied
    semesters = state.semesters

    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    collision = False
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        parallel_optionals = True if semesters[sem_id].has_optional_subjects == 1 else False
        if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
            collision = any_collisions_in_mandatory_rasp(state, new_all_dates, rasp, nasts_occupied[sem_id])
        elif not rasp_mandatory and parallel_optionals:
            collision = any_collisions_in_optional_rasp(state, new_all_dates, rasp, sem_id)
        if collision:
            return True
    return False
