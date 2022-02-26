import json
from dateutil.rrule import rrulestr, rrule, DAILY
from datetime import datetime, timedelta
from utilities.my_types import Timeblock, TimeStructure

"""
Returns two dates:
START_SEMESTER_DATE = date when the semester begins.
END_SEMESTER_DATE   = date when the semester ends.
"""
def get_start_end_semester():
    with open("database/input/start_end_year.json", "r") as fp:
        start_end_year = json.load(fp)["start_end_year"][0]

    START_SEMESTER_DATE = start_end_year["start_year_date"]
    END_SEMESTER_DATE   = start_end_year["end_year_date"]

    day, month, year = list(map(lambda x: int(x), START_SEMESTER_DATE.split(".")))
    START_SEMESTER_DATE = datetime(year, month, day)

    day, month, year = list(map(lambda x: int(x), END_SEMESTER_DATE.split(".")))
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
    with open("database/input/day_structure.json", "r") as fp:
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
    START_SEMESTER_DATE, END_SEMESTER_DATE = get_start_end_semester()
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
def index_to_date(week: int, day: int, hour: int, index_to_hour: dict, NUM_HOURS: int):
    #START_SEMESTER_DATE, _ = get_start_end_semester()

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
def date_to_index(date : datetime, hour_to_index: dict):
    #START_SEMESTER_DATE, _ = get_start_end_semester()
    week = weeks_between(START_SEMESTER_DATE, date) - 1 #-1 because weeks_between is 1-indexed
    #week = weeks_from_start(START_SEMESTER_DATE, date)

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
def all_dtstart_weekdays(dtstart):
    monday = (dtstart - timedelta(days=dtstart.weekday()))
    all_weekdays = rrule(dtstart=monday, freq=DAILY, count=5)
    return list(all_weekdays)


"""
1) Takes an RRULE string
2) Replaces DTSTART with NEW_DTSTART and UNTIL with NEW_UNTIL
3) Extracts RRULE parameters (e.g. freq, interval, wkst, etc...)
4) Creates a new RRULE with same parameters but NEW_DTSTART and NEW_UNTIL
5) Converts all of the RRULE dates to indices (week, day, hour)
6) Returns a list of these indices
"""
def get_rrule_dates(rasp_rrule, NEW_DTSTART, NEW_UNTIL, hour_to_index):
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

    rasp_rrule = rrulestr(rasp_rrule)
    freq = rasp_rrule._freq
    interval = rasp_rrule._interval
    wkst = rasp_rrule._wkst
    bymonth = rasp_rrule._bymonth
    bymonthday = rasp_rrule._bymonthday
    byyearday = rasp_rrule._byyearday
    byweekno = rasp_rrule._byweekno
    byweekday = rasp_rrule._byweekday

    rasp_dates = rrule(dtstart = NEW_DTSTART, until = NEW_UNTIL,
                       freq = freq, interval = interval, wkst = wkst,
                       bymonth = bymonth, bymonthday = bymonthday,
                       byyearday = byyearday, byweekno = byweekno,
                       byweekday = byweekday)

    rasp_dates = tuple(date_to_index(date, hour_to_index) for date in rasp_dates)
    return rasp_dates


"""
Returns a dictionary rasp_rrules[rasp.id] = rrule_obj and also list rrule_space.
rrule_obj consists of keys ["DTSTART", "UNTIL", "FREQ", "all_dates",
                            "dtstart_weekdays", "possible_all_dates_idx"]

rrule_space holds a list of "rrule_enumeration" dictionaries.
rrule_enumeration[(week, day)] = all_dates
(week, day) is possible DTSTART of a rasp and all_dates is a list of all rrule
dates starting from (week, day).
The idea is to memoize all of the possible "all_dates" of each rasp in "rrule_space".
"""
def init_rrule_objects(rasps, time_structure):
    hour_to_index = time_structure.hour_to_index

    rasp_rrules, rrule_space = {}, []
    rrule_space = []
    freqs = {0:"YEARLY", 1:"MONTHLY", 2:"WEEKLY", 3:"DAILY"}
    for rasp in rasps:
        rrule_obj = rrulestr(rasp.rrule)
        dtstart = rrule_obj._dtstart
        until = rrule_obj._until
        dtstart_weekdays = all_dtstart_weekdays(dtstart) if rasp.random_dtstart_weekday else []

        # At most 5 starting days defined by (week, day).
        # Since we don't allow hour manipulation we can leave out the hour (e.g. no (week, day, hour))
        rrule_enumeration = {}
        if rasp.random_dtstart_weekday:
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, _ = date_to_index(dtstart_weekday, hour_to_index)
                key = (given_week, given_day)
                all_dates = list(get_rrule_dates(rasp.rrule, dtstart_weekday, until, hour_to_index))
                for i, val in enumerate(all_dates):
                    all_dates[i] = (val[0], val[1])
                rrule_enumeration[key] = all_dates

        elif not rasp.random_dtstart_weekday:
            all_dates = list(get_rrule_dates(rasp.rrule, dtstart, until, hour_to_index))
            for i, val in enumerate(all_dates):
                all_dates[i] = (val[0], val[1])
            rrule_enumeration[key] = all_dates

        if rrule_enumeration not in rrule_space:
            rrule_space.append(rrule_enumeration)

        dtstart_weekdays = [date_to_index(dtstart_, hour_to_index) for dtstart_ in dtstart_weekdays]
        dtstart = date_to_index(dtstart, hour_to_index)
        until = date_to_index(until, hour_to_index)
        rasp_rrules[rasp.id] = {"DTSTART": dtstart, "UNTIL": until, "FREQ": freqs[rrule_obj._freq],
                                "all_dates":[], "dtstart_weekdays": dtstart_weekdays,
                                "possible_all_dates_idx": rrule_space.index(rrule_enumeration)}

    return rasp_rrules, rrule_space

START_SEMESTER_DATE, END_SEMESTER_DATE = get_start_end_semester()
