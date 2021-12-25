import sys
import random
import numpy as np
from tqdm import tqdm
import signal
from collections import defaultdict
from dateutil.rrule import rrulestr
from multiprocessing import Pool
import data_api.time_structure as time_api

class Optimizer:
    def get_size(self, obj, seen=None):
        """Recursively finds size of objects"""
        size = sys.getsizeof(obj)
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        # Important mark as seen *before* entering recursion to gracefully handle
        # self-referential objects
        seen.add(obj_id)
        if isinstance(obj, dict):
            size += sum([self.get_size(v, seen) for v in obj.values()])
            size += sum([self.get_size(k, seen) for k in obj.keys()])
        elif hasattr(obj, '__dict__'):
            size += self.get_size(obj.__dict__, seen)
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            size += sum([self.get_size(i, seen) for i in obj])
        return size


    def __init__(self, data):
        self.NUM_WEEKS = data["NUM_WEEKS"]
        self.NUM_HOURS = data["NUM_HOURS"]
        self.rasps = data["rasps"]
        self.nasts = data["nasts"]
        self.students_estimate = data["students_estimate"]
        self.room_capacity = data["room_capacity"]
        self.computer_rooms = data["computer_rooms"]
        self.free_slots = data["free_slots"]
        self.starting_slots = data["starting_slots"]
        self.rooms_occupied = dict(**data["rooms_occupied"])
        self.profs_occupied = dict(**data["profs_occupied"])


    def random_sample(self, N):
        sample = []
        for i in range(N):
            print(i)
            all_avs = self.free_slots.copy()
            timetable, rasp_rrules = {}, {}

            for rasp in self.rasps:
                rrule_obj = rrulestr(rasp.rrule)
                dtstart = rrule_obj._dtstart
                until = rrule_obj._until
                dtstart_weekdays = time_api.all_dtstart_weekdays(dtstart) if rasp.random_dtstart_weekday else []
                rasp_rrules[rasp.id] = {"DTSTART": dtstart, "UNTIL": until, "dtstart_weekdays":dtstart_weekdays, "all_dates":[]}

            for rasp in self.rasps:
                slot = None
                while not slot:
                    pool = set()
                    # Starting day is a random weekday AND hour is a random hour
                    DTSTART = rasp_rrules[rasp.id]["DTSTART"]

                    if rasp.random_dtstart_weekday and not rasp.fixed_hour:
                        dtstart_weekdays = rasp_rrules[rasp.id]["dtstart_weekdays"]
                        for dtstart_weekday in dtstart_weekdays:
                            given_week, given_day, _ = time_api.date_to_index(dtstart_weekday)
                            pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day)

                    elif rasp.random_dtstart_weekday and rasp.fixed_hour:
                        dtstart_weekdays = rasp_rrules[rasp.id]["dtstart_weekdays"]
                        for dtstart_weekday in dtstart_weekdays:
                            given_week, given_day, given_hour = time_api.date_to_index(dtstart_weekday)
                            pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour)

                    elif not rasp.random_dtstart_weekday and not rasp.fixed_hour:
                        given_week, given_day, _ = time_api.date_to_index(DTSTART)
                        pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day)

                    elif not rasp.random_dtstart_weekday and rasp.fixed_hour:
                        given_week, given_day, given_hour = time_api.date_to_index(DTSTART)
                        pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour)

                    try_slot = random.choice(tuple(pool))

                    if try_slot.hour + rasp.duration < self.NUM_HOURS:
                        slot = try_slot

                NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
                NEW_UNTIL = rasp_rrules[rasp.id]["UNTIL"]
                until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
                NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

                # Remove if they exit
                all_avs.remove(slot)

                rasp_rrules[rasp.id]["DTSTART"] = NEW_DTSTART
                rasp_rrules[rasp.id]["UNTIL"] = NEW_UNTIL
                rasp_rrules[rasp.id]["all_dates"] = time_api.get_rrule_dates(rasp.rrule, NEW_DTSTART, NEW_UNTIL)
                timetable[rasp] = slot

            sample.append((self.grade((timetable, rasp_rrules)), timetable, rasp_rrules))

        return sample


    def nast_tax_rrule_optional_rasp(self, optionals_occupied, nast_occupied, rasp, hour, rrule_dates):
        for hr in range(hour, hour + rasp.duration):
            for week, day, _ in rrule_dates:
                if optionals_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] += 1
        self.tax_rrule_in_matrix3D(optionals_occupied, rasp, rrule_dates)


    def tax_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1


    def count_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        return sum(np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>1)
                   for week, day, hour in rrule_dates)


    def grade(self, timetable):
        timetable, rasp_rrules = timetable[0], timetable[1]
        rooms_occupied = {k:v.copy() for k,v in self.rooms_occupied.items()}
        profs_occupied = {k:v.copy() for k,v in self.profs_occupied.items()}

        #for rasp, (room_id, _, _, hour) in timetable.items():
        #    print(rasp)
        #    print(room_id, rasp_rrules[rasp.id]["all_dates"])
        #quit()

        for rasp, (room_id, _, _, hour) in timetable.items():
            self.tax_rrule_in_matrix3D(rooms_occupied[room_id], rasp, rasp_rrules[rasp.id]["all_dates"])
            self.tax_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp, rasp_rrules[rasp.id]["all_dates"])

        total_score = 0
        total_room_score, total_professor_score = 0, 0
        total_capacity_score, total_computers_score = 0, 0
        for rasp, (room_id, _, _, hour) in timetable.items():

            # Room collisions
            cnt = self.count_rrule_in_matrix3D(rooms_occupied[room_id], rasp, rasp_rrules[rasp.id]["all_dates"])
            score_rooms = cnt * self.students_estimate[rasp.id]
            total_room_score -= score_rooms
            total_score -= score_rooms

            # Professor collisions
            cnt = self.count_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp, rasp_rrules[rasp.id]["all_dates"])
            score_professors = cnt * self.students_estimate[rasp.id]
            total_professor_score -= score_professors
            total_score -= score_professors

            # Insufficient room capacity
            capacity = bool(self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0)
            score_capacity = capacity * rasp.duration * self.students_estimate[rasp.id]
            total_capacity_score -= score_capacity
            total_score -= score_capacity

            # Computer room & computer rasp collisions
            if not room_id in self.computer_rooms and rasp.needsComputers:
                score_computers = self.students_estimate[rasp.id]
                total_computers_score -= score_computers
                total_score -= score_computers

            if room_id in self.computer_rooms and not rasp.needsComputers:
                score_computers = self.students_estimate[rasp.id] * 0.1
                total_computers_score -= score_computers
                total_score -= score_computers

        # Nast collisions
        total_nast_score = 0
        nasts_occupied = defaultdict(lambda: np.zeros((self.NUM_WEEKS, 5, self.NUM_HOURS), dtype=np.uint8))
        for semester, the_nasts in self.nasts.items():
            sem_id, _, _, _ = semester
            score_nasts = 0

            NUM_OPTIONALS_ALLOWED = 1
            PARALLEL_OPTIONALS_ALLOWED = True if NUM_OPTIONALS_ALLOWED == 1 else False

            seen_rasps = set()
            taxed_rasps = set()
            optionals_occupied = np.zeros((self.NUM_WEEKS, 5, self.NUM_HOURS), dtype=np.uint8)
            for nast in the_nasts:
                for rasp in nast:
                    if rasp.id in seen_rasps:
                        continue
                    seen_rasps.add(rasp.id)

                    room_id, _, _, hour = timetable[rasp]

                    rasp_mandatory = True if sem_id in rasp.mandatory_in_semesterIds else False

                    if rasp_mandatory or not PARALLEL_OPTIONALS_ALLOWED:
                        self.tax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp, rasp_rrules[rasp.id]["all_dates"])
                    else:
                        self.nast_tax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp, hour, rasp_rrules[rasp.id]["all_dates"])

                for rasp in nast:
                    if rasp.id in taxed_rasps:
                        continue
                    taxed_rasps.add(rasp.id)
                    room_id, _, _, hour = timetable[rasp]
                    cnt = self.count_rrule_in_matrix3D(nasts_occupied[sem_id], rasp, rasp_rrules[rasp.id]["all_dates"])
                    score_nasts += cnt * self.students_estimate[rasp.id]

            total_nast_score -= score_nasts
            total_score -= score_nasts

        final_score = {
                "totalScore": round(total_score,2),
                "roomScore": round(total_room_score, 2),
                "professorScore": round(total_professor_score,2),
                "capacityScore": round(total_capacity_score,2),
                "computerScore": round(total_computers_score,2),
                "nastScore": round(total_nast_score,2)
        }

        #print("Constraints size: ",(self.get_size(profs_occupied) + self.get_size(rooms_occupied) + self.get_size(nasts_occupied))/10**6, "MB.")

        return final_score


    def mutate(self, timetable):
        old_timetable = timetable[0]
        new_timetable, rasp_rrules = timetable[0].copy(), timetable[1]

        rasp0 = random.choice(list(new_timetable.keys()))
        old_slot = new_timetable[rasp0]

        new_timetable.pop(rasp0, 0)
        all_avs = self.free_slots.copy()

        taken_terms = set()
        for rasp, (room_id, _, _, _) in old_timetable.items():
            for week, day, hour in rasp_rrules[rasp.id]["all_dates"]:
                taken_terms |= {(room_id, week, day, hour+i) for i in range(rasp.duration)}
        all_avs -= taken_terms

        nonavs = set()
        for (room_id, week, day, hour) in all_avs:
            if any((room_id, week, day, hour+i) not in all_avs for i in range(1, rasp0.duration)):
                nonavs.add((room_id, week, day, hour))
        all_avs -= nonavs

        pool = set()
        if rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, _ = time_api.date_to_index(dtstart_weekday)
                pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and rasp0.duration + slot.hour < self.NUM_HOURS)

        elif rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, given_hour = time_api.date_to_index(dtstart_weekday)
                pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour and rasp0.duration + slot.hour < self.NUM_HOURS)

        elif not rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, _ = time_api.date_to_index(dtstart)
            pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and rasp0.duration + slot.hour < self.NUM_HOURS)

        elif not rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, given_hour = time_api.date_to_index(dtstart)
            pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour and rasp0.duration + slot.hour < self.NUM_HOURS)

        if not pool:
            print("nothing")
            new_timetable[rasp0] = old_slot
            return new_timetable, rasp_rrules

        slot = random.choice(tuple(pool))

        NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
        NEW_UNTIL = rasp_rrules[rasp0.id]["UNTIL"]
        until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
        NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

        rasp_rrules[rasp0.id]["DTSTART"] = NEW_DTSTART
        rasp_rrules[rasp0.id]["UNTIL"] = NEW_UNTIL
        rasp_rrules[rasp0.id]["all_dates"] = time_api.get_rrule_dates(rasp0.rrule, NEW_DTSTART, NEW_UNTIL)
        new_timetable[rasp0] = slot

        return new_timetable, rasp_rrules


    def mutate_and_grade(self, timetable):
        timetable = self.mutate(timetable)
        return self.grade(timetable), *timetable


    def iterate(self, sample, generations=1000, starting_generation=1, population_cap=5):
        BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        for generation in tqdm(range(starting_generation, starting_generation+generations)):
            #print("SAMPLE: ", self.get_size(sample) / 10**6, "MB.")
            try:
                original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
                with Pool(7) as p:
                    signal.signal(signal.SIGINT, original_sigint_handler)

                    the_samples = [(s[1], s[2]) for s in sample]

                    mutations = p.map_async(self.mutate_and_grade, the_samples)
                    probs = p.map_async(self.prob_and_grade, the_samples)
                    mutations.wait()
                    probs.wait()

                sample += mutations.get() + probs.get()
                #sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
                sample = sample[0:population_cap]
                if sample[0][0]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

            except KeyboardInterrupt:
                return sample

        return sample


    #Just for testing
    def iterate_no_parallel(self, sample, generations=1000, starting_generation=1, population_cap=5):
        BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        for generation in tqdm(range(starting_generation, starting_generation+generations)):
                the_samples = [(s[1], s[2]) for s in sample]

                for s in the_samples:
                    mutation = self.mutate_and_grade(s)
                    prob = self.prob_and_grade(s)
                    sample.append(mutation)
                    sample.append(prob)

                sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
                sample = sample[0:population_cap]
                if sample[0][0]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

        return sample


    def fix_problematic(self, timetable):
        old_timetable = timetable[0]
        new_timetable, rasp_rrules = timetable[0].copy(), timetable[1]
        problematic_rasps = []

        rooms_occupied = {k:v.copy() for k,v in self.rooms_occupied.items()}
        profs_occupied = {k:v.copy() for k,v in self.profs_occupied.items()}

        for rasp, (room_id, week, day, hour) in old_timetable.items():
            self.tax_rrule_in_matrix3D(rooms_occupied[room_id], rasp, rasp_rrules[rasp.id]["all_dates"])
            self.tax_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp, rasp_rrules[rasp.id]["all_dates"])

        for rasp, (room_id, week, day, hour) in old_timetable.items():
            room_problem = self.count_rrule_in_matrix3D(rooms_occupied[room_id], rasp, rasp_rrules[rasp.id]["all_dates"])
            prof_problem = self.count_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp, rasp_rrules[rasp.id]["all_dates"])
            capacity_problem = bool(self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0)
            computer_problem1 = not room_id in self.computer_rooms and rasp.needsComputers
            computer_problem2 = room_id in self.computer_rooms and not rasp.needsComputers

            if room_problem or prof_problem or capacity_problem or computer_problem1 or computer_problem2:
                problematic_rasps.append(rasp)

        if not problematic_rasps:
            return timetable

        new_timetable = old_timetable.copy()

        # Choose a random problematic rasp
        rasp0 = random.choice(problematic_rasps)
        old_slot = new_timetable[rasp0]

        new_timetable.pop(rasp0, 0)

        all_avs = self.free_slots.copy()

        taken_terms = set()
        for rasp, (room_id, _, _, _) in old_timetable.items():
            for week, day, hour in rasp_rrules[rasp.id]["all_dates"]:
                taken_terms |= {(room_id, week, day, hour+i) for i in range(rasp.duration)}
        all_avs -= taken_terms

        nonavs = set()
        for (room_id, week, day, hour) in all_avs:
            if any((room_id, week, day, hour+i) not in all_avs for i in range(1, rasp0.duration)):
                nonavs.add((room_id, week, day, hour))
        all_avs -= nonavs

        pool = set()
        if rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, _ = time_api.date_to_index(dtstart_weekday)
                pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and rasp0.duration + slot.hour < self.NUM_HOURS)

        elif rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, given_hour = time_api.date_to_index(dtstart_weekday)
                pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour and rasp0.duration + slot.hour < self.NUM_HOURS)

        elif not rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, _ = time_api.date_to_index(dtstart)
            pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and rasp0.duration + slot.hour < self.NUM_HOURS)

        elif not rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, given_hour = time_api.date_to_index(dtstart)
            pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour and rasp0.duration + slot.hour < self.NUM_HOURS)

        if not pool:
            print("nothing")
            new_timetable[rasp0] = old_slot
            return new_timetable, rasp_rrules

        slot = random.choice(tuple(pool))

        NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
        NEW_UNTIL = rasp_rrules[rasp0.id]["UNTIL"]
        until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
        NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

        rasp_rrules[rasp0.id]["DTSTART"] = NEW_DTSTART
        rasp_rrules[rasp0.id]["UNTIL"] = NEW_UNTIL
        rasp_rrules[rasp0.id]["all_dates"] = time_api.get_rrule_dates(rasp0.rrule, NEW_DTSTART, NEW_UNTIL)
        new_timetable[rasp0] = slot

        return new_timetable, rasp_rrules


    def prob_and_grade(self, timetable):
        timetable = self.fix_problematic(timetable)
        return self.grade(timetable), *timetable
