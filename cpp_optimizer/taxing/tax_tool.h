#pragma once
#include "../types/my_types.h"

void tax_all_constraints(State& state, Slot& slot, Rasp& rasp);

void untax_all_constraints(State& state, Slot& slot, Rasp& rasp);

void tax_new_slot(State& state, Rasp& rasp, Slot& new_slot);

Grade untax_old_slot(State& state, Rasp& rasp, Slot& old_slot);
