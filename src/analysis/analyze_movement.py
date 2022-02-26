import pickle
import random
import data_api.time_structure as time_api
import optimizer.any_collisions as any_cols
import optimizer.tax_tool.tax_tool as tax_tool
import optimizer.rasp_slots as rasp_slots
from data_api.utilities.my_types import Slot
from dateutil.rrule import rrulestr

"""
Returns complete state from a .pickle file.
"""
def load_state():
    name = "saved_timetables/zero_timetable.pickle"
    with open(name, "rb") as f:
        state = pickle.load(f)
    return state


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
                print(sem_id, slot.week, ":\n", state.mutable_constraints.nasts_occupied[sem_id][slot.week])

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
Semester (nast) free times are more complicated because 1=occupied could still be
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
    hour_to_index = state.time_structure.hour_to_index
    index_to_hour = state.time_structure.index_to_hour

    dt_week, dt_day, dt_hour = all_dates[0]
    until = rrulestr(rasp.rrule)._until
    un_week, un_day, _ = time_api.date_to_index(until, hour_to_index)
    intersection = []

    days  = list(range(NUM_DAYS))  if not rasp.random_dtstart_weekday else [dt_day]
    hours = list(range(NUM_HOURS)) if not rasp.fixed_hour else [dt_hour]
    hours = [hour for hour in hours if hour + rasp.duration < NUM_HOURS]
    for day in days:
        for hour in hours:
            NEW_DTSTART = time_api.index_to_date(dt_week, day, hour, index_to_hour, NUM_HOURS)
            NEW_UNTIL   = time_api.index_to_date(un_week, un_day, hour, index_to_hour, NUM_HOURS)
            new_all_dates = time_api.get_rrule_dates(rasp.rrule, NEW_DTSTART, NEW_UNTIL, hour_to_index)

            room_problem = any_cols.any_collisions_in_matrix3D(rasp, new_all_dates, rooms_occupied[room_id])
            if room_problem:
                continue
            prof_problem = any_cols.any_collisions_in_matrix3D(rasp, new_all_dates, profs_occupied[rasp.professor_id])
            if prof_problem:
                continue
            nast_problem = any_cols.any_collisions_in_nasts(state, rasp, new_all_dates)
            if nast_problem:
                continue

            intersection.append((dt_week, day, hour))

    return intersection


#analyze_movement()
