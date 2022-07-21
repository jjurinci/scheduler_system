import data_api.state          as state_api
import optimizer.optimizer_rrule as optimizer
from utilities.general_utilities import save_timetable_to_file


"""
Termination critera for the iterated local search algorithm.
"""
def terminate(state):
    if state.grades["all"]["totalScore"] == 0:
        return True
    return False


"""
Starts solver whose goal is to construct a timetable with fewest collisions possible.
Returns an State object that holds all information necessary to manipulate the timetable
in the future.
"""
def iterated_local_search(ITERATIONS):
    state = state_api.get_state()
    for _ in range(ITERATIONS):
        try:
            state_api.clear_mutable(state)
            optimizer.set_random_timetable(state)
            optimizer.local_search(state, 100000)
            if terminate(state):
                break

        except KeyboardInterrupt:
            break

    save_timetable_to_file(state, "saved_timetables/one_state.pickle")


iterated_local_search(5)
