import math
import random
import data_api.constraints as cons_api
import optimizer.tax_tool as tax_tool
from optimizer.taxing.tax_sems import sems_tax_punish
import optimizer.rasp_slots as rasp_slots

"""
Returns an empty grade object.
Used for later timetable grading.
"""
def init_grade(rasps):
    all_sem_ids = set()
    for rasp in rasps:
        rasp_sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in rasp_sem_ids:
            all_sem_ids.add(sem_id)

    grade = {"totalScore": 0, "roomScore": 0, "professorScore": 0, "capacityScore": 0, "computerScore": 0, "semScore": 0}
    return grade


"""
Returns True if rasp doesn't need computers but its room has computers.
"""
def is_weak_computer_problematic(state, rasp, room_id):
    rooms = state.rooms
    return rooms[room_id].has_computers and not rasp.needs_computers


"""
Returns True if rasp needs computers but its room doesn't have computers.
"""
def is_strong_computer_problematic(state, rasp, room_id):
    rooms = state.rooms
    return not rooms[room_id].has_computers and rasp.needs_computers


"""
Returns True if rasp has any computer problems.
"""
def is_computer_problematic(state, rasp, room_id):
    return is_strong_computer_problematic(state, rasp, room_id)


"""
Returns True if room capacity is lesser than number of students attending rasp.
"""
def is_capacity_problematic(state, rasp, room_id):
    rooms = state.rooms
    students_per_rasp = state.students_per_rasp
    return students_per_rasp[rasp.id] - rooms[room_id].capacity > 0


"""
Returns True if rasp has any room collisions in its all_dates path.
"""
def is_room_problematic(state, room_id, all_dates):
    rooms_occupied = state.mutable_constraints.rooms_occupied
    return any(rooms_occupied[room_id][week, day, hour]>1 for week, day, hour in all_dates)


"""
Returns True if rasp has any professor collisions in its all_dates path.
"""
def is_prof_problematic(state, rasp, all_dates):
    profs_occupied = state.mutable_constraints.profs_occupied
    return any(profs_occupied[rasp.professor_id][week, day, hour]>1 for week, day, hour in all_dates)


"""
Returns True if rasp has any sem collisions in its all_dates path.
"""
def is_sem_problematic(state, rasp, all_dates):
    sems_collisions = state.mutable_constraints.sems_collisions
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids

    for sem_id in sem_ids:
        if any(sems_collisions[sem_id][week, day, hour]>1 for week, day, hour in all_dates):
            return True
    return False


"""
Returns True if rasp has any of the following:
    - room, prof, or sem collision
    - capacity or computer problem
"""
def is_rasp_problematic(state, rasp, room_id):
    if is_computer_problematic(state, rasp, room_id) or \
       is_capacity_problematic(state, rasp, room_id):
           return True

    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    if is_room_problematic(state, room_id, all_dates) or \
       is_prof_problematic(state, rasp, all_dates) or \
       is_sem_problematic(state, rasp, all_dates):
               return True
    return False



"""
Returns a grade_obj that represents collisions along the rasp's all_dates path
(room, prof, sems), together with capacity and computer collisions.
The function and its subfunctions assume that rasp's all_dates have NOT yet been taxed.
That's why they simulate taxing by adding "+1" to matrix positions.
"""
def count_all_collisions(state, slot, rasp):
    room_occupied = state.mutable_constraints.rooms_occupied[slot.room_id]
    prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id]

    grade_obj                   = {"totalScore": 0, "roomScore": 0, "professorScore": 0, "capacityScore": 0, "computerScore": 0, "semScore": 0}
    grade_obj["roomScore"]      = count_rrule_in_matrix3D(state, rasp, room_occupied)
    grade_obj["professorScore"] = count_rrule_in_matrix3D(state, rasp, prof_occupied)
    grade_obj["semScore"]       = count_rrule_in_sems(state, rasp)
    grade_obj["capacityScore"]  = -30 * is_capacity_problematic(state, rasp, slot.room_id)
    grade_obj["computerScore"]  = -30 * is_strong_computer_problematic(state, rasp, slot.room_id)
    grade_obj["totalScore"]     = sum(grade_obj.values())
    return grade_obj


"""
Returns -30 * number of collisions along the rasp's all_dates path in a given 3D matrix.
"""
def count_rrule_in_matrix3D(state, rasp, matrix3D):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    return -30 * sum(matrix3D[week, day, hour]+1
                     for week,day,hour in all_dates
                     if matrix3D[week, day, hour]+1 > 1)


"""
Returns -30 * number of collisions along the rasp's all_dates path in sem_collisions.
This is only activated if rasp is mandatory in a given semester.
"""
def count_rrule_in_mandatory_rasp(state, rasp, sem_id):
    all_dates       = state.rasp_rrules[rasp.id]["all_dates"]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    sem_occupied    = state.mutable_constraints.sems_occupied[sem_id]
    sem_collisions  = state.mutable_constraints.sems_collisions[sem_id]

    punish = 0
    for week, day, hour in all_dates:
        old_cnt_occ, old_cnt_colls = sem_occupied[week, day, hour], sem_collisions[week, day, hour]
        new_cnt_colls = old_cnt_colls + 1 if (week, day, hour) not in own_group_dates else old_cnt_colls
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls)
    return punish

"""
Returns -30 * number of collisions along the rasp's all_dates path in sem_collisions.
This is only activated if rasp is optional in a given semester.
"""
def count_rrule_in_optional_rasp(state, rasp, sem_id):
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
    other_groups_dates = cons_api.get_other_groups_all_dates(state, rasp)
    sem_occupied    = state.mutable_constraints.sems_occupied[sem_id]
    optional_occupied = state.mutable_constraints.optionals_occupied[sem_id]
    sem_collisions  = state.mutable_constraints.sems_collisions[sem_id]

    punish = 0
    for week, day, hour in all_dates:
        old_cnt_occ, old_cnt_colls = sem_occupied[week, day, hour], sem_collisions[week, day, hour]
        new_cnt_colls = 0
        if not (week, day, hour) in own_group_dates and (optional_occupied[week, day, hour] == 0 or (week, day, hour) in other_groups_dates):
            new_cnt_colls = old_cnt_colls + 1
        else:
            new_cnt_colls = old_cnt_colls
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls)
    return punish


"""
Returns -30 * number of collisions along the rasp's all_dates path in sems_collisions.
Used to calculate semester collisions.
"""
def count_rrule_in_sems(state, rasp):
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
    punish = 0
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        if rasp_mandatory:
            punish += count_rrule_in_mandatory_rasp(state, rasp, sem_id)
        else:
            punish += count_rrule_in_optional_rasp(state, rasp, sem_id)
    return punish


def random_problematic_rasp(state, tabu_list):
    timetable = state.timetable
    rasps = list(timetable.keys())
    random.shuffle(rasps)
    rasp0 = None
    for rasp in rasps:
        if rasp.id in tabu_list:
            continue
        room_id, _, _, _= timetable[rasp]
        if is_rasp_problematic(state, rasp, room_id):
            rasp0 = rasp
            break
    return rasp0


def problematic_rasp_pair(state, tabu_list1, tabu_list2):
    timetable = state.timetable
    rasps = list(timetable.keys())
    random.shuffle(rasps)
    rasp0, rasp1 = None, None

    for rasp in rasps:
        if rasp.id in tabu_list1:
            continue
        room_id, _, _, _= timetable[rasp]
        if is_rasp_problematic(state, rasp, room_id):
            rasp0 = rasp
            break

    if not rasp0:
        return None, None

    for pot_rasp1 in rasps:
        if rasp0.id == pot_rasp1.id or timetable[rasp0] == timetable[pot_rasp1]:
            continue
        if rasp0.id in tabu_list2 and pot_rasp1.id in tabu_list2[rasp0.id]:
            continue
        if not rasp_slots.check_rasps_swap(state, rasp0, pot_rasp1, timetable[rasp0], timetable[pot_rasp1]):
            continue
        rasp1 = pot_rasp1
        break

    return rasp0, rasp1



def most_problematic_rasps(state, percent):
    timetable = state.timetable
    problematic_rasps = []
    for rasp, old_slot in timetable.items():
        if not is_rasp_problematic(state, rasp, old_slot.room_id):
            continue
        only_old_slot_grade = tax_tool.untax_old_slot(state, rasp, old_slot)
        tax_tool.tax_new_slot(state, rasp, old_slot)
        problematic_rasps.append((rasp, only_old_slot_grade["totalScore"]))

    problematic_rasps.sort(key=lambda x:x[1])
    num_keep = math.ceil(len(timetable) * percent)
    problematic_rasps = problematic_rasps[:num_keep]
    problematic_rasps = [ele[0] for ele in problematic_rasps]
    return problematic_rasps

