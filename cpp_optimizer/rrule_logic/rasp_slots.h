#pragma once
#include "../types/my_types.h"
#include <iostream>
#include <vector>

Slot get_random_slot(State& state, Rasp& rasp);

void update_possible_slots(State& state, std::vector<Slot>& pool, Rasp& rasp, int week, int day, std::string fixed_hour);

std::vector<Slot> get_rasp_slots(State& state, Rasp& rasp, bool shuffle_slots);

void update_rasp_rrules(State& state, Slot& slot, Rasp& rasp);

void clear_rasp_rrules(State& state, Rasp& rasp);

bool can_swap_rasp_slots(State& state, Rasp& rasp0, Rasp& rasp1, Slot& slot0, Slot& slot1);
