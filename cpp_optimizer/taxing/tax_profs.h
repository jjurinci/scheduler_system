#pragma once
#include "../types/my_types.h"

void update_grade_profs(State& state, int punish, bool plus=true);

void tax_rrule_in_profs(State& state, Rasp& rasp);

void untax_rrule_in_profs(State& state, Rasp& rasp);
