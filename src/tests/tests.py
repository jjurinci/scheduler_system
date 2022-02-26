import pickle
import numpy as np
import data_api.time_structure as time_api
from collections import defaultdict
from dateutil.rrule import rrulestr
from data_api.utilities.get_size import print_size, get_size
from data_api.utilities.my_types import State, MutableConstraints
from optimizer.tax_tool import tax_tool
import optimizer.grade_tool as grade_tool
import data_api.constraints as cons_api
import optimizer.rasp_slots as rasp_slots

path = "saved_timetables/zero_timetable.pickle"

with open(path, "rb") as p:
    state = pickle.load(p)
    print(get_size(state) / 10**6)
    print_size(state)


"""
Tests if timetable constraints was properly graded.
1) Initial constraints are reconstructed
2) Each rasp is freshly taxed on initial constraints
3) New and old constraints are compared to check for differences (no differences are allowed)
"""
def check_grade_is_0(state):
    timetable         = state.timetable
    NUM_WEEKS         = state.time_structure.NUM_WEEKS
    NUM_DAYS          = state.time_structure.NUM_DAYS
    NUM_HOURS         = state.time_structure.NUM_HOURS
    rooms             = state.rooms
    students_per_rasp = state.students_per_rasp
    rasps             = timetable.keys()

    init_rooms_occupied     = {k:v.copy() for k,v in state.initial_constraints.rooms_occupied.items()}
    init_profs_occupied     = {k:v.copy() for k,v in state.initial_constraints.profs_occupied.items()}
    init_nasts_occupied     = {k:v.copy() for k,v in state.initial_constraints.nasts_occupied.items()}
    init_optionals_occupied = {k:v.copy() for k,v in state.initial_constraints.optionals_occupied.items()}

    test_mutable_constraints = MutableConstraints(init_rooms_occupied, init_profs_occupied,
                                                  init_nasts_occupied, init_optionals_occupied)

    test_state = State(state.is_winter, state.semesters, state.time_structure,
                       state.rooms, state.students_per_rasp, state.initial_constraints,
                       test_mutable_constraints, state.timetable, grade_tool.init_grades(rasps, rooms),
                       state.rasp_rrules, state.rrule_space, state.groups, state.subject_types)

    # rasp_rrules[all_dates] is already set to parallel groups so the tax algo will read wrong
    for rasp in timetable:
        test_state.rasp_rrules[rasp.id]["all_dates"] = []

    for rasp, slot in timetable.items():
        rasp_slots.update_rasp_rrules(test_state, slot, rasp)
        tax_tool.tax_all_constraints(test_state, slot, rasp)

    for rasp, slot in timetable.items():
        if rooms[slot.room_id].capacity < students_per_rasp[rasp.id]:
            print(f"{rasp.id} has a capacity problem at {slot}.")
        if not rooms[slot.room_id].has_computers and rasp.needs_computers:
            print(f"{rasp.id} has a strong computer problem at {slot}.")
        if rooms[slot.room_id].has_computers and not rasp.needs_computers:
            print(f"{rasp.id} has a weak computer problem at {slot}.")

    given_rooms_occupied = state.mutable_constraints.rooms_occupied
    calc_rooms_occupied  = test_state.mutable_constraints.rooms_occupied
    for room_id in calc_rooms_occupied:
        for week in range(NUM_WEEKS):
            for day in range(NUM_DAYS):
                for hour in range(NUM_HOURS):
                    if calc_rooms_occupied[room_id][week, day, hour] > 1:
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
                    if calc_profs_occupied[prof_id][week, day, hour] > 1:
                        print(f"PROFS: {prof_id} has a collision problem at ({week}, {day}, {hour}).")
                    if calc_profs_occupied[prof_id][week, day, hour] != given_profs_occupied[prof_id][week, day, hour]:
                        print(f"{prof_id} is not the same in given and calculated 'profs_occupied' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", calc_profs_occupied[prof_id][week, day, hour])
                        print(f"given is: ", given_profs_occupied[prof_id][week, day, hour])

    given_nasts_occupied = state.mutable_constraints.nasts_occupied
    calc_nasts_occupied  = test_state.mutable_constraints.nasts_occupied
    all_sem_ids = set(sem_id for rasp in timetable for sem_id in rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids)
    for sem_id in all_sem_ids:
        for week in range(NUM_WEEKS):
            for day in range(NUM_DAYS):
                for hour in range(NUM_HOURS):
                    if calc_nasts_occupied[sem_id][week, day, hour] > 1:
                        print(f"NASTS: {sem_id} has a collision problem at ({week}, {day}, {hour}).")
                    if calc_nasts_occupied[sem_id][week, day, hour] != given_nasts_occupied[sem_id][week, day, hour]:
                        print(f"{sem_id} is not the same in given and calculated 'nasts_occupied' at {week}, {day}, {hour}).")
                        print(f"calculated is: ", calc_nasts_occupied[sem_id][week, day, hour])
                        print(f"given is: ", given_nasts_occupied[sem_id][week, day, hour])


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
                for hr in range(hour, hour + rasp.duration):
                    if rasp_mandatory and (week, day, hr) not in own_group_dates:
                        mandatory_occupied[sem_id][week, day, hr] += 1
                    elif not rasp_mandatory:
                        optionals_occupied[sem_id][week, day, hr] += 1
                assert all(mandatory_occupied[sem_id][week, day, hour:(hour + rasp.duration)]<=1), f"Mandatory rasps collide at {sem_id}"

    all_sem_ids = set([sem_id for rasp in timetable for sem_id in rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids])
    for sem_id in all_sem_ids:
        for week in range(NUM_WEEKS):
            for day in range(NUM_DAYS):
                for hour in range(NUM_HOURS):
                    mand_val = mandatory_occupied[sem_id][week, day, hour]
                    opti_val = optionals_occupied[sem_id][week, day, hour]
                    assert not (mand_val >= 1 and opti_val >= 1), f"Mandatory and optional rasps collide at {sem_id}"


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

    assert not bads


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
        assert start_slot == all_dates[0]


"""
Tests if rasp's all_dates path are correctly calculated according to rasp's RRULE.
"""
def correct_rrules(state):
    timetable     = state.timetable
    rasp_rrules   = state.rasp_rrules
    hour_to_index = state.time_structure.hour_to_index
    index_to_hour = state.time_structure.index_to_hour
    NUM_HOURS     = state.time_structure.NUM_HOURS

    for rasp, _ in timetable.items():
        rrule = rrulestr(rasp.rrule)

        chosen_dt_week, chosen_dt_day, chosen_dt_hour    = rasp_rrules[rasp.id]["DTSTART"]
        chosen_un_week, chosen_un_day, chosen_un_hour    = rasp_rrules[rasp.id]["UNTIL"]
        correct_dt_week, correct_dt_day, correct_dt_hour = time_api.date_to_index(rrule._dtstart, hour_to_index)

        if rasp.fixed_hour and chosen_dt_hour != correct_dt_hour:
            print(rrule._dtstart)
            print(f"{rasp.id} has fixed hour and {chosen_dt_hour=} != {correct_dt_hour=}")
        else:
            correct_dt_hour = chosen_dt_hour

        # random=1 -> Check if chosen DTSTART falls in the correct random range
        if rasp.random_dtstart_weekday:
            viable_dtstarts = time_api.all_dtstart_weekdays(rrule._dtstart)
            viable_dtstarts = [time_api.date_to_index(dt, hour_to_index) for dt in viable_dtstarts]
            good = False
            for week, day, _ in viable_dtstarts:
                if week == chosen_dt_week and day == chosen_dt_day:
                    good = True
                    break
            if not good:
                print(f"{rasp.id} has {rasp.random_dtstart_weekday=} and {chosen_dt_week=} {chosen_dt_day=} but it's not viable for {correct_dt_week=} {correct_dt_day=}")

        # random=0 -> Enforce DTSTART day
        elif chosen_dt_week != chosen_dt_day or chosen_dt_day != correct_dt_day:
            print(f"{rasp.id} has {rasp.random_dtstart_weekday=} and {chosen_dt_week=} and {correct_dt_week=} and {chosen_dt_day=} and {correct_dt_day=}")

        # At this point: *chosen* DTSTART week,day,hr is correct
        chosen_dt_date = time_api.index_to_date(chosen_dt_week, chosen_dt_day, chosen_dt_hour, index_to_hour, NUM_HOURS)
        chosen_un_date = time_api.index_to_date(chosen_un_week, chosen_un_day, chosen_un_hour, index_to_hour, NUM_HOURS)
        correct_all_dates = time_api.get_rrule_dates(rasp.rrule, chosen_dt_date, chosen_un_date, hour_to_index)
        chosen_all_dates = rasp_rrules[rasp.id]["all_dates"]

        assert len(correct_all_dates) == len(chosen_all_dates)

        for i in range(len(correct_all_dates)):
            assert correct_all_dates[i] == chosen_all_dates[i]


all_rasps_have_dates(state)
all_dates_correct_start(state)
check_grade_is_0(state)
no_mandatory_optional_collisions(state)
no_subject_type_collisions(state)
correct_rrules(state)
