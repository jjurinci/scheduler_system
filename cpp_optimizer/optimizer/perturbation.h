#pragma once
#include "../types/my_types.h"
#include <vector>

void set_random_slots(State& state, std::vector<Rasp>& rasps);

void set_semi_random_slots(State& state, float percent, time_point start_time);

void random_timetable(State& state, time_point start_time);

void semi_random_timetable(State& state, float percent, time_point start_time);
