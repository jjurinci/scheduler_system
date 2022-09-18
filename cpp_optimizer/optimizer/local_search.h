#pragma once
#include "../types/my_types.h"

std::vector<std::pair<double, int>> get_grasp_tracker();

std::vector<std::pair<double, int>> get_rls_tracker();

std::vector<std::pair<double, int>> get_ils_tracker();

void clear_ls_tracker();

void set_rls_tracker();

void set_ils_tracker();

void set_grasp_tracker();

Slot* steepest_better_slot(State& state, Rasp& rasp0, Grade& only_old_slot_grade);

Slot* first_better_slot(State& state, Rasp& rasp0, Grade& only_old_slot_grade);

bool find_better_neighbor(State& state, double& current_best_grade, double CPU_TIME_SEC, time_point start_time);

void local_search(State& state, double current_best_grade, double CPU_TIME_SEC, time_point start_time);
