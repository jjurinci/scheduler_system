from utilities.my_types import Slot

"""
Returns Slot(room_id, week, day, hour) for given (week, day, hour).
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
    if rasp.random_dtstart_weekday and rasp.fixed_hour == None:
        dtstart_weekdays = rasp_rrules[rasp.id]["dtstart_weekdays"]
        for given_week, given_day, _ in dtstart_weekdays:
            pool |= get_possible_slots(state, rasp, given_week, given_day)

    elif rasp.random_dtstart_weekday and rasp.fixed_hour != None:
        dtstart_weekdays = rasp_rrules[rasp.id]["dtstart_weekdays"]
        for given_week, given_day, _ in dtstart_weekdays:
            pool |= get_possible_slots(state, rasp, given_week, given_day, rasp.fixed_hour)

    elif not rasp.random_dtstart_weekday and rasp.fixed_hour == None:
        given_week, given_day, _ = rasp_rrules[rasp.id]["DTSTART"]
        pool |= get_possible_slots(state, rasp, given_week, given_day)

    elif not rasp.random_dtstart_weekday and rasp.fixed_hour != None:
        given_week, given_day, _ = rasp_rrules[rasp.id]["DTSTART"]
        pool |= get_possible_slots(state, rasp, given_week, given_day, rasp.fixed_hour)
    return pool


"""
Updates rasp's DTSTART, UNTIL and all_dates to new values.
"""
def update_rasp_rrules(state, slot, rasp):
    rasp_rrules = state.rasp_rrules
    rrule_space = state.rrule_space

    index = rasp_rrules[rasp.id]["possible_all_dates_idx"]
    key = (slot.week, slot.day)
    rrule_enumeration = rrule_space[index][key]
    all_dates = [(week, day, slot.hour) for week, day in rrule_enumeration]
    rasp_rrules[rasp.id]["DTSTART"] = all_dates[0]
    rasp_rrules[rasp.id]["UNTIL"] = all_dates[-1]
    rasp_rrules[rasp.id]["all_dates"] = all_dates
