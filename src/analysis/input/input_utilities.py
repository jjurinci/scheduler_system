from dateutil.rrule import rrulestr
from datetime import datetime

"""
Returns True if all dates of a given rrule:
1) Fit inside [START_SEMESTER_DATE, END_SEMESTER_DATE] interval AND
2) Have valid academic hours (defined in timeblocks)
"""
def is_valid_rrule(rrule_str: str, START_SEMESTER_DATE: datetime, END_SEMESTER_DATE: datetime, hour_to_index: dict, index):
    rrule_str = rrule_str[1:-1].replace("\\n", "\n")
    try:
        rrule_obj = rrulestr(rrule_str)
    except Exception:
        print(f"ERROR: In rasps.csv -> In Row {index} cannot parse \"rrule\".")
        return False

    start_sem_date_repr = START_SEMESTER_DATE.strftime("%d/%m/%Y,%H:%M")
    end_sem_date_repr   = END_SEMESTER_DATE.strftime("%d/%m/%Y,%H:%M")

    all_dates = list(rrule_obj)
    for rrule_date in all_dates:
        rrule_date_repr = rrule_date.strftime("%d/%m/%Y,%H:%M")
        hour_min = rrule_date.strftime("%H:%M")

        if rrule_date < START_SEMESTER_DATE:
            print(f"ERROR: In rasps.csv -> In Row {index} invalid \"rrule\" because rrule date={rrule_date_repr} is lesser than START_SEMESTER_DATE={start_sem_date_repr}.")
            return False
        if rrule_date > END_SEMESTER_DATE:
            print(f"ERROR: In rasps.csv -> In Row {index} invalid \"rrule\" because rrule date={rrule_date_repr} is bigger than END_SEMESTER_DATE={end_sem_date_repr}.")
            return False
        if hour_min != "00:00" and hour_min not in hour_to_index:
            print(f"ERROR: In rasps.csv -> In Row {index} invalid \"rrule\" because rrule date={rrule_date_repr} has hour:min which is not an academic hour:min.")
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
def is_positive_integer(value: str, include_zero = False):
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
def is_zero_or_one(number: str):
    if number=="0" or number=="1" or number=="0.0" or number=="1.0":
        return True
    return False


"""
Returns True if semester has a valid season string.
"""
def is_valid_season(value: str):
    return True if value=="W" or value=="S" else False
