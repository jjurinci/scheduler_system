import optimizer.taxing.tax_rooms     as tax_rooms
import optimizer.taxing.tax_nasts     as tax_nasts
import optimizer.taxing.tax_profs     as tax_profs
import optimizer.taxing.tax_capacity  as tax_capac
import optimizer.taxing.tax_computers as tax_compu

"""
Taxes:
    1) rasp's all_dates path in rooms, professors, and nasts (semesters).
    2) rasp's capacity and computers problem.
"""
def tax_all_constraints(state, slot, rasp):
    tax_rooms.tax_rrule_in_rooms(state, slot.room_id, rasp)
    tax_profs.tax_rrule_in_profs(state, rasp)
    tax_nasts.tax_rrule_in_nasts(state, rasp)
    tax_capac.tax_capacity(state, slot.room_id, rasp)
    tax_compu.tax_computers(state, slot.room_id, rasp)

"""
Untaxes:
    1) rasp's all_dates path in rooms, professors, and nasts (semesters).
    2) rasp's capacity and computers problem.
"""
def untax_all_constraints(state, slot, rasp):
    tax_rooms.untax_rrule_in_rooms(state, slot.room_id, rasp)
    tax_profs.untax_rrule_in_profs(state, rasp)
    tax_nasts.untax_rrule_in_nasts(state, rasp)
    tax_capac.untax_capacity(state, slot.room_id, rasp)
    tax_compu.untax_computers(state, slot.room_id, rasp)
