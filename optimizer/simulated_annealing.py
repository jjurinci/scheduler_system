import time
import math
import random
from tqdm import tqdm
import optimizer.grade_tool as grade_tool
import optimizer.tax_tool   as tax_tool
import optimizer.rasp_slots as rasp_slots
import optimizer.why_fail   as why_fail
from utilities.my_types import State


"""
Loop where each iteration is an attempt to optimize the timetable grade.
"""
def run(state, temperature, CPU_TIME_SEC, start_time):
    print(0, state.grade)

    iteration = 0
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            break

        temp = temperature / (iteration+1)
        local_optima = next_neighbor(state, temp, CPU_TIME_SEC, start_time)

        if state.grade["totalScore"] == 0:
            print("Found 0 score solution.")
            return

        elif local_optima:
            print("No 0 score solution.")
            return

        iteration += 1


def next_neighbor(state: State, temperature, CPU_TIME_SEC, start_time):
    timetable   = state.timetable

    searched_entire_neighborhood, local_optima = False, False
    tabu_list = set()

    old_total = state.grade["totalScore"]
    while not searched_entire_neighborhood:
        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            break

        # Define a neighborhood (random problematic rasp)
        rasp0 = grade_tool.random_problematic_rasp(state, tabu_list)

        # Local optimum reached (no more improving neighbors)
        if not rasp0:
            local_optima = True
            break

        # Untax rasp0's old slot from memory & calculate grade
        old_slot = timetable[rasp0]
        only_old_slot_grade = tax_tool.untax_old_slot(state, rasp0, old_slot)

        # Choose descent
        new_slot = annealing_descent(state, rasp0, only_old_slot_grade, temperature)

        # Update tabu list
        update_tabu_list(tabu_list, rasp0, new_slot)

        # Tax the chosen slot
        new_slot = new_slot if new_slot else old_slot
        tax_tool.tax_new_slot(state, rasp0, new_slot)

        new_total = state.grade["totalScore"]
        improvement = True if new_total > old_total else False

        if improvement:
            tqdm.write(f"{round(elapsed_time, 2)}, {round(temperature, 1)}, {state.grade}")
            break

    return local_optima


def annealing_descent(state, rasp0, only_old_slot_grade, temperature):
    action = why_fail.init_action()
    pool_list = list(rasp_slots.get_rasp_slots(state, rasp0))
    random.shuffle(pool_list)
    for new_slot in pool_list:
        if why_fail.is_skippable(new_slot, action):
            continue

        rasp_slots.update_rasp_rrules(state, new_slot, rasp0)

        # Calculate collisions if rasp0 would be on new slot
        only_new_slot_grade = grade_tool.count_all_collisions(state, new_slot, rasp0)
        old = only_old_slot_grade["totalScore"]
        new = only_new_slot_grade["totalScore"]

        if P(old, new, temperature) >= random.random():
            return new_slot
        else:
            why_fail.failure_reason(action, new_slot, only_new_slot_grade, only_old_slot_grade)

    return None


def P(old, new, temperature):
    old, new = abs(old), abs(new)
    return 1.0 if new < old else math.exp((old-new) / temperature)


def update_tabu_list(tabu_list, rasp0, new_slot):
    tabu_list.clear() if new_slot else tabu_list.add(rasp0.id)

