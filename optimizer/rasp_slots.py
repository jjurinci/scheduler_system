from utilities.my_types import Slot

""" Returns Slot(room_id, week, day, hour) for given (week, day, hour).
"""
def get_possible_slots(state, rasp, week, day, hour = None):
    rooms_occupied = state.mutable_constraints.rooms_occupied
    NUM_HOURS      = state.time_structure.NUM_HOURS

    room_pool = set()
    if rasp.fix_at_room_id:
        room_pool = set([rasp.fix_at_room_id])
    else:
        room_pool = set(room_id for room_id in rooms_occupied)

    if hour != None: # hour=0 should trigger this if
        return set([Slot(room_id, week, day, hour)
                    for room_id in room_pool])
    else:
        return set([Slot(room_id, week, day, hr)
                    for room_id in room_pool
                    for hr in range(NUM_HOURS)
                    if hr+rasp.duration < NUM_HOURS])


"""
Returns a set of possible starting Slot(room_id, week, day, hour)s for a rasp.
Used later to pick DTSTART of rasp.
"""
def get_rasp_slots(state, rasp):
    rasp_rrules = state.rasp_rrules
    pool = set()
    dtstart_weekdays = rasp_rrules[rasp.id]["dtstart_weekdays"]
    for given_week, given_day in dtstart_weekdays:
        pool |= get_possible_slots(state, rasp, given_week, given_day, rasp.fixed_hour)
    return pool


"""
Updates rasp's DTSTART, UNTIL and all_dates to new values.
"""
def update_rasp_rrules(state, slot, rasp):
    rasp_rrules = state.rasp_rrules
    rrule_table = state.rrule_table

    index = rasp_rrules[rasp.id]["rrule_table_index"]
    key = (slot.week, slot.day)
    rrule_table_element = rrule_table[index][key]
    all_dates = [(week, day, hour)
                 for week, day in rrule_table_element
                 for hour in range(slot.hour, slot.hour + rasp.duration)]
    rasp_rrules[rasp.id]["DTSTART"] = all_dates[0]
    rasp_rrules[rasp.id]["UNTIL"] = all_dates[-1]
    rasp_rrules[rasp.id]["all_dates"] = all_dates


def clear_rasp_rrules(state, rasp):
    rasp_rrules = state.rasp_rrules

    rasp_rrules[rasp.id]["DTSTART"] = None
    rasp_rrules[rasp.id]["UNTIL"] = None
    rasp_rrules[rasp.id]["all_dates"] = []


"""
Checks if two rasp slots can be swapped.
"""
def check_rasps_swap(state, rasp0, rasp1, slot0, slot1):
    NUM_HOURS = state.time_structure.NUM_HOURS
    rasp_rrules = state.rasp_rrules
    rrule_table = state.rrule_table

    index0 = rasp_rrules[rasp0.id]["rrule_table_index"]
    index1 = rasp_rrules[rasp1.id]["rrule_table_index"]
    key0 = (slot0.week, slot0.day)
    key1 = (slot1.week, slot1.day)

    if key1 not in rrule_table[index0] or key0 not in rrule_table[index1] or \
        (rasp0.duration + slot1.hour >= NUM_HOURS) or (rasp1.duration + slot0.hour >= NUM_HOURS) or \
        rasp0.fixed_hour != rasp1.fixed_hour:
        return False
    return True
