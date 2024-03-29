import random
import data_api.time_structure as time_api
import optimizer.tax_tool as tax_tool
import optimizer.rasp_slots as rasp_slots
from utilities.my_types import Slot
from dateutil.rrule import rrulestr
from movement.move_utilities import any_collisions_in_matrix3D, any_collisions_in_sems
from utilities.general_utilities import load_state


"""
Given a rasp, function prints all available slots where rasp can be moved to.
Available means that there are no rrule collisions of rooms, profs, and semesters.

Function iterates through all rasps and prints their available slots for illustrative
purposes. In practice, user would click on 1 rasp and function would return available
slots just for that rasp.
"""
def analyze_movement(verbose = False, move = False):
    state = load_state()
    timetable = state.timetable

    for rasp, slot in timetable.items():
        other_free_slots = get_other_free_slots(state, rasp, slot.room_id)
        print(rasp.id, rasp.professor_id, other_free_slots, "\n")
        if verbose:
            print(rasp.id, rasp.professor_id, "fixed_hr:", rasp.fixed_hour, "rnd_day:", rasp.random_dtstart_weekday, other_free_slots, "\n")
            print(rasp.professor_id, slot, ":\n", state.mutable_constraints.profs_occupied[rasp.professor_id][slot.week])
            print(slot.room_id, slot.week, ":\n", state.mutable_constraints.rooms_occupied[slot.room_id][slot.week])
            sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
            for sem_id in sem_ids:
                print(sem_id, slot.week, ":\n", state.mutable_constraints.sems_collisions[sem_id][slot.week])

        if move:
            dt_week, dt_day, dt_hour = random.choice(other_free_slots)
            new_slot = Slot(slot.room_id, dt_week, dt_day, dt_hour)
            old_slot = slot

            tax_tool.untax_all_constraints(state, old_slot, rasp)
            rasp_slots.update_rasp_rrules(state, new_slot, rasp)
            tax_tool.tax_all_constraints(state, new_slot, rasp)


"""
Function returns other free slots where rasp can be moved to (without collisions).
It does this by finding the intersection of room, prof, and semester free times
that are enough to fit rasp.duration.
Finding room and prof free times is straightforward -> either there is 0=free or 1=occupied.
Semester free times are more complicated because 1=occupied could still be
free if it's occupied by parallel group or by parallel optional (in case optional
rasp is being moved). The function does take proper care of that, but it's something
to keep in mind.
"""
def get_other_free_slots(state, rasp, room_id):
    rooms_occupied = state.mutable_constraints.rooms_occupied
    profs_occupied = state.mutable_constraints.profs_occupied
    NUM_DAYS = state.time_structure.NUM_DAYS
    NUM_HOURS = state.time_structure.NUM_HOURS
    all_dates = state.rasp_rrules[rasp.id]["all_dates"]
    time_structure = state.time_structure

    dt_week, dt_day, dt_hour = all_dates[0]
    until = rrulestr(rasp.rrule)._until
    un_week, un_day, _ = time_api.date_to_index(until, time_structure)
    intersection = []

    days  = list(range(NUM_DAYS))  if not rasp.random_dtstart_weekday else [dt_day]
    hours = list(range(NUM_HOURS)) if rasp.fixed_hour == None else [rasp.fixed_hour]
    hours = [hour for hour in hours if hour + rasp.duration < NUM_HOURS]
    for day in days:
        for hour in hours:
            NEW_DTSTART = time_api.index_to_date(dt_week, day, hour, time_structure)
            NEW_UNTIL   = time_api.index_to_date(un_week, un_day, hour, time_structure)
            new_all_dates = time_api.get_rrule_dates(rasp.rrule, NEW_DTSTART, NEW_UNTIL, time_structure)

            room_problem = any_collisions_in_matrix3D(rasp, new_all_dates, rooms_occupied[room_id])
            if room_problem:
                continue
            prof_problem = any_collisions_in_matrix3D(rasp, new_all_dates, profs_occupied[rasp.professor_id])
            if prof_problem:
                continue
            sem_problem = any_collisions_in_sems(state, rasp, new_all_dates)
            if sem_problem:
                continue

            intersection.append((dt_week, day, hour))

    return intersection


analyze_movement()
