import random
from tqdm import tqdm
from multiprocessing import Pool
from itertools import repeat
import optimizer.grade_tool as grade_tool
import optimizer.tax_tool   as tax_tool
import optimizer.rasp_slots as rasp_slots
import optimizer.why_fail   as why_fail
from utilities.my_types import State


"""
Fills the timetable with random slots.
Slots are chosen with respect to rasp's rrule, but no measure to prevent collisions
is taken.
"""
def set_random_timetable(state: State):
    timetable = state.timetable

    # Generating a random timetable
    for rasp, _ in timetable.items():
        slot = None
        pool = rasp_slots.get_rasp_slots(state, rasp)
        slot = random.choice(tuple(pool))

        rasp_slots.update_rasp_rrules(state, slot, rasp)
        tax_tool.tax_all_constraints(state, slot, rasp)
        timetable[rasp] = slot


"""
Loop where each iteration is an attempt to optimize the timetable grade.
"""
def iterate(population, iterations=1000):
    population_cap = len(population)
    population.sort(key=lambda x: x[1].grades["all"]["totalScore"], reverse=True)
    BEST_GRADE = population[0][1].grades["all"].copy()
    print(0, BEST_GRADE)

    for generation in tqdm(range(iterations)):
        #with Pool(7) as p:
        #    mutations = p.map_async(find_better_grade, population)
        #    mutations.wait()

        mutations = [find_better_grade(pop) for pop in population]

        population += mutations #mutations.get()
        population.sort(key=lambda x: (x[1].grades["all"]["totalScore"], x[0]), reverse=True)
        population = population[:population_cap]

        calc_grade = population[0][1].grades["all"]
        if calc_grade["totalScore"] > BEST_GRADE["totalScore"]:
            BEST_GRADE = calc_grade.copy()
            tqdm.write(f"{generation}, {BEST_GRADE}")

        if BEST_GRADE["totalScore"] == 0:
            print("Found 0 score solution.")
            break

        elif all(converged for (converged, _) in population):
            print("Didn't find 0 score solution.")
            break

    population = [state for (_, state) in population]
    for state in population:
        state.unsuccessful_rasps.clear()

    return population

"""
Transformation function:
    1) Randomly picks a problematic rasp (caled rasp0).
       Problematic rasp has at least one of the following:
       room, prof, nast, capacity, or computer collisions.
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
def find_better_grade(data):
    _, state = data
    timetable   = state.timetable
    grades      = state.grades

    # Pick a random problematic rasp
    rasps = list(timetable.keys())
    random.shuffle(rasps)
    rasp0 = None
    first_iters, skipped_iters = 0, 0
    for rasp in rasps:
        if rasp.id in state.unsuccessful_rasps:
            skipped_iters += 1
            continue
        first_iters += 1
        room_id, _, _, _= timetable[rasp]
        if grade_tool.is_rasp_problematic(state, rasp, room_id):
            rasp0 = rasp
            break

    if not rasp0:
        return (True, state)

    old_slot = timetable[rasp0]
    old_grade_with_old_slot = grades["all"].copy()
    timetable.pop(rasp0, 0)
    pool = rasp_slots.get_rasp_slots(state, rasp0)

    tax_tool.untax_all_constraints(state, old_slot, rasp0)

    old_grade_without_old_slot = grades["all"].copy()
    pure_old_slot_grade = {k:old_grade_with_old_slot[k] -
                             old_grade_without_old_slot[k]
                           for k in old_grade_with_old_slot}

    need_same_score   = pure_old_slot_grade["totalScore"] == 0
    need_better_score = pure_old_slot_grade["totalScore"] != 0

    action = why_fail.init_action()
    pool_list = list(pool)
    random.shuffle(pool_list)
    the_slot = None
    cnt, skipped = 0, 0
    new_grade_with_new_slot = None

    for new_slot in pool_list:
        if why_fail.is_skippable(state, new_slot, rasp0, action):
            skipped += 1
            continue
        cnt += 1

        rasp_slots.update_rasp_rrules(state, new_slot, rasp0)

        pure_new_slot_grade = grade_tool.count_all_collisions(state, new_slot, rasp0)
        new_grade_with_new_slot = {k:old_grade_without_old_slot[k] + pure_new_slot_grade[k] for k in pure_new_slot_grade}

        got_same_score   = new_grade_with_new_slot["totalScore"] == old_grade_with_old_slot["totalScore"]
        got_better_score = new_grade_with_new_slot["totalScore"] >  old_grade_with_old_slot["totalScore"]

        # Regular case: normal problematic rasps
        if need_better_score and got_better_score:
            the_slot = new_slot
            break
        elif need_better_score:
            why_fail.failure_reason(state, action, new_slot, rasp0, pure_new_slot_grade, pure_old_slot_grade)

        # Special case: problematic parallel groups and/or optionals at some slot
        if need_same_score and got_same_score:
            the_slot = new_slot
            break
        elif need_same_score:
            why_fail.failure_reason_rigorous(state, action, new_slot, rasp0, pure_new_slot_grade)

    if not the_slot:
        state.unsuccessful_rasps.add(rasp0.id)
        timetable[rasp0] = old_slot
        rasp_slots.update_rasp_rrules(state, old_slot, rasp0)
        tax_tool.tax_all_constraints(state, old_slot, rasp0)
        return (False, state)
    else:
        state.unsuccessful_rasps.clear()

    tax_tool.tax_all_constraints(state, the_slot, rasp0)

    timetable[rasp0] = the_slot
    return (False, state)
