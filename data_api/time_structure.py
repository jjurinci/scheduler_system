import json
from dateutil.rrule import rrulestr, rrule, DAILY
from datetime import datetime, timedelta
from utilities.my_types import Timeblock, TimeStructure
from utilities.general_utilities import load_settings

"""
Returns two dates:
START_SEMESTER_DATE = date when the semester begins.
END_SEMESTER_DATE   = date when the semester ends.
"""
def get_start_end_year():
    settings = load_settings()
    path = settings["path_startendyear_json"]
    with open(path, "r", encoding="utf-8") as fp:
        start_end_year = json.load(fp)["start_end_year"][0]

    START_SEMESTER_DATE = start_end_year["start_semester_date"]
    END_SEMESTER_DATE   = start_end_year["end_semester_date"]

    start_list = START_SEMESTER_DATE.split(".")
    day, month, year  = int(start_list[0]), int(start_list[1]), int(start_list[2])
    START_SEMESTER_DATE = datetime(year, month, day)

    end_list = END_SEMESTER_DATE.split(".")
    day, month, year  = int(end_list[0]), int(end_list[1]), int(end_list[2])
    END_SEMESTER_DATE = datetime(year, month, day)

    return START_SEMESTER_DATE, END_SEMESTER_DATE


"""
Returns "timeblocks" dictionary which holds academic hours format.
For example:
1: 08:00-08:45,
2: 08:50-09:35,
3: 09:40-10:25,
...
"""
def get_timeblocks():
    settings = load_settings()
    path = settings["path_daystructure_json"]

    with open(path, "r", encoding="utf-8") as fp:
        day_structure = json.load(fp)["day_structure"]

    timeblocks = []
    for row in day_structure:
        tblock = {}
        tblock["index"] = row["#"]
        tblock["timeblock"] = row["timeblock"]
        tblock = Timeblock(**{field: tblock[field] for field in Timeblock._fields})
        timeblocks.append(tblock)

    return timeblocks


"""
Returns 2 dictionaries:
hour_to_index = converts hour (e.g. "08:00") to index (e.g. 0)
index_to_hour = converts index (e.g. 0) to hour (e.g. "08:00")
"""
def get_hour_index_structure(timeblocks):
    hour_to_index = {}
    index_to_hour = {}
    index = 0
    for tblock in timeblocks:
        start_hourmin = tblock.timeblock[:5]
        hour_to_index[start_hourmin] = index
        index_to_hour[index] = start_hourmin
        index += 1

    return hour_to_index, index_to_hour


"""
Returns TimeStructure object which contains all of the important time variables.
"""
def get_time_structure():
    START_SEMESTER_DATE, END_SEMESTER_DATE = get_start_end_year()
    NUM_WEEKS  = weeks_between(START_SEMESTER_DATE, END_SEMESTER_DATE)
    timeblocks = get_timeblocks()
    NUM_DAYS   = 5
    hour_to_index, index_to_hour = get_hour_index_structure(timeblocks)
    NUM_HOURS = len(timeblocks)

    return TimeStructure(START_SEMESTER_DATE, END_SEMESTER_DATE,
                         NUM_WEEKS, NUM_DAYS, NUM_HOURS,
                         timeblocks, hour_to_index, index_to_hour)



"""
Returns weeks between two dates.
It is 1-indexed -> "2021.10.4", "2021.10.4" will return 1 week
"""
def weeks_between(start_date, end_date):
    return ((end_date-start_date).days // 7) + 1


"""
Converts index triplet (week, day, hour) to matching datetime.
e.g. (0,0,0) might return datetime(2021, 10, 4, 8, 0)
"""
def index_to_date(week, day, hour, time_structure):
    START_SEMESTER_DATE = time_structure.START_SEMESTER_DATE
    index_to_hour = time_structure.index_to_hour
    NUM_HOURS = time_structure.NUM_HOURS

    # 2 (3rd) week, 1 tuesday, 13 (14th) hour
    hr, mins = 0, 0
    if hour >= 0 and hour < NUM_HOURS:
        hourmin = index_to_hour[hour]
        hr, mins = int(hourmin[:2]), int(hourmin[3:5])

    date = START_SEMESTER_DATE.replace(hour = hr, minute = mins)
    week_difference = timedelta(weeks = week)
    date = date + week_difference

    current_weekday = date.weekday()
    day_difference = timedelta(days = day - current_weekday)
    date = date + day_difference

    return date


"""
Converts datetime to matching index triplet (week, day, hour).
e.g. datetime(2021, 10, 4, 8, 0) might return (0,0,0)
"""
def date_to_index(date, time_structure):
    START_SEMESTER_DATE = time_structure.START_SEMESTER_DATE
    hour_to_index = time_structure.hour_to_index
    week = weeks_between(START_SEMESTER_DATE, date) - 1 #-1 because weeks_between is 1-indexed

    day = date.weekday() # in Python 0 is Monday, 6 is Sunday
    hr, mins = str(date.hour), str(date.minute)
    hr = hr if len(hr) == 2 else "0" + hr
    mins = mins if len(mins) == 2 else "0" + mins
    hourmin = hr + ":" + mins

    hour = -1
    if hourmin != "00:00":
        hour = hour_to_index[hourmin]

    return week,day,hour


"""
1) Finds a Monday in the week of "dtstart".
2) Returns a list of 5 datetimes which are:
    Monday, Tuesday, Wednesday, Thursday, Friday
"""
def all_dtstart_weekdays(dtstart, NUM_DAYS):
    monday = (dtstart - timedelta(days=dtstart.weekday()))
    all_weekdays = rrule(dtstart=monday, freq=DAILY, count=NUM_DAYS)
    return list(all_weekdays)


"""
1) Takes an RRULE string
2) Replaces DTSTART with NEW_DTSTART and UNTIL with NEW_UNTIL
3) Extracts RRULE parameters (e.g. freq, interval, wkst, etc...)
4) Creates a new RRULE with same parameters but NEW_DTSTART and NEW_UNTIL
5) Converts all of the RRULE dates to indices (week, day, hour)
6) Returns a list of these indices
"""
def get_rrule_dates(rasp_rrule, NEW_DTSTART, NEW_UNTIL, time_structure):
    old_dtstart_str, old_until_str = None, None
    for line in rasp_rrule.split():
        name, value = line.split(':', 1)
        if name == "DTSTART":
            old_dtstart_str = value
        elif name == "RRULE":
            parms = value.split(";")
            for parm in parms:
                name_,value_ = parm.split("=")
                if name_ == "UNTIL":
                    old_until_str = value_

    new_dtstart_str = NEW_DTSTART.strftime("%Y%m%dT%H%M%S")
    new_until_str   = NEW_UNTIL.strftime("%Y%m%dT%H%M%S")
    rasp_rrule = rasp_rrule.replace(old_dtstart_str, new_dtstart_str)
    rasp_rrule = rasp_rrule.replace(old_until_str, new_until_str)
    rasp_dates = rrulestr(rasp_rrule)

    rasp_dates = tuple(date_to_index(date, time_structure) for date in rasp_dates)
    return rasp_dates


def get_rrule_table_element(rrule_str, dtstart_weekdays, until, time_structure):
    rrule_table_element = {}
    for dtstart in dtstart_weekdays:
        all_dates = list(get_rrule_dates(rrule_str, dtstart, until, time_structure))
        all_dates = [(week, day) for week, day, hour in all_dates]
        key = (all_dates[0][0], all_dates[0][1])
        rrule_table_element[key] = all_dates
    return rrule_table_element

"""
Returns a dictionary rasp_rrules[rasp.id] = rrule_obj and also list rrule_space.
rrule_obj consists of keys ["DTSTART", "UNTIL", "FREQ", "all_dates",
                            "dtstart_weekdays", "rrule_table_index"]

rrule_space holds a list of "rrule_table_element" dictionaries.
rrule_table_element[(week, day)] = all_dates
(week, day) is possible DTSTART of a rasp and all_dates is a list of all rrule
dates starting from (week, day).
The idea is to memoize all of the possible "all_dates" of each rasp in "rrule_space".
"""
def init_rrule_objects(rasps, time_structure):
    NUM_DAYS = time_structure.NUM_DAYS

    rasp_rrules, rrule_table = {}, []
    freqs = {0:"YEARLY", 1:"MONTHLY", 2:"WEEKLY", 3:"DAILY"}
    for rasp in rasps:
        rrule_obj = rrulestr(rasp.rrule)
        dtstart = rrule_obj._dtstart
        until = rrule_obj._until
        dtstart_weekdays = all_dtstart_weekdays(dtstart, NUM_DAYS) if rasp.random_dtstart_weekday else [dtstart]
        rrule_table_element = get_rrule_table_element(rasp.rrule, dtstart_weekdays, until, time_structure)
        if rrule_table_element not in rrule_table:
            rrule_table.append(rrule_table_element)

        dtstart_weekdays = []
        for week, day in rrule_table_element.keys():
            dtstart_weekdays.append((week, day))

        rasp_rrules[rasp.id] = {"DTSTART": None, "UNTIL": None, "FREQ": freqs[rrule_obj._freq],
                                "all_dates":[], "dtstart_weekdays": dtstart_weekdays,
                                "rrule_table_index": rrule_table.index(rrule_table_element)}

    return rasp_rrules, rrule_table
