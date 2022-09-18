#pragma once
#include "../types/my_types.h"

void update_grade_rooms(State& state, int punish, bool plus=true);

void tax_rrule_in_rooms(State& state, id_room room_id, Rasp& rasp);

void untax_rrule_in_rooms(State& state, id_room room_id, Rasp& rasp);
