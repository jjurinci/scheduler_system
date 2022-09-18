#pragma once
#include "../types/my_types.h"
#include <iostream>
#include <vector>

typedef std::vector<std::pair<Slot, int>> Rcl;

void select_random_element(State& state, Rcl& rcl, Rasp& rasp0);

void apply_greedy(State& state, Rcl& candidate_list, int& num_candidates, Rasp& rasp0, double CPU_TIME_SEC, time_point start_time);

Rcl make_rcl(State& state, int& num_candidates, int& num_restrict, Rasp& rasp0, double CPU_TIME_SEC, time_point start_time);

void construct_solution(State& state, int num_candidates, int num_restrict, double CPU_TIME_SEC, time_point start_time);
