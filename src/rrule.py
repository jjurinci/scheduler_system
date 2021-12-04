import random
import pandas as pd
from tqdm import tqdm
import signal
from collections import defaultdict
from itertools import product
from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MO, TU, WE, TH, FR
from multiprocessing import Pool
import data_api.classrooms as room_api
import data_api.professors as prof_api
import data_api.rasps      as rasp_api
import data_api.semesters  as seme_api
from data_api.utilities.my_types import Rasp, Slot

class Optimizer:
    def __init__(self):
        self.START_SEMESTER_DATE = datetime(2021, 10, 4)
        self.END_SEMESTER_DATE = datetime(2022, 1, 28)
        self.NUM_WEEKS = self.__weeks_between(self.START_SEMESTER_DATE, self.END_SEMESTER_DATE)

        self.day_structure = self.get_day_structure()
        self.hourmin_to_index = {}
        self.index_to_hourmin = {}
        index = 0
        for timeblock in self.day_structure["timeblock"]:
            start_hourmin = timeblock[:5]
            self.hourmin_to_index[start_hourmin] = index
            self.index_to_hourmin[index] = start_hourmin
            index += 1

        self.NUM_HOURS = len(self.day_structure)

        self.winter = False
        self.rasps = rasp_api.get_rasps_by_season(winter = self.winter)

        self.starting_rooms = room_api.get_rooms()
        self.rooms_constraints = room_api.get_rooms_constraints()
        self.free_slots = room_api.get_rooms_free_terms(self.NUM_WEEKS, self.NUM_HOURS, self.rooms_constraints, self.starting_rooms)

        self.rooms_occupied = room_api.get_rooms_occupied2(self.NUM_WEEKS, self.NUM_HOURS, self.free_slots, self.rasps)
        self.starting_slots = self.generate_starting_slots()

        starting_profs_ids = set(rasp.professorId for rasp in self.rasps)
        self.starting_profs = prof_api.get_professors_by_ids(starting_profs_ids)
        self.profs_constraints = prof_api.get_professors_constraints()
        self.profs_occupied = prof_api.get_professors_occupied(self.NUM_WEEKS, self.NUM_HOURS, self.profs_constraints, self.starting_profs)


    def __weeks_between(self, start_date, end_date):
        weeks = rrule(WEEKLY, dtstart=start_date, until=end_date)
        return weeks.count()


    def get_day_structure(self):
        path = "database/input/csvs/day_structure.csv"
        with open(path) as csv_file:
            day_structure = pd.read_csv(csv_file,
                                        delimiter=",",
                                        usecols=[0,1])

            day_structure = pd.DataFrame(day_structure).astype("str")

        return day_structure


    def generate_starting_slots(self):
        starting_slots = set()
        for room_id in self.rooms_occupied:
            for day in range(5):
                for hour in range(self.NUM_HOURS):
                    if self.rooms_occupied[room_id][0][day][hour] == 0:
                        starting_slots.add(Slot(room_id, 0, day, hour))
        return starting_slots


    def index_to_date(self, week, day, hour):
        # 2 (3rd) week, 1 tuesday, 13 (14th) hour
        hr, mins = 0, 0
        if hour:
            hourmin = self.index_to_hourmin[hour]
            hr, mins = int(hourmin[:2]), int(hourmin[3:5])

        date = self.START_SEMESTER_DATE.replace(hour = hr, minute = mins)
        week_difference = timedelta(weeks = week)
        date = date + week_difference

        current_weekday = date.weekday()
        day_difference = timedelta(days = day - current_weekday)
        date = date + day_difference

        return date


    def date_to_index(self, date : datetime):
        week = self.__weeks_between(self.START_SEMESTER_DATE, date) - 1 # -1 coz we want 0 based indexes
        day = date.weekday() # in Python 0 is Monday, 6 is Sunday
        hr, mins = date.hour, date.minute
        hour = None
        if hr:
            hr = str(hr) if len(str(hr)) == 2 else "0" + str(hr)
            mins = str(mins) if len(str(mins)) == 2 else "0" + str(mins)
            hourmin = hr + ":" + mins
            hour = self.hourmin_to_index[hourmin]

        return week,day,hour


    def random_sample(self, N):
        sample = []
        for i in range(N):
            all_avs = self.free_slots.copy()
            first_week_avs = self.starting_slots.copy()
            timetable = {}
            for rasp in self.rasps:
                slot = None
                while not slot:
                    avs_pool = first_week_avs

                    DTSTART = rasp.DTSTART
                    #case: NO DTSTART -> random (room_id, 0, day, hour)
                    if not DTSTART:
                        avs_pool = first_week_avs

                    #case: has DTSTART without hour -> random (room_id, _given_week, _given_day, hour)
                    elif DTSTART and not DTSTART.hour:
                        given_week, given_day, _ = self.date_to_index(rasp.DTSTART)
                        avs_pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day)

                    #case: has DTSTART wit hour -> random(room_id, _given_week, _given_day, _given_hour)
                    elif DTSTART and DTSTART.hour:
                        print(rasp.subjectId, rasp.type, rasp.group)
                        given_week, given_day, given_hour = self.date_to_index(rasp.DTSTART)
                        avs_pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour)

                    try_slot = random.choice(tuple(avs_pool))

                    if try_slot.hour + rasp.duration < self.NUM_HOURS:
                        slot = try_slot

                NEW_DTSTART = self.index_to_date(slot.week, slot.day, slot.hour)
                NEW_UNTIL = rasp.UNTIL

                #case has no UNTIL:
                if not NEW_UNTIL:
                    NEW_UNTIL = self.index_to_date(self.NUM_WEEKS-1, 4, slot.hour) #last week, last day, DTSTART.hour

                #case has UNTIL without hour OR has UNTIL with hour:
                elif NEW_UNTIL:
                    until_week, until_day, _ = self.date_to_index(NEW_UNTIL)
                    NEW_UNTIL = self.index_to_date(until_week, until_day, slot.hour)

                # Remove if they exit
                all_avs.discard(slot)
                first_week_avs.discard(slot)

                timetable.pop(rasp, 0)
                rasp = rasp._replace(DTSTART=NEW_DTSTART, UNTIL=NEW_UNTIL)

                timetable[rasp] = slot

            sample.append(timetable)

        return sample


    def grade(self, timetable):
        pass


    def mutate(self, timetable):
        new_timetable = timetable.copy()
        rasp0 = random.choice(list(new_timetable.keys()))
        old_slot = new_timetable[rasp0]

        new_timetable.pop(rasp0, 0)
        avs_pool = self.starting_slots.copy()

        #case: has no DTSTART
        DTSTART = rasp0.DTSTART
        if not DTSTART:
            pass

        #case: has DTSTART without hour
        elif DTSTART and not DTSTART.hour:
            week, day, _ = self.date_to_index(DTSTART)
            avs_pool = {slot for slot in self.free_slots if slot.week == week and slot.day == day} #TODO: Optimize

        #case: has DTSTART and hour
        elif DTSTART and DTSTART.hour:
            week, day, hour = self.date_to_index(DTSTART)
            avs_pool = {slot for slot in self.free_slots if slot.week == week and slot.day == day and slot.hour == hour}

        taken_terms = set()
        for rasp, (room_id, week, day, hour) in timetable.items():
            taken_terms |= {(room_id, week, day, hour+i) for i in range(rasp.duration)}
        avs_pool -= taken_terms

        nonavs = set()
        for (room_id, week, day, hour) in avs_pool:
            if any((room_id, week, day, hour+i) not in avs_pool for i in range(1, rasp0.duration)):
                nonavs.add((room_id, week, day, hour))
        avs_pool -= nonavs

        if not avs_pool:
            new_timetable[rasp0] = old_slot
            return new_timetable

        slot = random.choice(list(avs_pool))

        NEW_DTSTART = self.index_to_date(slot.week, slot.day, slot.hour)

        #case: has no UNTIL
        NEW_UNTIL = rasp0.UNTIL
        if not NEW_UNTIL:
            NEW_UNTIL = self.index_to_date(self.NUM_WEEKS-1, 4, slot.hour)
        elif NEW_UNTIL:
            until_week, until_day, _ = self.date_to_index(NEW_UNTIL)
            NEW_UNTIL = self.index_to_date(until_week, until_day, slot.hour)

        rasp0 = rasp0._replace(DTSTART = NEW_DTSTART, UNTIL = NEW_UNTIL)
        new_timetable[rasp0] = slot
        return new_timetable


    def mutate_and_grade(self, timetable):
        timetable = self.mutate(timetable)
        return self.grade(timetable), timetable


    def iterate(self, sample, generations=100, starting_generation=1, population_cap=512):
        pass


o = Optimizer()
sample = o.random_sample(10)
print(len(sample[0]))

timetable = sample[3]

mutated = o.mutate(timetable)
print(len(mutated))
print(mutated)

