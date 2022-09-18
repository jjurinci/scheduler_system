import numpy as np
import data_api.time_structure as time_api
from collections import defaultdict
from dateutil.rrule import rrulestr
from utilities.general_utilities import load_state, print_size
from utilities.my_types import State, MutableConstraints
from optimizer import tax_tool
import optimizer.grade_tool as grade_tool
import data_api.constraints as cons_api
import optimizer.rasp_slots as rasp_slots

state = load_state()
#print_size(state)

"""
Tests if timetable constraints was properly taxed.
1) Initial constraints are reconstructed
2) Each rasp is freshly taxed on initial constraints
3) New and old constraints are compared to check for differences (no differences are allowed)
"""
def timetable_properly_taxed(state):
    timetable         = state.timetable
    NUM_WEEKS         = state.time_structure.NUM_WEEKS
    NUM_DAYS          = state.time_structure.NUM_DAYS
    NUM_HOURS         = state.time_structure.NUM_HOURS
    rooms             = state.rooms
    students_per_rasp = state.students_per_rasp
    rasps             = timetable.keys()
    room_grade        = state.grade["roomScore"]
    prof_grade        = state.grade["professorScore"]
    sem_grade         = state.grade["semScore"]
    capa_grade        = state.grade["capacityScore"]
    comp_grade        = state.grade["computerScore"]
    total_grade       = state.grade["totalScore"]

    init_rooms_occupied     = {k:v.copy() for k,v in state.initial_constraints.rooms_occupied.items()}
    init_profs_occupied     = {k:v.copy() for k,v in state.initial_constraints.profs_occupied.items()}
    init_sems_occupied      = {k:v.copy() for k,v in state.initial_constraints.sems_occupied.items()}
    init_optionals_occupied = {k:v.copy() for k,v in state.initial_constraints.optionals_occupied.items()}
    init_sems_collisions    = {k:v.copy() for k,v in state.initial_constraints.sems_collisions.items()}

    test_mutable_constraints = MutableConstraints(init_rooms_occupied, init_profs_occupied,
                                                  init_sems_occupied, init_optionals_occupied,
                                                  init_sems_collisions)

    test_state = State(state.is_winter, state.semesters, state.time_structure, state.rasps,
                       state.rooms, state.students_per_rasp, state.initial_constraints,
                       state.groups, state.subject_types,
                       test_mutable_constraints, state.timetable, grade_tool.init_grade(rasps),
                       state.rasp_rrules, state.rrule_table)

    # rasp_rrules[all_dates] is already set to parallel groups so the tax algo will read wrong
    for rasp in timetable:
        test_state.rasp_rrules[rasp.id]["all_dates"] = []

    for rasp, slot in timetable.items():
        rasp_slots.update_rasp_rrules(test_state, slot, rasp)
        tax_tool.tax_all_constraints(test_state, slot, rasp)

    if total_grade != test_state.grade["totalScore"]:
        print("Total grade are not equal.")
        print("Given total grade:", total_grade)
        print("Calculated total grade:", test_state.grade["totalScore"])

    for rasp, slot in timetable.items():
        if capa_grade == 0 and rooms[slot.room_id].capacity < students_per_rasp[rasp.id]:
            print(f"{rasp.id} has a capacity problem at {slot}.")
        if comp_grade == 0 and not rooms[slot.room_id].has_computers and rasp.needs_computers:
            print(f"{rasp.id} has a strong computer problem at {slot}.")
        #if comp_grade == 0 and rooms[slot.room_id].has_computers and not rasp.needs_computers:
        #    print(f"{rasp.id} has a weak computer problem at {slot}.")

    given_rooms_occupied = state.mutable_constraints.rooms_occupied
    calc_rooms_occupied  = test_state.mutable_constraints.rooms_occupied
    for room_id in calc_rooms_occupied:
        for week in range(NUM_WEEKS):
            for day in range(NUM_DAYS):
                for hour in range(NUM_HOURS):
                    if room_grade == 0 and calc_rooms_occupied[room_id][week, day, hour] > 1:
                        print(f"ROOMS: {room_id} has a collision problem at ({week}, {day}, {hour}).")
                    if calc_rooms_occupied[room_id][week, day, hour] != given_rooms_occupied[room_id][week, day, hour]:
                        print(f"{room_id} is not the same in given and calculated 'rooms_occupied' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", calc_rooms_occupied[room_id][week, day, hour])
                        print(f"given is: ", given_rooms_occupied[room_id][week, day, hour])

    given_profs_occupied = state.mutable_constraints.profs_occupied
    calc_profs_occupied  = test_state.mutable_constraints.profs_occupied
    prof_ids = set([rasp.professor_id for rasp in timetable])
    for prof_id in prof_ids:
        for week in range(NUM_WEEKS):
            for day in range(NUM_DAYS):
                for hour in range(NUM_HOURS):
                    if prof_grade == 0 and calc_profs_occupied[prof_id][week, day, hour] > 1:
                        print(f"PROFS: {prof_id} has a collision problem at ({week}, {day}, {hour}).")
                    if calc_profs_occupied[prof_id][week, day, hour] != given_profs_occupied[prof_id][week, day, hour]:
                        print(f"{prof_id} is not the same in given and calculated 'profs_occupied' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", calc_profs_occupied[prof_id][week, day, hour])
                        print(f"given is: ", given_profs_occupied[prof_id][week, day, hour])

    given_sems_collisions = state.mutable_constraints.sems_collisions
    calc_sems_collisions  = test_state.mutable_constraints.sems_collisions
    all_sem_ids = set(sem_id for rasp in timetable for sem_id in rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids)
    for sem_id in all_sem_ids:
        for week in range(NUM_WEEKS):
            for day in range(NUM_DAYS):
                for hour in range(NUM_HOURS):
                    if sem_grade == 0 and calc_sems_collisions[sem_id][week, day, hour] > 1:
                        print(f"SEMS: {sem_id} has a collision problem at ({week}, {day}, {hour}).")
                    if calc_sems_collisions[sem_id][week, day, hour] != given_sems_collisions[sem_id][week, day, hour]:
                        print(f"{sem_id} is not the same in given and calculated 'sems_collisions' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", calc_sems_collisions[sem_id][week, day, hour])
                        print(f"given is: ", given_sems_collisions[sem_id][week, day, hour])

    if sem_grade == 0:
        no_mandatory_optional_collisions(state)
        no_subject_type_collisions(state)


"""
Tests if there are any collisions between mandatory and optional rasps.
Also tests if mandatory rasps collide between themselves.
"""
def no_mandatory_optional_collisions(state):
    timetable   = state.timetable
    rasp_rrules = state.rasp_rrules
    NUM_WEEKS   = state.time_structure.NUM_WEEKS
    NUM_DAYS    = state.time_structure.NUM_DAYS
    NUM_HOURS   = state.time_structure.NUM_HOURS

    mandatory_occupied = defaultdict(lambda: np.zeros(shape=(NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8))
    optionals_occupied = defaultdict(lambda: np.zeros(shape=(NUM_WEEKS, NUM_DAYS, NUM_HOURS), dtype=np.uint8))

    for rasp, _ in timetable.items():
        own_group_dates = cons_api.get_own_groups_all_dates(state, rasp)
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        for sem_id in sem_ids:
            rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
            for week, day, hour in all_dates:
                if rasp_mandatory and (week, day, hour) not in own_group_dates:
                    mandatory_occupied[sem_id][week, day, hour] += 1
                elif not rasp_mandatory:
                    optionals_occupied[sem_id][week, day, hour] += 1

                if not mandatory_occupied[sem_id][week, day, hour]<=1:
                    print(f"Mandatory rasps collide at {sem_id} at {week},{day},{hour}")

    all_sem_ids = set([sem_id for rasp in timetable for sem_id in rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids])
    for sem_id in all_sem_ids:
        for week in range(NUM_WEEKS):
            for day in range(NUM_DAYS):
                for hour in range(NUM_HOURS):
                    mand_val = mandatory_occupied[sem_id][week, day, hour]
                    opti_val = optionals_occupied[sem_id][week, day, hour]
                    if mand_val >= 1 and opti_val >= 1:
                        print(f"Mandatory and optional rasps collide at {sem_id} at {week},{day},{hour}")


"""
Tests if there are subject type collisions (in optional rasps).
E.g. hrmgmtP1 cannot collide with hrmgmtV1 in semesters.
"""
def no_subject_type_collisions(state):
    timetable   = state.timetable
    rasp_rrules = state.rasp_rrules

    rasp_keys = {}
    for rasp in timetable:
        if rasp.subject_id not in rasp_keys:
            rasp_keys[rasp.subject_id] = set()

        key = str(rasp.subject_id) + str(rasp.type)
        rasp_keys[rasp.subject_id].add(key)

    seen = defaultdict(lambda: set())
    for rasp, _ in timetable.items():
        own_key = str(rasp.subject_id) + str(rasp.type)
        all_dates = rasp_rrules[rasp.id]["all_dates"]

        for week, day, hour in all_dates:
            seen[own_key].add((week, day, hour))

    for rasp, _ in timetable.items():
        own_key = str(rasp.subject_id) + str(rasp.type)
        other_keys = rasp_keys[rasp.subject_id]

        all_dates = rasp_rrules[rasp.id]["all_dates"]
        for week, day, hour in all_dates:
            bad = False
            own_slot = (week, day, hour)
            for other_key in other_keys:
                if other_key == own_key:
                    continue
                if own_slot in seen[other_key]:
                    print(f"{rasp.id=} {rasp.subject_id=} {rasp.group=} has a type collision at {week=} {day=} {hour=}.")
                    for other_key in other_keys:
                        print(f"ALL KEYS: {other_key=}")
                    bad = True
            if bad:
                break


"""
Tests if all rasps have RRULE all_dates paths.
"""
def all_rasps_have_dates(state):
    timetable = state.timetable
    rasp_rrules = state.rasp_rrules
    bads = []
    for rasp, _ in timetable.items():
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        if not all_dates:
            bads.append(rasp)
    if bads:
        for rasp in bads:
            print(f"rasp_rrule[{rasp.id}]['all_dates'] is empty.")
            dtstart = rasp_rrules[rasp.id]["DTSTART"]
            until = rasp_rrules[rasp.id]["UNTIL"]
            print(f"{rasp}\n{dtstart}\n{until}\n")


"""
Tests if all rasps Slot(room_id, week, day, hour) are equal to the first date
of all_dates path.
"""
def all_dates_correct_start(state):
    timetable = state.timetable
    rasp_rrules = state.rasp_rrules

    for rasp, (_, week, day, hour) in timetable.items():
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        start_slot = (week, day, hour)
        if not start_slot == all_dates[0]:
            print(f"{rasp.id}\n{start_slot=}\n{all_dates=}")


"""
Tests if rasp's all_dates path are correctly calculated according to rasp's RRULE.
"""
def correct_rrules(state):
    timetable     = state.timetable
    rasp_rrules   = state.rasp_rrules
    rrule_table   = state.rrule_table
    time_structure = state.time_structure

    for rasp, _ in timetable.items():
        rrule = rrulestr(rasp.rrule)

        chosen_dt_week, chosen_dt_day, chosen_dt_hour    = rasp_rrules[rasp.id]["DTSTART"]
        chosen_un_week, chosen_un_day, chosen_un_hour    = rasp_rrules[rasp.id]["UNTIL"]

        correct_all_dates = time_api.get_rrule_dates(rasp.rrule, rrule._dtstart, rrule._until, time_structure)
        correct_dt_week, correct_dt_day, correct_dt_hour = correct_all_dates[0]

        if rasp.fixed_hour != None and chosen_dt_hour != correct_dt_hour:
            print(rrule._dtstart)
            print(f"{rasp.id} has fixed hour and {chosen_dt_hour=} != {correct_dt_hour=}")
        else:
            correct_dt_hour = chosen_dt_hour

        # random=1 -> Check if chosen DTSTART falls in the correct random range
        if rasp.random_dtstart_weekday:
            viable_dtstarts = []
            idx = rasp_rrules[rasp.id]["rrule_table_index"]
            for week, day in rrule_table[idx]:
                viable_dtstarts.append((week, day, -1))

            good = False
            for week, day, _ in viable_dtstarts:
                if week == chosen_dt_week and day == chosen_dt_day:
                    good = True
                    break
            if not good:
                print(f"{rasp.id} has {rasp.random_dtstart_weekday=} and {chosen_dt_week=} {chosen_dt_day=} but it's not viable for {correct_dt_week=} {correct_dt_day=}")

        # random=0 -> Enforce DTSTART day
        elif chosen_dt_week != correct_dt_week or chosen_dt_day != correct_dt_day:
            print(rasp)
            print(f"{rasp.id} has {rasp.random_dtstart_weekday=} and {chosen_dt_week=} and {correct_dt_week=} and {chosen_dt_day=} and {correct_dt_day=}")

        # At this point: *chosen* DTSTART week,day,hr is correct
        chosen_dt_date = time_api.index_to_date(chosen_dt_week, chosen_dt_day, chosen_dt_hour, time_structure)
        chosen_un_date = time_api.index_to_date(chosen_un_week, chosen_un_day, chosen_un_hour, time_structure)
        correct_all_dates_ = time_api.get_rrule_dates(rasp.rrule, chosen_dt_date, chosen_un_date, time_structure)
        correct_all_dates = []
        for week, day, hour in correct_all_dates_:
            for hr in range(hour, hour + rasp.duration):
                correct_all_dates.append((week, day, hr))
        chosen_all_dates = rasp_rrules[rasp.id]["all_dates"]

        if not len(correct_all_dates) == len(chosen_all_dates):
            print(f"correct length: {len(correct_all_dates)} | given length: {len(chosen_all_dates)}")

        for i in range(len(correct_all_dates)):
            if not correct_all_dates[i] == chosen_all_dates[i]:
                print(f"i: {i} | correct_all_dates[i]: {correct_all_dates[i]}) != chosen_all_dates[i]: {chosen_all_dates[i]}")


def all_rasps_in_timetable(state):
    all_rasps          = state.rasps
    rasps_in_timetable = set(rasp.id for rasp in state.timetable.keys())

    for rasp in all_rasps:
        if not rasp.id in rasps_in_timetable:
            print(f"{rasp.id} not in timetable.")


def correct_rooms(state):
    for rasp, slot in state.timetable.items():
        if rasp.fix_at_room_id and slot.room_id != rasp.fix_at_room_id:
            print(f"{rasp.id} has rasp.fix_at_room_id = {rasp.fix_at_room_id} and slot.room_id = {slot.room_id} | NOT EQUAL.")



all_rasps_have_dates(state)
all_dates_correct_start(state)
correct_rrules(state)
correct_rooms(state)
timetable_properly_taxed(state)
all_rasps_in_timetable(state)
