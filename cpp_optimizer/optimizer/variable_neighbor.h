#pragma once
#include "../types/my_types.h"

std::vector<std::pair<double, int>> get_vns_tracker();

void clear_vns_tracker();

bool swap_pairs(State& state, Rasp rasp0, Rasp rasp1);

bool vnd_neighborhood_2(State& state);

bool vnd_neighborhood_1(State& state);

void variable_neighborhood_descent(State& state, double& current_best_grade, double CPU_TIME_SEC, time_point start_time);

void shake(State& state, int neighbor_k, double& current_best_grade, time_point start_time);

void run_vns(State& state, double current_best_grade, double CPU_TIME_SEC, time_point start_time);
