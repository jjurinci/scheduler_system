import data_api.time_structure as time_api
from datetime import datetime, timedelta

"""
Generates all possible dates from START_SEMESTER_DATE to END_SEMESTER_DATE.
"""
def get_all_possible_dates():
    time_structure = time_api.get_time_structure()
    START_SEMESTER_DATE = time_structure.START_SEMESTER_DATE
    END_SEMESTER_DATE   = time_structure.END_SEMESTER_DATE
    hour_to_index       = time_structure.hour_to_index

    assert START_SEMESTER_DATE < END_SEMESTER_DATE, "START SEMESTER DATE is later than END SEMESTER DATE"

    all_hours = []
    for hourmin in hour_to_index:
        hour, minute = hourmin.split(":")
        hour, minute = int(hour), int(minute)
        all_hours.append((hour, minute))

    all_possible_dates = []
    END_DATE = datetime(END_SEMESTER_DATE.year, END_SEMESTER_DATE.month, END_SEMESTER_DATE.day, 23, 59, 59)
    date = START_SEMESTER_DATE
    while date <= END_DATE:
        for hour, minute in all_hours:
            date_with_hour = datetime(date.year, date.month, date.day, hour, minute)
            all_possible_dates.append(date_with_hour)
        date += timedelta(days=1)

    return all_possible_dates

"""
Testing if "index_to_date(date_to_index(date)) == date"
for all possible dates between START_SEMESTER_DATE and END_SEMESTER_DATE.
"""
def date_conversion_test(all_possible_dates):
    time_structure = time_api.get_time_structure()
    hour_to_index       = time_structure.hour_to_index
    index_to_hour       = time_structure.index_to_hour
    NUM_HOURS           = time_structure.NUM_HOURS

    for date in all_possible_dates:
        week, day, hour = time_api.date_to_index(date, hour_to_index)
        calculated_date  = time_api.index_to_date(week, day, hour, index_to_hour, NUM_HOURS)
        assert date == calculated_date, "date_to_index and index_to_date functions don't work properly."
        date += timedelta(days=1)

"""
Testing if "all_dtstart_weekdays" actually returns dates in correct weekdays:
["monday", "tuesday", "wednesday", "thursday", "friday"]
"""
def all_dtstart_weekdays_test(all_possible_dates):
    convert = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday"}

    for date in all_possible_dates:
        five_dates = time_api.all_dtstart_weekdays(date)
        expected_weekday = 0

        assert len(five_dates) == 5, "Length of all_dtstart_weekdays is not 5."
        for week_date in five_dates:
            actual_weekday = week_date.weekday()
            assert actual_weekday == expected_weekday, f"In all_dtstart_weekdays {week_date} is {convert[actual_weekday]} but expected {convert[expected_weekday]}"
            expected_weekday += 1


"""
Testing if "weeks_between" is actually returning the correct number of weeks between
two dates. "weeks_between" is 1-indexed -> "2021.10.4", "2021.10.4" = 1 week
"""
def weeks_between_test():
    time_structure = time_api.get_time_structure()
    START_SEMESTER_DATE = time_structure.START_SEMESTER_DATE
    END_SEMESTER_DATE   = time_structure.END_SEMESTER_DATE

    date = START_SEMESTER_DATE
    expected_week = 1
    while date <= END_SEMESTER_DATE:
        actual_week = time_api.weeks_between(START_SEMESTER_DATE, date)
        assert expected_week == actual_week, f"Expected week {expected_week} but calculated week is {actual_week} between {START_SEMESTER_DATE} and {date}"
        date += timedelta(days = 7)
        expected_week += 1


def main():
    all_possible_dates = get_all_possible_dates()
    date_conversion_test(all_possible_dates)
    all_dtstart_weekdays_test(all_possible_dates)
    weeks_between_test()

main()
