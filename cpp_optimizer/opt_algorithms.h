#include "types/my_types.h"
#include "common/common.h"

State variable_neighborhood_search(State& state, double CPU_TIME_SEC);

State grasp(State& state, int num_candidates, int num_restrict, double CPU_TIME_SEC);

State repeated_local_search(State& state, double CPU_TIME_SEC);

State iterated_local_search(State& state, double CPU_TIME_SEC);

State simulated_annealing(State& state, int temperature, double CPU_TIME_SEC);
