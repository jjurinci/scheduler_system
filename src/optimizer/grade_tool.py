import numpy as np
import data_api.constraints as cons_api

def is_weak_computer_problematic(state, rasp, room_id):
    rooms = state.rooms
    return rooms[room_id].has_computers and not rasp.needs_computers


def is_strong_computer_problematic(state, rasp, room_id):
    rooms = state.rooms
    return not rooms[room_id].has_computers and rasp.needs_computers


def is_computer_problematic(state, rasp, room_id):
    return is_strong_computer_problematic(state, rasp, room_id) or \
           is_weak_computer_problematic(state, rasp, room_id)


def is_capacity_problematic(state, rasp, room_id):
    rooms = state.rooms
    students_per_rasp = state.students_per_rasp
    return students_per_rasp[rasp.id] - rooms[room_id].capacity > 0


def is_room_problematic(state, rasp, room_id, slot):
    rooms_occupied = state.mutable_constraints.rooms_occupied
    week, day, hour = slot
    return np.any(rooms_occupied[room_id][week, day, hour:(hour+rasp.duration)]>1)


def is_prof_problematic(state, rasp, slot):
    profs_occupied = state.mutable_constraints.profs_occupied
    week, day, hour = slot
    return np.any(profs_occupied[rasp.professor_id][week, day, hour:(hour+rasp.duration)]>1)


def is_nast_problematic(state, rasp, slot):
    nasts_occupied = state.mutable_constraints.nasts_occupied
    week, day, hour = slot
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids

    for sem_id in sem_ids:
        if np.any(nasts_occupied[sem_id][week, day, hour:(hour+rasp.duration)]>1):
            return True
    return False


def is_rasp_problematic(state, rasp, room_id):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]

    if is_computer_problematic(state, rasp, room_id) or \
       is_capacity_problematic(state, rasp, room_id):
           return True

    for week, day, hour in all_dates:
        slot = (week, day, hour)
        if is_room_problematic(state, rasp, room_id, slot) or \
           is_prof_problematic(state, rasp, slot) or \
           is_nast_problematic(state, rasp, slot):
               return True
    return False


def init_grades(rasps, rooms):
    all_sem_ids = set()
    for rasp in rasps:
        rasp_sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in rasp_sem_ids:
            all_sem_ids.add(sem_id)

    grade_obj   = {"totalScore": 0, "roomScore": 0, "professorScore": 0, "capacityScore": 0, "computerScore": 0, "nastScore": 0}
    grade_rooms = {"roomScore": 0, "capacityScore": 0, "computerScore": 0}
    grades = {"rooms": {room_id:grade_rooms.copy() for room_id in rooms},
              "profs": {rasp.professor_id:0 for rasp in rasps},
              "nasts": {sem_id:0 for sem_id in all_sem_ids},
              "all": grade_obj.copy()}
    return grades


def count_all_constraints(state, slot, rasp):
    room_occupied     = state.mutable_constraints.rooms_occupied[slot.room_id]
    prof_occupied     = state.mutable_constraints.profs_occupied[rasp.professor_id]

    grade_obj                   = {"totalScore": 0, "roomScore": 0, "professorScore": 0, "capacityScore": 0, "computerScore": 0, "nastScore": 0}
    grade_obj["roomScore"]      = count_rrule_in_matrix3D(state, rasp, room_occupied)
    grade_obj["professorScore"] = count_rrule_in_matrix3D(state, rasp, prof_occupied)
    grade_obj["nastScore"]      = count_rrule_in_nasts(state, rasp)
    grade_obj["capacityScore"]  = -30 * is_capacity_problematic(state, rasp, slot.room_id)
    grade_obj["computerScore"]  = -30 * is_strong_computer_problematic(state, rasp, slot.room_id) + \
                                  (-3 * is_weak_computer_problematic(state, rasp, slot.room_id))
    grade_obj["totalScore"]     = sum(grade_obj.values())
    return grade_obj


def count_rrule_in_matrix3D(state, rasp, matrix3D):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    return -30 * sum(np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]+1 > 1)
                 for week,day,hour in all_dates)


def count_rrule_in_mandatory_rasp(state, rasp, nast_occupied):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)

    cnt = 0
    for week, day, hour in all_dates:
        for hr in range(hour, hour + rasp.duration):
            if (week, day, hr) not in own_group_dates:
                cnt += np.sum(nast_occupied[week, day, hr]+1 > 1)
    return cnt * -30


def count_rrule_in_optional_rasp(state, rasp, sem_id):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    nast_occupied = state.mutable_constraints.nasts_occupied[sem_id]
    optional_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)

    cnt = 0
    for week, day, hour in all_dates:
        for hr in range(hour, hour + rasp.duration):
            if optional_occupied[week, day, hr] == 0 or (week, day, hr) in other_groups_dates:
                cnt += np.sum(nast_occupied[week, day, hr] + 1 >1)
    return cnt * -30


def count_rrule_in_nasts(state, rasp):
    nasts_occupied = state.mutable_constraints.nasts_occupied
    semesters = state.semesters

    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    grade = 0
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        parallel_optionals = True if semesters[sem_id].has_optional_subjects == 1 else False
        if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
            grade += count_rrule_in_mandatory_rasp(state, rasp, nasts_occupied[sem_id])
        elif not rasp_mandatory and parallel_optionals:
            grade += count_rrule_in_optional_rasp(state, rasp, sem_id)
    return grade
