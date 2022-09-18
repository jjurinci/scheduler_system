import time
import random
import data_api.state            as state_api
import optimizer.rasp_slots      as rasp_slots
import optimizer.tax_tool        as tax_tool
import optimizer.grade_tool      as grade_tool
from tqdm import tqdm


def construct_solution(state, num_candidates, num_restrict, CPU_TIME_SEC, start_time):
    state_api.clear_mutable(state)

    the_rasps = [rasp for rasp in state.rasps]
    random.shuffle(the_rasps)

    for i in tqdm(range(len(the_rasps))):
        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            num_candidates, num_restrict = 1,1

        rasp = state.rasps[i]
        rcl = make_rcl(state, num_candidates, num_restrict, rasp, CPU_TIME_SEC, start_time)
        select_random_element(state, rcl, rasp)
        tqdm.write(f"{round(elapsed_time, 2)}, {i} {state.grade}")


def make_rcl(state, num_candidates, num_restrict, rasp, CPU_TIME_SEC, start_time):
    rcl = apply_greedy(state, num_candidates, rasp, CPU_TIME_SEC, start_time)
    rcl.sort(key = lambda x:x[1]["totalScore"], reverse=True)
    rcl = rcl[:num_restrict]
    return rcl


def select_random_element(state, rcl, rasp):
    solution = random.choice(rcl)
    slot = solution[0]
    tax_tool.tax_new_slot(state, rasp, slot)


def apply_greedy(state, num_candidates, rasp, CPU_TIME_SEC, start_time):
    candidate_list = []
    pool = list(rasp_slots.get_rasp_slots(state, rasp))
    random.shuffle(pool)
    pool = pool[:num_candidates]
    for new_slot in pool:
        rasp_slots.update_rasp_rrules(state, new_slot, rasp)
        only_new_slot_grade = grade_tool.count_all_collisions(state, new_slot, rasp)
        candidate_list.append((new_slot, only_new_slot_grade))

        elapsed_time = time.time() - start_time
        if elapsed_time >= CPU_TIME_SEC:
            break
    return candidate_list
