import pandas as pd
from dateutil.rrule import rrule, WEEKLY
from datetime import datetime, timedelta


def get_start_end_semester():
    return datetime(2021,10,4), datetime(2022,1,28)


def get_day_structure():
    path = "database/input/csvs/day_structure.csv"
    with open(path) as csv_file:
        day_structure = pd.read_csv(csv_file,
                                    delimiter=",",
                                    usecols=[0,1])

        day_structure = pd.DataFrame(day_structure).astype("str")

    return day_structure


def get_hour_index_structure(day_structure):
    hourmin_to_index = {}
    index_to_hourmin = {}
    index = 0
    for timeblock in day_structure["timeblock"]:
        start_hourmin = timeblock[:5]
        hourmin_to_index[start_hourmin] = index
        index_to_hourmin[index] = start_hourmin
        index += 1

    return hourmin_to_index, index_to_hourmin


def old_weeks_between(start_date, end_date):
    weeks = rrule(WEEKLY, dtstart=start_date, until=end_date, cache=True)
    return weeks.count()


def weeks_between(start_date, end_date):
    days = abs(start_date-end_date).days
    return days // 7


def index_to_date(week, day, hour):
    START_SEMESTER_DATE, _ = get_start_end_semester()
    day_structure = DAY_STRUCTURE
    NUM_HOURS = len(day_structure)

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
    START_SEMESTER_DATE, _ = get_start_end_semester()
    hourmin_to_index = HOURMIN_TO_INDEX

    week = weeks_between(START_SEMESTER_DATE, date)

    day = date.weekday() # in Python 0 is Monday, 6 is Sunday
    hr, mins = date.hour, date.minute
    hour = None
    hr = str(hr) if len(str(hr)) == 2 else "0" + str(hr)
    mins = str(mins) if len(str(mins)) == 2 else "0" + str(mins)
    hourmin = hr + ":" + mins
    hour = hourmin_to_index[hourmin]

    return week,day,hour


DAY_STRUCTURE = get_day_structure()
HOURMIN_TO_INDEX, INDEX_TO_HOUR_MIN = get_hour_index_structure(DAY_STRUCTURE)
