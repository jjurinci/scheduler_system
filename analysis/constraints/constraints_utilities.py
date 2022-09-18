"""
Returns sum of all professor's rasp durations.
"""
def get_professor_rasps_duration(rasps, professor_id):
    return sum(rasp.duration for rasp in rasps if rasp.professor_id == professor_id)


"""
Given a row of weekdays where each weekday could be "T", "F", or a list of
ranges like [2,4,8,9] the function returns free time (int) contained in that row.
"""
def get_free_time(row, NUM_HOURS):
    keys = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    free_time = 0
    for key in keys:
        if row[key] == "F":
            continue
        elif row[key] == "T":
            free_time += NUM_HOURS
        else:
            times = row[key].split(",")
            for i in range(0, len(times), 2):
                start, end = int(times[i]), int(times[i+1])
                free_time += (end - start + 1)
    return free_time


"""
Function checks if there is enough free time in rooms to fit all rasps.

1) Calculates free time for each room, then appends all rooms to a list
2) Sorts that list by has_computers=False first, smallest capacity second, smallest free time third
   This way the rooms with smallest resources are first in the list.
3) Iterates through all rasps and tries to greedily fit them into the first
   room that satisfies computer, capacity, and free time requirements.
4) Returns True if all rasps could be fit, False otherwise
"""
def check_capacity_free_time(rasps, classrooms, room_available, NUM_DAYS, NUM_HOURS, students_per_rasp):
    constrained_rooms = {room.room_id : room for _, room in room_available.iterrows()}
    rooms_free_time = []
    for room in classrooms.values():
        free_time = NUM_DAYS * NUM_HOURS
        if room.id in constrained_rooms:
            free_time = get_free_time(constrained_rooms[room.id], NUM_HOURS)

        room_obj = {"id": room.id, "capacity": room.capacity,
                    "has_computers":room.has_computers, "free_time":free_time}
        rooms_free_time.append(room_obj)


    # sort by has_computers=False first, by smallest capacity second, by free_time third
    rooms_free_time.sort(key=lambda room: (room["has_computers"], room["capacity"], room["free_time"]))

    fit_rasps_count = 0
    for rasp in rasps:
        for room_obj in rooms_free_time:
            if room_obj["has_computers"] == rasp.needs_computers and \
               room_obj["capacity"] >= students_per_rasp[rasp.id] and \
               room_obj["free_time"] - rasp.duration >= 0:
                   room_obj["free_time"] -= rasp.duration
                   fit_rasps_count += 1
                   break

    return fit_rasps_count == len(rasps)


"""
Returns True if string is a postiive integer.
E.g. 0,1,2,3,4,... -> True
"""
def is_positive_integer(value: str, include_zero = False):
    try:
        num = int(value)

        if not include_zero:
            return True if num > 0 else False
        else:
            return True if num >= 0 else False
    except ValueError:
        return False


"""
Returns a list of errors related to free time formatting in initial constraints csvs.
E.g. "2,5,6,9" has no errors.
     "abc" has errors. (strings)
     "5,2" has errors. (start > end)
     "2,5,7" has errors. (odd number of values)
"""
def is_valid_time(time: str, file_name, index, column, NUM_HOURS):
    if time == "T" or time == "F":
        return []

    errors = []
    times = time.split(",")
    for number in times:
        if not is_positive_integer(number):
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{number}' is not a positive integer (or 'T' or 'F').")

        if is_positive_integer(number) and (int(number)<1 or int(number)>NUM_HOURS):
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{number}' is not in range [1,{NUM_HOURS}].")

    if errors:
        return errors

    if len(times) % 2 == 1:
        errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" value '{time}' does not have an even number of integers. {len(times)} integers given.")
        return errors

    for i in range(0, len(times), 2):
        start, end = int(times[i]), int(times[i+1])
        if end - start <= 0:
            errors.append(f"ERROR: In {file_name} -> In Row {index} In column \"{column}\" values '{start}' (start) and '{end}' (end) don't make a valid time block.")

    return errors
