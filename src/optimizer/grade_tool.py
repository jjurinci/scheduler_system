import numpy as np

def is_computer_problematic(rasp, room_id, computer_rooms):
    return (not room_id in computer_rooms and rasp.needs_computers) or \
           (room_id in computer_rooms and not rasp.needs_computers)


def is_capacity_problematic(rasp, room_id, students_estimate, room_capacity):
    return students_estimate[rasp.id] - room_capacity[room_id] >= 0


def is_room_problematic(rasp, room_id, slot, rooms_occupied):
    week, day, hour = slot
    return np.any(rooms_occupied[room_id][week, day, hour:(hour+rasp.duration)]>1)


def is_prof_problematic(rasp, slot, profs_occupied):
    week, day, hour = slot
    return np.any(profs_occupied[rasp.professor_id][week, day, hour:(hour+rasp.duration)]>1)


def is_nast_problematic(rasp, slot, nasts_occupied, optionals_occupied):
    week, day, hour = slot
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids

    for sem_id in sem_ids:
        if np.any(nasts_occupied[sem_id][week, day, hour:(hour+rasp.duration)]>1):
            return True
    return False


def is_rasp_problematic(rasp, all_dates, room_id, rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, computer_rooms, room_capacity, students_estimate):
    if is_computer_problematic(rasp, room_id, computer_rooms) or \
       is_capacity_problematic(rasp, room_id, students_estimate, room_capacity):
           return True

    for week, day, hour in all_dates:
        slot = (week, day, hour)
        if is_room_problematic(rasp, room_id, slot, rooms_occupied) or \
           is_prof_problematic(rasp, slot, profs_occupied) or \
           is_nast_problematic(rasp, slot, nasts_occupied, optionals_occupied):
               return True
    return False


#Sum variation
def computer_grade(rasp, room_id, computer_rooms):
    strong_computer = -30 * bool(not room_id in computer_rooms and rasp.needs_computers)
    weak_computer   = -3  * bool(room_id in computer_rooms and not rasp.needs_computers)
    return strong_computer + weak_computer


def capacity_grade(rasp, room_id, students_estimate, room_capacity):
    return -30 * (students_estimate[rasp.id] - room_capacity[room_id] >= 0)


def room_grade(rasp, room_id, slot, rooms_occupied):
    week, day, hour = slot
    return -30 * np.sum(rooms_occupied[room_id][week, day, hour:(hour+rasp.duration)]>1)


def prof_grade(rasp, slot, profs_occupied):
    week, day, hour = slot
    return -30 * np.sum(profs_occupied[rasp.professor_id][week, day, hour:(hour+rasp.duration)]>1)


def nast_grade(rasp, slot, nasts_occupied, optionals_occupied):
    week, day, hour = slot
    sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids

    cnt = 0
    for sem_id in sem_ids:
        rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
        if rasp_mandatory:
            cnt += np.sum(nasts_occupied[sem_id][week, day, hour:(hour+rasp.duration)]>1)
        else:
            # If we were to untax such an optional rasp, it would improve the score
            for hr in range(hour, hour + rasp.duration):
                is_only_optional = optionals_occupied[sem_id][week,day,hr]-1 == 0
                has_collision    = nasts_occupied[sem_id][week,day,hr] > 1
                if is_only_optional and has_collision:
                    cnt += 1
    return -30 * cnt


def rasp_grade(rasp, all_dates, room_id, rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, computer_rooms, room_capacity, students_estimate):
    grade_obj = {"totalScore": 0, "roomScore": 0, "professorScore": 0,
                 "capacityScore": 0, "computerScore": 0, "nastScore": 0}

    grade_obj["capacityScore"] += capacity_grade(rasp, room_id, students_estimate, room_capacity)
    grade_obj["computerScore"] += computer_grade(rasp, room_id, computer_rooms)
    for week, day, hour in all_dates:
        slot = (week, day, hour)
        grade_obj["roomScore"] += room_grade(rasp, room_id, slot, rooms_occupied)
        grade_obj["professorScore"] += prof_grade(rasp, slot, profs_occupied)
        grade_obj["nastScore"] += nast_grade(rasp, slot, nasts_occupied, optionals_occupied)

    grade_obj["totalScore"] = sum(grade_obj.values())
    return grade_obj
