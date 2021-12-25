import json
import pandas as pd
from dateutil.rrule import rrulestr, rrule, DAILY
from datetime import datetime, timedelta
from data_api.utilities.my_types import Timeblock


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


def get_day_structure():
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


TIMEBLOCKS = get_day_structure()
HOURMIN_TO_INDEX, INDEX_TO_HOUR_MIN = get_hour_index_structure(TIMEBLOCKS)
