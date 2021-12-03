import random
import pandas as pd
from tqdm import tqdm
import signal
from collections import defaultdict
from itertools import product
from datetime import datetime
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

        self.rasp_dtstart = defaultdict(lambda: None)
        self.rasp_until= defaultdict(lambda: None)
        for rasp in self.rasps:
            self.rasp_dtstart[rasp.id] = rasp.DTSTART
            self.rasp_until[rasp.id] = rasp.UNTIL


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
        return datetime.now()


    def date_to_index(self, date):
        return (1,2,3)


    def update_rasp_rrule(self, rasp_id, NEW_DTSTART, NEW_UNTIL):
        self.rasp_dtstart[rasp_id] = NEW_DTSTART
        self.rasp_until[rasp_id] = NEW_UNTIL


    def random_sample(self, N):
        sample = []
        for _ in range(N):
            all_avs = self.free_slots.copy()
            first_week_avs = self.starting_slots.copy()
            rasp_dtstart = self.rasp_dtstart.copy()
            rasp_until = self.rasp_until.copy()
            timetable = {}
            for rasp in self.rasps:
                slot = None
                while not slot:
                    avs_pool = first_week_avs

                    DTSTART = rasp_dtstart[rasp.id]
                    #case: NO DTSTART -> random (room_id, 0, day, hour)
                    if not DTSTART:
                        avs_pool = first_week_avs

                    #case: has DTSTART without hour -> random (room_id, _given_week, _given_day, hour)
                    elif DTSTART and not DTSTART.hour:
                        given_week, given_day, _ = self.date_to_index(rasp.DTSTART)
                        avs_pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day)

                    #case: has DTSTART wit hour -> random(room_id, _given_week, _given_day, _given_hour)
                    elif DTSTART and DTSTART.hour:
                        given_week, given_day, given_hour = self.date_to_index(rasp.DTSTART)
                        avs_pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour)

                    try_slot = random.choice(tuple(avs_pool))

                    if try_slot.hour + rasp.duration < self.NUM_HOURS:
                        slot = try_slot

                NEW_DTSTART = self.index_to_date(slot.week, slot.day, slot.hour)

                UNTIL = rasp_until[rasp.id]
                NEW_UNTIL = None

                #case has no UNTIL:
                if not UNTIL:
                    NEW_UNTIL = self.index_to_date(self.NUM_WEEKS-1, 4, NEW_DTSTART.hour) #last week, last day, DTSTART.hour

                #case has UNTIL without hour OR has UNTIL with hour:
                elif UNTIL:
                    until_week, until_day, _ = self.date_to_index(UNTIL)
                    NEW_UNTIL = self.index_to_date(until_week, until_day, NEW_DTSTART.hour)

                # Remove if they exit
                all_avs.discard(slot)
                first_week_avs.discard(slot)

                #self.update_rasp_rrule(rasp.id, NEW_DTSTART, NEW_UNTIL)
                timetable[rasp] = slot

            sample.append(timetable)

        return sample


    def grade(self, timetable):
        pass


    def mutate(self, timetable):
        new_timetable = timetable.copy()
        rasp0 = random.choice(self.rasps)
        new_timetable.pop(rasp0, 0)

        avs_pool = self.starting_slots.copy()

        #case: has no DTSTART
        DTSTART = self.rasp_dtstart[rasp0.id]
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

        slot = random.choice(list(avs_pool))
        new_timetable[rasp0] = slot

        NEW_DTSTART = self.index_to_date(slot.week, slot.day, slot.hour)

        #case: has no UNTIL
        UNTIL = self.rasp_until[rasp0.id]
        NEW_UNTIL = None
        if not UNTIL:
            NEW_UNTIL = self.index_to_date(self.NUM_WEEKS-1, 4, slot.hour)
        elif UNTIL:
            until_week, until_day, _ = self.date_to_index(UNTIL)
            NEW_UNTIL = self.index_to_date(until_week, until_day, NEW_DTSTART.hour)

        #self.update_rasp_rrule(rasp0.id, NEW_DTSTART, NEW_UNTIL)
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
