import numpy as np
import data_api.constraints as cons_api


"""
Returns True if entire new_all_dates path has no collisions in given 3D matrix.
"""
def any_collisions_in_matrix3D(rasp, new_all_dates, matrix3D):
    return any(np.any(matrix3D[week, day, hour:(hour + rasp.duration)]>0)
               for week,day,hour in new_all_dates)


"""
Returns True if entire new_all_dates path has no collisions in sem_collisions.
Only activated when rasp is mandatory in given semester.
"""
def any_collisions_in_mandatory_rasp(state, new_all_dates, rasp, sem_id):
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    sem_collisions  = state.mutable_constraints.sems_collisions[sem_id]

    for week, day, hour in new_all_dates:
        for hr in range(hour, hour + rasp.duration):
            if (week, day, hr) not in own_group_dates and sem_collisions[week, day, hr] > 0:
                return True
            elif (week, day, hr) in own_group_dates and sem_collisions[week, day, hr] > 1:
                return True
    return False


"""
Returns True if entire new_all_dates path has no collisions in sem_collisions.
Only activated when rasp is optional in given semester.
"""
def any_collisions_in_optional_rasp(state, new_all_dates, rasp, sem_id):
    sem_collisions = state.mutable_constraints.sems_collisions[sem_id]
    optional_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)

    for week, day, hour in new_all_dates:
        for hr in range(hour, hour + rasp.duration):
            if not (week, day, hr) in own_group_dates and (optional_occupied[week, day, hr] == 0 or (week, day, hr) in other_groups_dates) \
               and sem_collisions[week, day, hr] > 0:
                    return True
            elif sem_collisions[week, day, hr] > 1:
                return True
    return False


"""
Returns True if entire new_all_dates path has no collisions in sems_collisions.
It checks all semesters of a rasp.
"""
def any_collisions_in_sems(state, rasp, new_all_dates):
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    collision = False
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        if rasp_mandatory:
            collision = any_collisions_in_mandatory_rasp(state, new_all_dates, rasp, sem_id)
        else:
            collision = any_collisions_in_optional_rasp(state, new_all_dates, rasp, sem_id)
        if collision:
            return True
    return False
