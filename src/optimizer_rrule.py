import random
import numpy as np
from tqdm import tqdm
import signal
from collections import defaultdict
from dateutil.rrule import rrule, WEEKLY, MO, TU, WE, TH, FR
from multiprocessing import Pool
import data_api.time_structure as time_api

class Optimizer:
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
            first_week_avs = self.starting_slots.copy()
            timetable = {}
            rasp_rrules = {rasp.id : {"DTSTART": None, "UNTIL": None, "all_dates": []} for rasp in self.rasps}
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
                        given_week, given_day, _ = time_api.date_to_index(rasp.DTSTART)
                        avs_pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day)

                    #case: has DTSTART with hour -> random(room_id, _given_week, _given_day, _given_hour)
                    elif DTSTART and DTSTART.hour:
                        print(rasp.subjectId, rasp.type, rasp.group)
                        given_week, given_day, given_hour = time_api.date_to_index(rasp.DTSTART)
                        avs_pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour)

                    try_slot = random.choice(tuple(avs_pool))

                    if try_slot.hour + rasp.duration < self.NUM_HOURS:
                        slot = try_slot

                NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
                NEW_UNTIL = rasp.UNTIL

                #case has no UNTIL:
                if not NEW_UNTIL:
                    NEW_UNTIL = time_api.index_to_date(self.NUM_WEEKS-1, 4, slot.hour) #last week, last day, DTSTART.hour

                #case has UNTIL without hour OR has UNTIL with hour:
                elif NEW_UNTIL:
                    until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
                    NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

                # Remove if they exit
                all_avs.discard(slot)
                first_week_avs.discard(slot)

                rasp_rrules[rasp.id] = {"DTSTART": NEW_DTSTART, "UNTIL": NEW_UNTIL, "all_dates": self.get_rrule_dates(rasp, NEW_DTSTART, NEW_UNTIL)}
                timetable[rasp] = slot

            sample.append((self.grade((timetable, rasp_rrules)), timetable, rasp_rrules))

        return sample


    def nast_tax_rrule_optional_rasp(self, optionals_occupied, nast_occupied, rasp, hour, rrule_dates):
        for hr in range(hour, hour + rasp.duration):
            for date in rrule_dates:
                week, day, _ = time_api.date_to_index(date)
                if optionals_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] += 1
            self.tax_rrule_in_matrix3D(optionals_occupied, rasp, rrule_dates)


    #Taxing funtions hold 90% of the complexity
    def tax_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        for date in rrule_dates:
            week, day, hour = time_api.date_to_index(date)
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1


    def count_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        count = 0
        for date in rrule_dates:
            week, day, hour = time_api.date_to_index(date)
            count += sum(matrix3D[week, day, hour:(hour + rasp.duration)]>1)
        return count


    def get_rrule_dates(self, rasp, NEW_DTSTART, NEW_UNTIL):
        freqs = {"WEEKLY":WEEKLY}
        FREQ = freqs[rasp.FREQ]

        byweekdays = {"MO":MO, "TU":TU, "WE":WE, "TH":TH, "FR":FR}
        BYWEEKDAY = None if not rasp.BYWEEKDAY else [byweekdays[wday] for wday in rasp.BYWEEKDAY]

        rasp_dates = tuple(rrule(freq = FREQ, interval = rasp.INTERVAL, byweekday = BYWEEKDAY,
                           dtstart = NEW_DTSTART, until = NEW_UNTIL, cache=True))
        return rasp_dates


    def grade(self, timetable):
        timetable, rasp_rrules = timetable[0], timetable[1]
        rooms_occupied = {k:v.copy() for k,v in self.rooms_occupied.items()}
        profs_occupied = {k:v.copy() for k,v in self.profs_occupied.items()}

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

                    #rasp = next(r for r in timetable.keys() if rasp.id == r.id)
                    room_id, _, _, hour = timetable[rasp]

                    if rasp.mandatory or not PARALLEL_OPTIONALS_ALLOWED:
                        self.tax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp, rasp_rrules[rasp.id]["all_dates"])
                    else:
                        self.nast_tax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp, hour, rasp_rrules[rasp.id]["all_dates"])

                for rasp in nast:
                    if rasp.id in taxed_rasps:
                        continue
                    taxed_rasps.add(rasp.id)

                    rasp = next(r for r in timetable.keys() if rasp.id == r.id)
                    room_id, _, _, hour = timetable[rasp]
                    cnt = self.count_rrule_in_matrix3D(nasts_occupied[sem_id], rasp, rasp_rrules[rasp.id]["all_dates"])
                    score_nasts += cnt * self.students_estimate[rasp.id]

            total_nast_score -= score_nasts
            total_score -= score_nasts

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
        old_timetable = timetable[0]
        new_timetable, rasp_rrules = timetable[0].copy(), timetable[1]

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
        for rasp, (room_id, week, day, hour) in old_timetable.items():
            taken_terms |= {(room_id, week, day, hour+i) for i in range(rasp.duration)}
        avs_pool -= taken_terms

        nonavs = set()
        for (room_id, week, day, hour) in avs_pool:
            if any((room_id, week, day, hour+i) not in avs_pool for i in range(1, rasp0.duration)):
                nonavs.add((room_id, week, day, hour))
        avs_pool -= nonavs

        if not avs_pool:
            print("nothing")
            new_timetable[rasp0] = old_slot
            return (new_timetable, rasp_rrules)

        slot = random.choice(list(avs_pool))

        NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)

        #case: has no UNTIL
        NEW_UNTIL = rasp0.UNTIL
        if not NEW_UNTIL:
            NEW_UNTIL = time_api.index_to_date(self.NUM_WEEKS-1, 4, slot.hour)
        elif NEW_UNTIL:
            until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
            NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)


        rasp_rrules[rasp0.id] = {"DTSTART": NEW_DTSTART, "UNTIL": NEW_UNTIL, "all_dates": self.get_rrule_dates(rasp0, NEW_DTSTART, NEW_UNTIL)}
        new_timetable[rasp0] = slot

        return (new_timetable, rasp_rrules)


    def mutate_and_grade(self, timetable):
        timetable = self.mutate(timetable)
        return self.grade(timetable), *timetable


    def iterate(self, sample, generations=1000, starting_generation=1, population_cap=5):
        BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        for generation in tqdm(range(starting_generation, starting_generation+generations)):
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
                sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
                sample = sample[0:population_cap]
                if sample[0][0]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

            except KeyboardInterrupt:
                return sample

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
        avs_pool = self.starting_slots.copy()

        week, day, hour = -1, -1, -1
        #case: has no DTSTART
        DTSTART = rasp0.DTSTART
        if not DTSTART:
            pass

        #case: has DTSTART without hour
        elif DTSTART and not DTSTART.hour:
            pass

        #case: has DTSTART and hour (care! -> random_sample sets DTSTART with hour) TODO: Check if FIXED DTSTART with hour
        elif DTSTART and DTSTART.hour:
            pass

        taken_terms = set()
        for rasp, (room_id, week, day, hour) in old_timetable.items():
            taken_terms |= {(room_id, week, day, hour+i) for i in range(rasp.duration)}
        avs_pool -= taken_terms

        nonavs = set()
        for (room_id, week, day, hour) in avs_pool:
            if any((room_id, week, day, hour+i) not in avs_pool for i in range(1, rasp0.duration)):
                nonavs.add((room_id, week, day, hour))
        avs_pool -= nonavs

        if not avs_pool:
            print("avs in prob prob")
            new_timetable[rasp0] = old_slot
            return (new_timetable, rasp_rrules)

        slot = random.choice(list(avs_pool))

        NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)

        #case: has no UNTIL
        NEW_UNTIL = rasp0.UNTIL
        if not NEW_UNTIL:
            NEW_UNTIL = time_api.index_to_date(self.NUM_WEEKS-1, 4, slot.hour)
        elif NEW_UNTIL:
            until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
            NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

        rasp_rrules[rasp0.id] = {"DTSTART": NEW_DTSTART, "UNTIL": NEW_UNTIL, "all_dates": self.get_rrule_dates(rasp0, NEW_DTSTART, NEW_UNTIL)}
        new_timetable[rasp0] = slot

        return (new_timetable, rasp_rrules)


    def prob_and_grade(self, timetable):
        timetable = self.fix_problematic(timetable)
        return self.grade(timetable), *timetable
