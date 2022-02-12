import json
from dateutil.rrule import rrulestr, rrule, DAILY
from datetime import datetime, timedelta
from data_api.utilities.my_types import Timeblock, TimeStructure


def get_start_end_semester():
    with open("database/input/start_end_year.json", "r") as fp:
        start_end_year = json.load(fp)["start_end_year"][0]

    start_year = start_end_year["start_year_date"]
    end_year   = start_end_year["end_year_date"]

    day, month, year = list(map(lambda x: int(x), start_year.split(".")))
    start_year = datetime(year, month, day)

    day, month, year = list(map(lambda x: int(x), end_year.split(".")))
    end_year = datetime(year, month, day)

    return start_year, end_year


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


def get_hour_index_structure(timeblocks):
    hourmin_to_index = {}
    index_to_hourmin = {}
    index = 0
    for tblock in timeblocks:
        start_hourmin = tblock.timeblock[:5]
        hourmin_to_index[start_hourmin] = index
        index_to_hourmin[index] = start_hourmin
        index += 1

    return hourmin_to_index, index_to_hourmin


def old_weeks_between(start_date, end_date):
    return (end_date-start_date).days // 7


#1-indexed -> "2021.10.4", "2021.10.4" = 1 week
def weeks_between(start_date, end_date):
    return ((end_date-start_date).days // 7) + 1


def weeks_from_start(date):
    START_SEMESTER_DATE = datetime(2021,10,4)
    return (date - START_SEMESTER_DATE).days // 7


def index_to_date(week, day, hour):
    START_SEMESTER_DATE, _ = get_start_end_semester()
    timeblocks = TIMEBLOCKS
    NUM_HOURS = len(timeblocks)

    index_to_hourmin = INDEX_TO_HOUR_MIN

    # 2 (3rd) week, 1 tuesday, 13 (14th) hour
    hr, mins = 0, 0
    if hour >= 0 and hour < NUM_HOURS:
        hourmin = index_to_hourmin[hour]
        hr, mins = int(hourmin[:2]), int(hourmin[3:5])

    date = START_SEMESTER_DATE.replace(hour = hr, minute = mins)
    week_difference = timedelta(weeks = week)
    date = date + week_difference

    current_weekday = date.weekday()
    day_difference = timedelta(days = day - current_weekday)
    date = date + day_difference

    return date


def date_to_index(date : datetime):
    hourmin_to_index = HOURMIN_TO_INDEX
    week = weeks_from_start(date)

    day = date.weekday() # in Python 0 is Monday, 6 is Sunday
    hr, mins = str(date.hour), str(date.minute)
    hr = hr if len(hr) == 2 else "0" + hr
    mins = mins if len(mins) == 2 else "0" + mins
    hourmin = hr + ":" + mins

    hour = -1
    if hourmin != "00:00":
        hour = hourmin_to_index[hourmin]

    return week,day,hour


def all_dtstart_weekdays(dtstart):
    monday = (dtstart - timedelta(days=dtstart.weekday()))
    all_weekdays = rrule(dtstart=monday, freq=DAILY, count=5)
    return list(all_weekdays)


def get_rrule_until(rasp_rrule):
    if rasp_rrule._until != None:
        return rasp_rrule._until
    else:
        last_date = list(rasp_rrule)[-1]
        return last_date


def get_rrule_dates(rasp_rrule, NEW_DTSTART, NEW_UNTIL):
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

    rasp_dates = tuple(map(date_to_index, rasp_dates))

    return rasp_dates


def init_rrule_objects(rasps):
    rasp_rrules, rrule_space = {}, []
    rrule_space = []
    freqs = {0:"YEARLY", 1:"MONTHLY", 2:"WEEKLY", 3:"DAILY"}
    for rasp in rasps:
        rrule_obj = rrulestr(rasp.rrule)
        dtstart = rrule_obj._dtstart
        until = rrule_obj._until
        dtstart_weekdays = all_dtstart_weekdays(dtstart) if rasp.random_dtstart_weekday else []

        # At most 5 starting days defined by (week, day). Since we don't allow hour manipulation we can leave out the hour (e.g. no (week, day, hour))
        rrule_enumeration = {}
        if rasp.random_dtstart_weekday:
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, _ = date_to_index(dtstart_weekday)
                key = (given_week, given_day)
                all_dates = list(get_rrule_dates(rasp.rrule, dtstart_weekday, until))
                for i, val in enumerate(all_dates):
                    all_dates[i] = (val[0], val[1])
                rrule_enumeration[key] = all_dates

        elif not rasp.random_dtstart_weekday:
            all_dates = list(get_rrule_dates(rasp.rrule, dtstart, until))
            for i, val in enumerate(all_dates):
                all_dates[i] = (val[0], val[1])
            rrule_enumeration[key] = all_dates

        if rrule_enumeration not in rrule_space:
            rrule_space.append(rrule_enumeration)

        dtstart_weekdays = [date_to_index(dtstart_) for dtstart_ in dtstart_weekdays]
        dtstart = date_to_index(dtstart)
        until = date_to_index(until)
        rasp_rrules[rasp.id] = {"DTSTART": dtstart, "UNTIL": until, "FREQ": freqs[rrule_obj._freq],
                                "all_dates":[], "dtstart_weekdays": dtstart_weekdays,
                                "possible_all_dates_idx": rrule_space.index(rrule_enumeration)}

    return rasp_rrules, rrule_space


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


TIMEBLOCKS = get_timeblocks()
HOURMIN_TO_INDEX, INDEX_TO_HOUR_MIN = get_hour_index_structure(TIMEBLOCKS)
