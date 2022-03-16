"""
Returns an empty timetable with None as its slots.
"""
def get_empty_timetable(rasps):
    return {rasp: None for rasp in rasps}
