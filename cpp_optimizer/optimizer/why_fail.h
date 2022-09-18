#pragma once
#include "../types/my_types.h"

void update_failure_reason(BannedSlots& banned, Slot& slot, Grade& only_new_slot_grade, Grade& only_old_slot_grade);

bool is_skippable(BannedSlots& banned, Slot& slot);
