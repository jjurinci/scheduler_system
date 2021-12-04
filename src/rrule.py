import random
import pandas as pd
import numpy as np
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

        self.nasts = seme_api.get_nasts_all_semesters(self.rasps, False)
        self.students = seme_api.get_students_per_rasp_estimate(self.nasts)

        self.starting_rooms = room_api.get_rooms()
        self.room_capacity = room_api.get_rooms_capacity(self.starting_rooms)
        self.computer_rooms = room_api.get_computer_rooms(self.starting_rooms)
        self.rooms_constraints = room_api.get_rooms_constraints()
        self.free_slots = room_api.get_rooms_free_terms(self.NUM_WEEKS, self.NUM_HOURS, self.rooms_constraints, self.starting_rooms)

        self.rooms_occupied = room_api.get_rooms_occupied(self.NUM_WEEKS, self.NUM_HOURS, self.free_slots, self.rasps)
        self.starting_slots = self.generate_starting_slots()

        starting_profs_ids = set(rasp.professorId for rasp in self.rasps)
        self.starting_profs = prof_api.get_professors_by_ids(starting_profs_ids)
        self.profs_constraints = prof_api.get_professors_constraints()
        self.profs_occupied = prof_api.get_professors_occupied(self.NUM_WEEKS, self.NUM_HOURS, self.profs_constraints, self.starting_profs)

        self.rooms_occupied = dict(**self.rooms_occupied)
        self.profs_occupied = dict(**self.profs_occupied)


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
        if hour >= 0 and hour < self.NUM_HOURS:
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
        hr = str(hr) if len(str(hr)) == 2 else "0" + str(hr)
        mins = str(mins) if len(str(mins)) == 2 else "0" + str(mins)
        hourmin = hr + ":" + mins
        hour = self.hourmin_to_index[hourmin]

        return week,day,hour


    def random_sample(self, N):
        sample = []
        for i in range(N):
            print(i)
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
                        print(rasp.subjectId, rasp.type, rasp.group)
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
                if NEW_DTSTART.hour == 0:
                    print("HAS 0 HOUR")
                    print(rasp.subjectId, rasp.type, rasp.group)
                    print(NEW_DTSTART)
                    print(slot)
                    print("\n")

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

            sample.append((self.grade(timetable), timetable))

        return sample


    # TODO: Add more parameters to RRULE later
    def tax_rrule_in_matrix3D(self, matrix3D, rasp):
        #print(rasp.subjectId, rasp.type, rasp.group, rasp.DTSTART, rasp.UNTIL)
        freqs = {"WEEKLY":WEEKLY}
        byweekdays = {"MO":MO, "TU":TU, "WE":WE, "TH":TH, "FR":FR}
        FREQ = freqs[rasp.FREQ]

        BYWEEKDAY = None if not rasp.BYWEEKDAY else [byweekdays[wday] for wday in rasp.BYWEEKDAY]

        rasp_dates = list(rrule(freq = FREQ, interval = rasp.INTERVAL,
                                byweekday = BYWEEKDAY,
                                dtstart = rasp.DTSTART, until = rasp.UNTIL))

        for date in rasp_dates:
            week, day, hour = self.date_to_index(date)
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1


    def count_rrule_in_matrix3D(self, matrix3D, rasp):
        freqs = {"WEEKLY":WEEKLY}
        FREQ = freqs[rasp.FREQ]

        rasp_dates = list(rrule(freq = FREQ, interval = rasp.INTERVAL, byweekday = rasp.BYWEEKDAY,
                          dtstart = rasp.DTSTART, until = rasp.UNTIL))

        count = 0
        for date in rasp_dates:
            week, day, hour = self.date_to_index(date)
            count += sum(matrix3D[week, day, hour:(hour + rasp.duration)] > 1)

        return count


    def grade(self, timetable):
        rooms_occupied = {k:v.copy() for k,v in self.rooms_occupied.items()}
        profs_occupied = {k:v.copy() for k,v in self.profs_occupied.items()}

        for rasp, (room_id, week, day, hour) in timetable.items():
            self.tax_rrule_in_matrix3D(rooms_occupied[room_id], rasp)
            self.tax_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp)

        total_score = 0
        total_room_score, total_professor_score = 0, 0
        total_capacity_score, total_computers_score = 0, 0
        for rasp, (room_id, week, day, hour) in timetable.items():

            # Room collisions
            cnt = self.count_rrule_in_matrix3D(rooms_occupied[room_id], rasp)
            score_rooms = cnt * self.students[rasp.id]
            total_room_score -= score_rooms
            total_score -= score_rooms

            # Professor collisions
            cnt = self.count_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp)
            score_professors = cnt * self.students[rasp.id]
            total_professor_score -= score_professors
            total_score -= score_professors

            # Insufficient room capacity
            capacity = bool(self.students[rasp.id] - self.room_capacity[room_id]>=0)
            score_capacity = capacity * rasp.duration * self.students[rasp.id]
            total_capacity_score -= score_capacity
            total_score -= score_capacity

            # Computer room & computer rasp collisions
            if not room_id in self.computer_rooms and rasp.needsComputers:
                score_computers = self.students[rasp.id]
                total_computers_score -= score_computers
                total_score -= score_computers

            if room_id in self.computer_rooms and not rasp.needsComputers:
                score_computers = self.students[rasp.id] * 0.1
                total_computers_score -= score_computers
                total_score -= score_computers

        #TODO: Optimize, it's quite slow
        # Nast collisions
        total_nast_score = 0
        #for semester, the_nasts in self.nasts.items():
        #    score_nasts = 0
        #    for nast in the_nasts:
        #        nast_occupied =  np.zeros((self.NUM_WEEKS,5,self.NUM_HOURS), dtype=np.uint8)
        #        for rasp in nast:
        #            rasp = next(r for r in timetable.keys() if rasp.id == r.id)
        #            room_id, week, day, hour = timetable[rasp]
        #            self.tax_rrule_in_matrix3D(nast_occupied, rasp)
        #        for rasp in nast:
        #            rasp = next(r for r in timetable.keys() if rasp.id == r.id)
        #            room_id, week, day, hour = timetable[rasp]
        #            cnt = self.count_rrule_in_matrix3D(nast_occupied, rasp)
        #            score_nasts += cnt * self.students[rasp.id]
        #    total_nast_score -= score_nasts
        #    total_score -= score_nasts

        final_score = {
                "totalScore": total_score,
                "roomScore": total_room_score,
                "professorScore": total_professor_score,
                "capacityScore": total_capacity_score,
                "computerScore": total_computers_score,
                "nastScore": total_nast_score
        }

        return final_score


    def mutate(self, timetable):
        new_timetable = timetable.copy()
        rasp0 = random.choice(list(new_timetable.keys()))
        old_slot = new_timetable[rasp0]

        new_timetable.pop(rasp0, 0)
        avs_pool = self.starting_slots.copy()

        week, day, hour = -1, -1, -1
        #case: has no DTSTART
        DTSTART = rasp0.DTSTART
        if not DTSTART:
            pass

        #case: has DTSTART without hour
        elif DTSTART and not DTSTART.hour:
            pass
            #week, day, _ = self.date_to_index(DTSTART)
            #avs_pool = {slot for slot in self.free_slots if slot.week == week and slot.day == day} #TODO: Optimize

        #case: has DTSTART and hour (care! -> random_sample sets DTSTART with hour) TODO: Check if FIXED DTSTART with hour
        elif DTSTART and DTSTART.hour:
            pass
            #week, day, hour = self.date_to_index(DTSTART)
            #avs_pool = {slot for slot in self.free_slots if slot.week == week and slot.day == day and slot.hour == hour}

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
            print("nothing")
            print(len(self.starting_slots))
            print(week, day, hour)
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
        BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        for generation in tqdm(range(starting_generation, starting_generation+generations)):
            try:
                original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
                with Pool(7) as p:
                    signal.signal(signal.SIGINT, original_sigint_handler)

                    the_samples = [s[1] for s in sample]

                    mutations = p.map_async(self.mutate_and_grade, the_samples)
                    mutations.wait()

                sample += mutations.get()
                sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
                sample = sample[0:population_cap]
                if sample[0][0]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

            except KeyboardInterrupt:
                return sample

        return sample


o = Optimizer()
sample = o.random_sample(5)
o.iterate(sample, population_cap=5)
