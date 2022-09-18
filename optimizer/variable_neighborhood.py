import time
import random
from tqdm import tqdm
import optimizer.grade_tool   as grade_tool
import optimizer.tax_tool     as tax_tool
import optimizer.local_search as local_search
import optimizer.rasp_slots   as rasp_slots
from utilities.my_types import State


def run(state, CPU_TIME_SEC, start_time):
    neighbor_k, k_max = 1,2
    best_grade, best_state = state.grade.copy(), state

    while neighbor_k <= k_max:
        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            break

        shake(state, neighbor_k)
        variable_neighborhood_descent(state, CPU_TIME_SEC, start_time)

        improvement = state.grade["totalScore"] > best_grade["totalScore"]
        if improvement:
            neighbor_k = 1
            best_grade = state.grade.copy()
            best_state = state
            tqdm.write(f"{round(elapsed_time,2)}, {neighbor_k=}, {best_grade}")
        else:
            neighbor_k += 1

        perfect_grade = state.grade["totalScore"] == 0
        if perfect_grade:
            break

    state = best_state


"""
neighbor_k = 1
- Pick a random rasp and pick a random slot for it
neighbor_k = 2
- Pick 2 random rasps (1 problematic) and swap their slots

Theory idea: Intensify/Deintensify the shaking.
"""
def shake(state, neighbor_k):
    timetable = state.timetable
    print(f"Shaking {neighbor_k}")

    if neighbor_k == 1:
        rasp0 = random.choice(list(timetable.keys()))
        tax_tool.untax_old_slot(state, rasp0, timetable[rasp0])
        rnd_slot = random.choice(list(rasp_slots.get_rasp_slots(state, rasp0)))
        tax_tool.tax_new_slot(state, rasp0, rnd_slot)
    elif neighbor_k == 2:
        rasp0, rasp1 = grade_tool.problematic_rasp_pair(state, set(), set())

        if not rasp0 or not rasp1:
            return

        old_rasp0_slot, old_rasp1_slot = timetable[rasp0], timetable[rasp1]
        new_rasp0_slot, new_rasp1_slot = old_rasp1_slot, old_rasp0_slot

        tax_tool.untax_old_slot(state, rasp0, old_rasp0_slot)
        tax_tool.tax_new_slot(state, rasp0, new_rasp0_slot)
        tax_tool.untax_old_slot(state, rasp1, old_rasp1_slot)
        tax_tool.tax_new_slot(state, rasp1, new_rasp1_slot)


def variable_neighborhood_descent(state: State, CPU_TIME_SEC, start_time):
    neighbor_l, l_max = 1, 2

    improvement = True
    while neighbor_l <= l_max:
        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            break

        if neighbor_l == 1:
            improvement = vnd_neighborhood_1(state)
        if neighbor_l == 2:
            improvement = vnd_neighborhood_2(state)

        if improvement:
            tqdm.write(f"{round(elapsed_time, 2)}, {neighbor_l}, {state.grade}")

        neighbor_l = 1 if improvement else neighbor_l+1


def vnd_neighborhood_1(state):
    timetable = state.timetable
    searched_entire_neighborhood, improvement = False, False
    tabu_list1 = set()

    while not searched_entire_neighborhood:
        # Define a neighborhood (random problematic rasp)
        rasp0 = grade_tool.random_problematic_rasp(state, tabu_list1)

        # Local optimum reached (no more improving neighbors)
        if not rasp0:
            improvement = False
            break

        else:
            # Untax rasp0's old slot from memory & calculate grade
            old_slot = timetable[rasp0]
            only_old_slot_grade = tax_tool.untax_old_slot(state, rasp0, old_slot)

            # Choose descent (finding best neighbor)
            new_slot = local_search.first_better_slot(state, rasp0, only_old_slot_grade)
            improvement = True if new_slot else False

            # Update tabu list
            update_tabu_list1(tabu_list1, rasp0, new_slot)

            # Tax the chosen slot
            new_slot = new_slot if new_slot else old_slot
            tax_tool.tax_new_slot(state, rasp0, new_slot)

            if improvement:
                break

    return improvement


def vnd_neighborhood_2(state):
    # At this point we know that no rasp succeeded with l=1 strategy
    # Therefore we pick 1 problematic rasp, and 1 OTHER rasp (problematic or not)
    # and try to put rasp0 to rasp1's all_dates and rasp1 to some of it's other dates

    searched_entire_neighborhood, improvement = False, False
    tabu_list1, tabu_list2 = set(), dict()

    while not searched_entire_neighborhood:
        rasp0, rasp1 = grade_tool.problematic_rasp_pair(state, tabu_list1, tabu_list2)

        # Local optimum reached (no more improving neighbors)
        if not rasp0 and not rasp1:
            improvement = False
            break

        # If no matching element for rasp0 was found, blacklist rasp0.
        elif rasp0 and not rasp1:
            tabu_list1.add(rasp0.id)
            continue

        # Try to improve the score by placing rasp0 to rasp1's slot and rasp1 to any of its other slots.
        got_better_score = swap_pairs(state, rasp0, rasp1)

        # If score wasn't improved, blacklist rasp1 as a swapping partner for rasp0.
        if not got_better_score:
            if rasp0.id not in tabu_list2:
                tabu_list2[rasp0.id] = set()
            tabu_list2[rasp0.id].add(rasp1.id)

        else:
            improvement = True
            break

    return improvement


def swap_pairs(state, rasp0, rasp1):
    timetable = state.timetable
    old_total_grade = state.grade.copy()

    rasp0_old_slot, rasp1_old_slot = timetable[rasp0], timetable[rasp1]

    # Remove rasp0 from its slot, remove rasp1 from its slot. Place rasp0 into rasp1's slot.
    tax_tool.untax_old_slot(state, rasp0, rasp0_old_slot)
    tax_tool.tax_new_slot(state, rasp0, rasp1_old_slot)
    tax_tool.untax_old_slot(state, rasp1, rasp1_old_slot)

    # If the score worsened just by moving rasp0 to rasp1's slot then set
    # rasp0 and rasp1 back to their original slots and return. Keep in mind
    # that rasp1 isn't even taxed at this point.
    if state.grade["totalScore"] <= old_total_grade["totalScore"]:
        tax_tool.tax_new_slot(state, rasp1, rasp1_old_slot)
        tax_tool.untax_old_slot(state, rasp0, rasp1_old_slot)
        tax_tool.tax_new_slot(state, rasp0, rasp0_old_slot)
        return False

    # Grade without rasp1 taxed.
    untaxed_rasp1_grade = state.grade.copy()

    # Grade that rasp1 at new slot has to beat.
    difference_grade = {k:old_total_grade[k] - untaxed_rasp1_grade[k] for k in old_total_grade}

    # Finding a slot for rasp1 that beats difference_grade.
    chosen_slot = local_search.first_better_slot(state, rasp1, difference_grade)

    # If slot is found, then tax it.
    if chosen_slot:
        tax_tool.tax_new_slot(state, rasp1, chosen_slot)

    # Otherwise set rasp0 and rasp1 back to their original slots.
    else:
        tax_tool.tax_new_slot(state, rasp1, rasp1_old_slot)
        tax_tool.untax_old_slot(state, rasp0, rasp1_old_slot)
        tax_tool.tax_new_slot(state, rasp0, rasp0_old_slot)

    return True if chosen_slot else False


def update_tabu_list1(tabu_list, rasp0, new_slot):
    tabu_list.clear() if new_slot else tabu_list.add(rasp0.id)

