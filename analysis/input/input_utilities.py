from dateutil.rrule import rrulestr
from datetime import datetime

"""
Returns True if all dates of a given rrule:
1) Fit inside [START_SEMESTER_DATE, END_SEMESTER_DATE] interval AND
2) Have valid academic hours (defined in timeblocks)
"""
def is_valid_rrule(rrule_str: str, START_SEMESTER_DATE: datetime, END_SEMESTER_DATE: datetime, hour_to_index: dict, rasp, index):
    rrule_str = rrule_str[1:-1].replace("\\n", "\n")
    try:
        rrule_obj = rrulestr(rrule_str)
    except Exception:
        print(f"ERROR: In rasps.csv -> In Row {index} cannot parse \"rrule\".")
        return False

    days = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"}
    allowed_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    start_sem_date_repr = START_SEMESTER_DATE.strftime("%d/%m/%Y,%H:%M")
    end_sem_date_repr   = END_SEMESTER_DATE.strftime("%d/%m/%Y,%H:%M")

    possible_indexes = list(hour_to_index.values())
    all_dates = list(rrule_obj)

    for rrule_date in all_dates:
        rrule_date_repr = rrule_date.strftime("%d/%m/%Y,%H:%M")
        hour_min = rrule_date.strftime("%H:%M")
        weekday = days[rrule_date.weekday()]

        if weekday not in allowed_days:
            print(f"ERROR: In rasps.csv -> In Row {index} {rasp.id=} -> invalid \"rrule\" because rrule date={rrule_date_repr} has a weekday '{weekday}' but only these are allowed {allowed_days}")
            return False
        if rrule_date < START_SEMESTER_DATE:
            print(f"ERROR: In rasps.csv -> In Row {index} {rasp.id=} -> invalid \"rrule\" because rrule date={rrule_date_repr} is lesser than START_SEMESTER_DATE={start_sem_date_repr}.")
            return False
        if rrule_date > END_SEMESTER_DATE:
            print(f"ERROR: In rasps.csv -> In Row {index} {rasp.id=} -> invalid \"rrule\" because rrule date={rrule_date_repr} is bigger than END_SEMESTER_DATE={end_sem_date_repr}.")
            return False
        if hour_min != "00:00" and hour_min not in hour_to_index:
            print(f"ERROR: In rasps.csv -> In Row {index} {rasp.id=} -> invalid \"rrule\" because rrule date={rrule_date_repr} has hour:min which is not an academic hour:min.")
            return False
        if hour_min != "00:00":
            index = hour_to_index[hour_min]
            duration = int(rasp.duration)
            if index + duration - 1 not in possible_indexes:
                print(f"ERROR: In rasps.csv -> In Row {index} {rasp.id=} -> invalid \"rrule\" because rrule date={rrule_date_repr} has hour:min that is too late to hold {duration=} academic hours.")
                return False

    return True


"""
Returns a list of invalid semester fks in subjects.csv.
Invalid semester fk is one that doesn't exist as an id in semesters.csv.
"""
def invalid_semesterIds(semesterIds: str, real_semester_ids: set):
    foreign_keys = semesterIds.split(",")
    return [fk for fk in foreign_keys if fk != "" and fk not in real_semester_ids]


"""
Returns True if a string is float.
E.g. "3.123" -> True, "a3.123" -> False
"""
def is_float(number: str):
    try:
        float(number)
        return True
    except ValueError:
        return False


"""
Returns True if string is strictly a positive integer.
E.g. 0,1,2,3,4,5,... -> True
0.1, 1.3, ... -> False
"""
def is_positive_integer(value, include_zero = False):
    try:
        float_num = float(value)
        if not float_num.is_integer():
            return False

        num = int(float_num)

        if not include_zero:
            return True if num > 0 else False
        else:
            return True if num >= 0 else False
    except ValueError:
        return False


"""
Returns True if string is either zero or one.
"""
def is_zero_or_one(number):
    if number=="0" or number=="1" or number=="0.0" or number=="1.0":
        return True
    return False


"""
Returns True if semester has a valid season string.
"""
def is_valid_season(value: str):
    return True if value=="W" or value=="S" else False


"""
Returns True if date is a valid starting or ending year date.
"""
def is_valid_sem_date(date):
    if not date:
        return False

    split_dot = date.split(".")
    if len(split_dot) < 3:
        return False

    day, month, year = split_dot[0], split_dot[1], split_dot[2]
    monthdays = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}

    if not year.isdigit() or not month.isdigit() or not day.isdigit():
        return False

    day, month, year = int(day), int(month), int(year)
    if year < 1 or month < 1 or month > 12:
        return False
    if day < 1 or day > monthdays[month]:
        return False

    return True

"""
Returns True if timeblock is a valid timeblock.
"""
def is_valid_timeblock(timeblock):
    if not timeblock:
        return False

    split_dot = timeblock.split("-")
    if len(split_dot) != 2:
        return False

    start, end = split_dot[0], split_dot[1]
    start_split, end_split = start.split(":"), end.split(":")

    if len(start_split) != 2 or len(end_split) != 2:
        return False

    if len(start_split[0]) != 2 or len(start_split[1]) != 2 or \
       len(end_split[0]) != 2 or len(end_split[1]) != 2:
           return False

    return True
