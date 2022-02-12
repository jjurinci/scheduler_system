import optimizer.tax_tool.tax_rooms     as tax_rooms
import optimizer.tax_tool.tax_nasts     as tax_nasts
import optimizer.tax_tool.tax_profs     as tax_profs
import optimizer.tax_tool.tax_capacity  as tax_capac
import optimizer.tax_tool.tax_computers as tax_compu

def tax_all_constraints(state, slot, rasp):
    tax_rooms.tax_rrule_in_rooms(state, slot.room_id, rasp)
    tax_profs.tax_rrule_in_profs(state, rasp)
    tax_nasts.tax_rrule_in_nasts(state, slot, rasp)
    tax_capac.tax_capacity(state, slot.room_id, rasp)
    tax_compu.tax_computers(state, slot.room_id, rasp)


def untax_all_constraints(state, slot, rasp):
    tax_rooms.untax_rrule_in_rooms(state, slot.room_id, rasp)
    tax_profs.untax_rrule_in_profs(state, rasp)
    tax_nasts.untax_rrule_in_nasts(state, slot, rasp)
    tax_capac.untax_capacity(state, slot.room_id, rasp)
    tax_compu.untax_computers(state, slot.room_id, rasp)