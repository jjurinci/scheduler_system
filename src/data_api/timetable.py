def get_fixed_timetable(rasps):
    FIXED = {}
    for rasp in rasps:
        if not rasp.fixedAt:
            continue
        room_id, day, hour = rasp.fixedAt.split(",")
        day, hour = int(day)-1, int(hour)-1
        FIXED[rasp] = (room_id, day, hour)
    return FIXED

def get_empty_timetable(rasps):
    return {rasp:None for rasp in rasps}
