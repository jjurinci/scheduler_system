from datetime import datetime
from dateutil.rrule import rrule, WEEKLY, DAILY, MO, TU, WE, TH, FR

START_SEMESTER = datetime(2021,10,4)
END_SEMESTER = datetime(2022,1,28)
weekly = rrule(freq=WEEKLY, dtstart=START_SEMESTER, until=END_SEMESTER)

START_SEMESTER = datetime(2021,10,4, 8,0)
END_SEMESTER = datetime(2022,1,28, 8,0)
weekly_8 = rrule(freq=WEEKLY, dtstart=START_SEMESTER, until=END_SEMESTER)

START_SEMESTER = datetime(2021,10,4, 11,20)
END_SEMESTER = datetime(2022,1,28, 11,20)
weekly_11_20 = rrule(freq=WEEKLY, dtstart=START_SEMESTER, until=END_SEMESTER)

START_SEMESTER = datetime(2021,10,4)
END_SEMESTER = datetime(2022,1,28)
biweekly = rrule(freq=WEEKLY, interval=2, dtstart=START_SEMESTER, until=END_SEMESTER)

start = datetime(2021,11,11)
end = datetime(2021,12,11)
custom1 = rrule(freq=DAILY, byweekday=[MO, TU, WE, TH, FR], dtstart=start, until=end)

start = datetime(2022,1,5)
end = datetime(2022,1,17)
custom2 = rrule(freq=DAILY, byweekday=[MO, TU, WE, TH, FR], dtstart=start, until=end)

print(f"{str(weekly)=}")
print(f"{str(weekly_8)=}")
print(f"{str(weekly_11_20)=}")
print(f"{str(biweekly)=}")
print(f"{str(custom1)=}")
print(f"{str(custom2)=}")
