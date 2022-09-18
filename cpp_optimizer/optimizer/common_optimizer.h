#pragma once
#include "../types/my_types.h"
#include <set>

void update_tabu_list(std::set<id_rasp>& tabu_list, Rasp& rasp0, Slot* new_slot_ptr);
