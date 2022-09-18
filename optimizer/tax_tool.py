import optimizer.taxing.tax_rooms     as tax_rooms
import optimizer.taxing.tax_sems      as tax_sems
import optimizer.taxing.tax_profs     as tax_profs
import optimizer.taxing.tax_capacity  as tax_capac
import optimizer.taxing.tax_computers as tax_compu
import optimizer.rasp_slots           as rasp_slots

"""
Taxes:
    1) rasp's all_dates path in rooms, professors, and sems (semesters).
    2) rasp's capacity and computers problem.
"""
def tax_all_constraints(state, slot, rasp):
    tax_rooms.tax_rrule_in_rooms(state, slot.room_id, rasp)
    tax_profs.tax_rrule_in_profs(state, rasp)
    tax_sems.tax_rrule_in_sems(state, rasp)
    tax_capac.tax_capacity(state, slot.room_id, rasp)
    tax_compu.tax_computers(state, slot.room_id, rasp)

"""
Untaxes:
    1) rasp's all_dates path in rooms, professors, and sems (semesters).
    2) rasp's capacity and computers problem.
"""
def untax_all_constraints(state, slot, rasp):
    tax_rooms.untax_rrule_in_rooms(state, slot.room_id, rasp)
    tax_profs.untax_rrule_in_profs(state, rasp)
    tax_sems.untax_rrule_in_sems(state, rasp)
    tax_capac.untax_capacity(state, slot.room_id, rasp)
    tax_compu.untax_computers(state, slot.room_id, rasp)


def tax_new_slot(state, rasp, new_slot):
    timetable = state.timetable
    rasp_slots.update_rasp_rrules(state, new_slot, rasp)
    tax_all_constraints(state, new_slot, rasp)
    timetable[rasp] = new_slot


def untax_old_slot(state, rasp, old_slot):
    grade = state.grade
    grade_with_old_slot = grade.copy()
    untax_all_constraints(state, old_slot, rasp)
    grade_without_old_slot = grade.copy()
    only_old_slot_grade = {k:grade_with_old_slot[k] - grade_without_old_slot[k] for k in grade_with_old_slot}
    rasp_slots.clear_rasp_rrules(state, rasp)
    state.timetable[rasp] = None
    return only_old_slot_grade

