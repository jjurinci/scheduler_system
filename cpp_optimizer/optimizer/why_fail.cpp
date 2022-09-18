#include "why_fail.h"

void update_failure_reason(BannedSlots& banned, Slot& slot, Grade& only_new_slot_grade, Grade& only_old_slot_grade) {
    int old_total     = only_old_slot_grade.totalScore;
    int new_professor = only_new_slot_grade.professorScore;
    int new_semester  = only_new_slot_grade.semScore;
    int new_capacity  = only_new_slot_grade.capacityScore;
    int new_computer  = only_new_slot_grade.computerScore;
    triplet date = std::make_tuple(slot.week, slot.day, slot.hour);

    if((new_professor + new_semester) <= old_total) {
        banned.ban_dates.insert(date);
    }
    if((new_capacity + new_computer) <= old_total) {
        banned.ban_rooms.insert(slot.room_id);
    }
}

bool is_skippable(BannedSlots& banned, Slot& slot) {
    triplet date = std::make_tuple(slot.week, slot.day, slot.hour);
    return banned.ban_rooms.find(slot.room_id) != banned.ban_rooms.end() ||
           banned.ban_dates.find(date) != banned.ban_dates.end();
}
