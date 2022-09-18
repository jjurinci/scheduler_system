import time
import random
from tqdm import tqdm
import optimizer.grade_tool   as grade_tool
import optimizer.tax_tool     as tax_tool
import optimizer.rasp_slots   as rasp_slots
import optimizer.why_fail     as why_fail
from utilities.my_types import State


"""
Loop where each iteration is an attempt to optimize the timetable grade.
"""
def run(state, CPU_TIME_SEC, start_time):
    print("Starting local search.")
    print(0, state.grade)

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            break

        found_better = find_better_neighbor(state, CPU_TIME_SEC, start_time)

        if state.grade["totalScore"] == 0:
            print("Found 0 score solution.")
            break
        elif not found_better:
            print("No 0 score solution.")
            break


"""
Solution improvement function:
    1) Randomly picks a problematic rasp (caled rasp0).
       Problematic rasp has at least one of the following:
       room, prof, semester, capacity, or computer collisions.
    2) rasp0's current slot is untaxed from the grade.
    3) List of new slots is generated according to rasp's rrule and then randomly shuffled
    4) Iteration takes 1 by 1 slot and simulates taxing it
    5) If better score was achieved (or equal score in 1 special case) then
       that slot is chosen and loop breaks. Otherwise loop continues.
    6) In case of new slot's failure to improve score, knowledge is extracted
       why that slot failed -> similar slots are skipped in the future.
    7) In case new slow was successfuly chosen, it is then taxed.
    8) Function returns True if the algorithm converged, False otherwise.
       "Converged" means that either all rasps have been scheduled with no collisions,
       OR rasps have been scheduled with collisions but no further improvement could be found.
"""
def find_better_neighbor(state: State, CPU_TIME_SEC, start_time):
    timetable   = state.timetable

    searched_entire_neighborhood, improvement = False, False
    tabu_list = set()

    while not searched_entire_neighborhood:
        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            break

        # Define a neighborhood (random problematic rasp)
        rasp0 = grade_tool.random_problematic_rasp(state, tabu_list)

        # Local optimum reached (no more improving neighbors)
        if not rasp0:
            improvement = False
            break

        else:
            # Untax rasp0's old slot from memory & calculate grade
            old_slot = timetable[rasp0]
            only_old_slot_grade = tax_tool.untax_old_slot(state, rasp0, old_slot)

            # Choose descent
            new_slot  = first_better_slot(state, rasp0, only_old_slot_grade)
            #new_slot = steepest_better_slot(state, rasp0, only_old_slot_grade)

            improvement = True if new_slot else False

            # Update tabu list
            update_tabu_list(tabu_list, rasp0, new_slot)

            # Tax the chosen slot
            new_slot = new_slot if new_slot else old_slot
            tax_tool.tax_new_slot(state, rasp0, new_slot)

            if improvement:
                tqdm.write(f"{round(elapsed_time, 2)}, {state.grade}")
                break

    return improvement


def first_better_slot(state, rasp0, only_old_slot_grade):
    action = why_fail.init_action()
    pool_list = list(rasp_slots.get_rasp_slots(state, rasp0))
    random.shuffle(pool_list)
    for new_slot in pool_list:
        if why_fail.is_skippable(new_slot, action):
            continue

        rasp_slots.update_rasp_rrules(state, new_slot, rasp0)

        # Calculate collisions if rasp0 would be on new slot
        only_new_slot_grade = grade_tool.count_all_collisions(state, new_slot, rasp0)
        got_better_score = only_new_slot_grade["totalScore"] > only_old_slot_grade["totalScore"]

        if got_better_score:
            return new_slot
        else:
            why_fail.failure_reason(action, new_slot, only_new_slot_grade, only_old_slot_grade)

    return None


def steepest_better_slot(state, rasp0, only_old_slot_grade):
    best_slot, best_grade = None, only_old_slot_grade.copy()
    action = why_fail.init_action()
    pool_list = list(rasp_slots.get_rasp_slots(state, rasp0))
    for new_slot in pool_list:
        if why_fail.is_skippable(new_slot, action):
            continue

        rasp_slots.update_rasp_rrules(state, new_slot, rasp0)

        # Calculate collisions if rasp0 would be on new slot
        only_new_slot_grade = grade_tool.count_all_collisions(state, new_slot, rasp0)
        got_better_score = only_new_slot_grade["totalScore"] > best_grade["totalScore"]

        if got_better_score:
            best_slot, best_grade = new_slot, only_new_slot_grade
            if best_grade["totalScore"] == 0:
                break
        else:
            why_fail.failure_reason(action, new_slot, only_new_slot_grade, only_old_slot_grade)

    return best_slot


def update_tabu_list(tabu_list, rasp0, new_slot):
    tabu_list.clear() if new_slot else tabu_list.add(rasp0.id)

