import time
import random
import data_api.state            as state_api
import optimizer.rasp_slots      as rasp_slots
import optimizer.tax_tool        as tax_tool
import optimizer.grade_tool      as grade_tool
import data_api.state            as state_api
import optimizer.local_search    as local_search
from tqdm import tqdm


def random_timetable(state):
    print("Generating random timetable.")
    state_api.clear_mutable(state)
    set_random_slots(state, state.rasps)


def semi_random_timetable(state, percent=0.05):
    first_iteration = True if not state.timetable else False
    if first_iteration:
        print("Generating random timetable.")
        set_random_slots(state, state.rasps)
    else:
        print("Generating semi random timetable.")
        set_semi_random_slots(state, percent)


def set_random_slots(state, rasps):
    for rasp in tqdm(rasps):
        pool = rasp_slots.get_rasp_slots(state, rasp)
        slot = random.choice(tuple(pool))
        tax_tool.tax_new_slot(state, rasp, slot)


def set_semi_random_slots(state, percent):
    # Schedule only the most problematic rasps
    problematic_rasps = grade_tool.most_problematic_rasps(state, percent)
    state_api.clear_mutable(state)
    set_random_slots(state, problematic_rasps)

    # Reach local optimum
    start_time = time.time()
    local_search.run(state, 5, start_time)

    # Randomly schedule other rasps
    other_rasps = set(state.rasps) - set(problematic_rasps)
    set_random_slots(state, other_rasps)
