import time
import data_api.state                  as state_api
import optimizer.perturbation          as perturbation
import optimizer.grasp                 as grasp
import optimizer.local_search          as local_search
import optimizer.variable_neighborhood as vns
import optimizer.simulated_annealing   as sa


def update_solution(state, best_grade, best_state):
    if state.grade["totalScore"] > best_grade:
        return (state.grade["totalScore"], state)
    else:
        return (best_grade, best_state)


def iterate(CPU_TIME_SEC, optimizer, **optimizer_args):
    best_grade, best_state = float("-inf"), optimizer_args["state"]
    start_time = time.time()
    optimizer_args["CPU_TIME_SEC"] = CPU_TIME_SEC
    optimizer_args["start_time"] = start_time

    while True:
        try:
            state = optimizer(**optimizer_args)
            best_grade, best_state = update_solution(state, best_grade, best_state)
            if best_grade == 0:
                break

            elapsed_time = time.time() - start_time
            if elapsed_time >= CPU_TIME_SEC:
                print("STOPPING DUE TO ELAPSED TIME.")
                break

        except KeyboardInterrupt:
            break

    print(f"BEST_GRADE: {best_grade}")
    return best_state


def grasp_iterate(CPU_TIME_SEC, num_candidates, num_restrict):
    return iterate(CPU_TIME_SEC, grasp_search, state=state_api.get_state(), num_candidates=num_candidates, num_restrict=num_restrict)


def repeated_local_search(CPU_TIME_SEC):
    return iterate(CPU_TIME_SEC, local_search_basic, state=state_api.get_state())


def iterated_local_search(CPU_TIME_SEC):
    return iterate(CPU_TIME_SEC, local_search_semi, state=state_api.get_state())


def simulated_annealing_iterate(CPU_TIME_SEC, temperature):
    return iterate(CPU_TIME_SEC, simulated_annealing, state=state_api.get_state(), temperature=temperature)


def vns_iterate(CPU_TIME_SEC):
    return iterate(CPU_TIME_SEC, variable_neighborhood, state=state_api.get_state())


def grasp_search(state, num_candidates, num_restrict, CPU_TIME_SEC, start_time):
    grasp.construct_solution(state, num_candidates, num_restrict, CPU_TIME_SEC, start_time)
    local_search.run(state, CPU_TIME_SEC, start_time)
    return state


def local_search_basic(state, CPU_TIME_SEC, start_time):
    perturbation.random_timetable(state)
    local_search.run(state, CPU_TIME_SEC, start_time)
    return state


def local_search_semi(state, CPU_TIME_SEC, start_time):
    perturbation.semi_random_timetable(state, 0.2)
    local_search.run(state, CPU_TIME_SEC, start_time)
    return state


def variable_neighborhood(state, CPU_TIME_SEC, start_time):
    perturbation.random_timetable(state)
    vns.run(state, CPU_TIME_SEC, start_time)
    return state


def simulated_annealing(state, temperature, CPU_TIME_SEC, start_time):
    perturbation.random_timetable(state)
    sa.run(state, temperature, CPU_TIME_SEC, start_time)
    return state

