#pragma once
#include "../types/my_types.h"
#include <set>

std::set<triplet> get_own_groups_all_dates(State &state, Rasp &rasp);

std::set<triplet> get_other_groups_all_dates(State& state, Rasp& rasp);
