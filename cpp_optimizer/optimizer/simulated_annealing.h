#pragma once
#include "../types/my_types.h"

std::vector<std::pair<double, int>> get_sa_tracker();

void clear_sa_tracker();

void clear_ls_tracker();

double P(int old_score, int new_score, double temp);

Slot* annealing_descent(State& state, Rasp& rasp, Grade only_old_slot_grade, double temp);

bool next_neighbor(State& state, double& temp, double& current_best_grade, double CPU_TIME_SEC, time_point start_time);

void run_sa(State& state, int temperature, double current_best_grade, double CPU_TIME_SEC, time_point start_time);
