#include "tax_tool.h"
#include "tax_rooms.h"
#include "tax_profs.h"
#include "tax_sems.h"
#include "tax_capacity.h"
#include "tax_computers.h"
#include "../rrule_logic/rasp_slots.h"
#include <map>

void tax_all_constraints(State& state, Slot& slot, Rasp& rasp) {
    tax_rrule_in_rooms(state, slot.room_id, rasp);
    tax_rrule_in_profs(state, rasp);
    tax_rrule_in_sems(state, rasp);
    tax_capacity(state, slot.room_id, rasp);
    tax_computers(state, slot.room_id, rasp);
}

void untax_all_constraints(State& state, Slot& slot, Rasp& rasp) {
    untax_rrule_in_rooms(state, slot.room_id, rasp);
    untax_rrule_in_profs(state, rasp);
    untax_rrule_in_sems(state, rasp);
    untax_capacity(state, slot.room_id, rasp);
    untax_computers(state, slot.room_id, rasp);
}

void tax_new_slot(State& state, Rasp& rasp, Slot& new_slot) {
    update_rasp_rrules(state, new_slot, rasp);
    tax_all_constraints(state, new_slot, rasp);
    state.timetable[rasp] = new_slot;
}

Grade untax_old_slot(State& state, Rasp& rasp, Slot& old_slot) {
    Grade grade_with_old_slot = Grade(state.grade);
    untax_all_constraints(state, old_slot, rasp);
    Grade grade_without_old_slot = Grade(state.grade);
    Grade only_old_slot_grade = grade_with_old_slot - grade_without_old_slot;
    clear_rasp_rrules(state, rasp);
    state.timetable[rasp] = Slot{"",-1,-1,-1};
    return only_old_slot_grade;
}
