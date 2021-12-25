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

            rooms_occupied = {k:v.copy() for k,v in self.rooms_occupied.items()}
            profs_occupied = {k:v.copy() for k,v in self.profs_occupied.items()}
            nasts_occupied = defaultdict(lambda: np.zeros((self.NUM_WEEKS, 5, self.NUM_HOURS), dtype=np.uint8))
            optionals_occupied = np.zeros((self.NUM_WEEKS, 5, self.NUM_HOURS), dtype=np.uint8)
            groups_occupied = {}

            grade_obj = {"totalScore": 0, "roomScore": 0, "professorScore": 0, "capacityScore": 0, "computerScore": 0, "nastScore": 0}
            rasp_grades = {rasp.id : grade_obj.copy() for rasp in self.rasps}
            all_rasps_grade = grade_obj.copy()

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

                all_avs.remove(slot)

                rasp_rrules[rasp.id]["DTSTART"] = NEW_DTSTART
                rasp_rrules[rasp.id]["UNTIL"] = NEW_UNTIL
                rasp_rrules[rasp.id]["all_dates"] = time_api.get_rrule_dates(rasp.rrule, NEW_DTSTART, NEW_UNTIL)

                self.tax_rrule_in_matrix3D(rooms_occupied[slot.room_id], rasp, rasp_rrules[rasp.id]["all_dates"])
                self.tax_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp, rasp_rrules[rasp.id]["all_dates"])

                if rasp.totalGroups > 1:
                    key = str(rasp.subjectId) + str(rasp.type)
                    if key not in groups_occupied:
                        groups_occupied[key] = {}
                    if slot not in groups_occupied[key]:
                        groups_occupied[key][slot] = 0

                    groups_occupied[key][slot]+=1

                sem_ids = rasp.mandatory_in_semesterIds + rasp.optional_in_semesterIds
                for sem_id in sem_ids:
                    key = str(rasp.subjectId) + str(rasp.type)
                    if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 1:
                        continue

                    rasp_mandatory = True if sem_id in rasp.mandatory_in_semesterIds else False
                    if rasp_mandatory: #or not PARALLEL_OPTIONALS_ALLOWED:
                        self.tax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp, rasp_rrules[rasp.id]["all_dates"])
                    else:
                        self.nast_tax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp, slot.hour, rasp_rrules[rasp.id]["all_dates"])

                all_rasps_grade = {k : v - rasp_grades[rasp.id][k] for k,v in all_rasps_grade.items()}
                rasp_grades[rasp.id] = self.grade_rasp(rooms_occupied, profs_occupied, nasts_occupied, rasp, slot, rasp_rrules)
                all_rasps_grade = {k : v + rasp_grades[rasp.id][k] for k,v in all_rasps_grade.items()}
                timetable[rasp] = slot

            data = {"grade":all_rasps_grade,
                    "timetable":timetable,
                    "rooms_occupied":rooms_occupied,
                    "profs_occupied":profs_occupied,
                    "nasts_occupied":dict(**nasts_occupied),
                    "optionals_occupied":optionals_occupied,
                    "groups_occupied":dict(**groups_occupied),
                    "rasp_grades": rasp_grades,
                    "rasp_rrules": rasp_rrules}
            sample.append(data)

        return sample


    def grade_rasp(self, rooms_occupied, profs_occupied, nasts_occupied, rasp, slot, rasp_rrules):
        total_score = 0
        cnt = self.count_rrule_in_matrix3D(rooms_occupied[slot.room_id], rasp, rasp_rrules[rasp.id]["all_dates"])
        score_rooms = -cnt * self.students_estimate[rasp.id]
        total_score += score_rooms

        # Professor collisions
        cnt = self.count_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp, rasp_rrules[rasp.id]["all_dates"])
        score_professors = -cnt * self.students_estimate[rasp.id]
        total_score += score_professors

        # Insufficient room capacity
        capacity = bool(self.students_estimate[rasp.id] - self.room_capacity[slot.room_id]>=0)
        score_capacity = -capacity * rasp.duration * self.students_estimate[rasp.id]
        total_score += score_capacity

        score_computers = 0
        # Computer room & computer rasp collisions
        if not slot.room_id in self.computer_rooms and rasp.needsComputers:
            score_computers = -self.students_estimate[rasp.id]
            total_score += score_computers

        if slot.room_id in self.computer_rooms and not rasp.needsComputers:
            score_computers = -self.students_estimate[rasp.id] * 0.1
            total_score += score_computers

        score_nasts = 0
        sem_ids = rasp.mandatory_in_semesterIds + rasp.optional_in_semesterIds
        for sem_id in sem_ids:
            score_sem = 0
            cnt = self.count_rrule_in_matrix3D(nasts_occupied[sem_id], rasp, rasp_rrules[rasp.id]["all_dates"])
            score_sem += -cnt * self.students_estimate[rasp.id]
            score_nasts += score_sem
            total_score += score_nasts

        final_score = {
                "totalScore": round(total_score,2),
                "roomScore": round(score_rooms, 2),
                "professorScore": round(score_professors,2),
                "capacityScore": round(score_capacity,2),
                "computerScore": round(score_computers,2),
                "nastScore": round(score_nasts,2)
        }

        return final_score


    def nast_untax_rrule_optional_rasp(self, optionals_occupied, nast_occupied, rasp, hour, rrule_dates):
        self.untax_rrule_in_matrix3D(optionals_occupied, rasp, rrule_dates)
        for hr in range(hour, hour + rasp.duration):
            for week, day, _ in rrule_dates:
                if optionals_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] -= 1


    def nast_tax_rrule_optional_rasp(self, optionals_occupied, nast_occupied, rasp, hour, rrule_dates):
        for hr in range(hour, hour + rasp.duration):
            for week, day, _ in rrule_dates:
                if optionals_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] += 1
        self.tax_rrule_in_matrix3D(optionals_occupied, rasp, rrule_dates)


    def untax_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] -= 1


    def tax_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1


    def count_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        return sum(np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>1)
                   for week, day, hour in rrule_dates)


    def grade(self, timetable):
        timetable, rasp_rrules, constraints = timetable[0], timetable[1], timetable[2]
        rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied = constraints["rooms_occupied"], constraints["profs_occupied"], constraints["nasts_occupied"], constraints["optionals_occupied"]

        #for rasp, (room_id, _, _, hour) in timetable.items():
        #    print(rasp)
        #    print(room_id, rasp_rrules[rasp.id]["all_dates"])
        #quit()

        total_score = 0
        total_room_score, total_professor_score = 0, 0
        total_capacity_score, total_computers_score = 0, 0
        prob_profs = []
        for rasp, (room_id, _, _, hour) in timetable.items():

            # Room collisions
            cnt = self.count_rrule_in_matrix3D(rooms_occupied[room_id], rasp, rasp_rrules[rasp.id]["all_dates"])
            score_rooms = cnt * self.students_estimate[rasp.id]
            total_room_score -= score_rooms
            total_score -= score_rooms

            # Professor collisions
            cnt = self.count_rrule_in_matrix3D(profs_occupied[rasp.professorId], rasp, rasp_rrules[rasp.id]["all_dates"])
            if cnt > 1:
                prob_profs.append(rasp.professorId)
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
        for semester, the_nasts in self.nasts.items():
            sem_id, _, _, _ = semester
            score_nasts = 0
            taxed_rasps = set()
            for nast in the_nasts:
                for rasp in nast:
                    if rasp.id in taxed_rasps:
                        continue
                    taxed_rasps.add(rasp.id)
                    room_id, _, _, _ = timetable[rasp]
                    cnt = self.count_rrule_in_matrix3D(nasts_occupied[sem_id], rasp, rasp_rrules[rasp.id]["all_dates"])
                    score_nasts += cnt * self.students_estimate[rasp.id]

            total_nast_score -= score_nasts
            total_score -= score_nasts

        #print(prob_profs,"\n")
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


    def mutate(self, data):
        old_timetable = data["timetable"]
        new_timetable = old_timetable.copy()
        rasp_rrules = data["rasp_rrules"]

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
            new_timetable[rasp0] = old_slot
            print("nothing")
            return data

        slot = random.choice(tuple(pool))

        rooms_occupied = data["rooms_occupied"]
        profs_occupied = data["profs_occupied"]
        nasts_occupied = data["nasts_occupied"]
        optionals_occupied = data["optionals_occupied"]
        groups_occupied = data["groups_occupied"]
        rasp_grades = data["rasp_grades"]

        self.untax_rrule_in_matrix3D(rooms_occupied[old_slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
        self.untax_rrule_in_matrix3D(profs_occupied[rasp0.professorId], rasp0, rasp_rrules[rasp0.id]["all_dates"])
        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds

        if rasp0.totalGroups > 1:
            key = str(rasp0.subjectId) + str(rasp0.type)
            if key in groups_occupied and slot in groups_occupied[key]:
                groups_occupied[key][slot] -= 1

        for sem_id in sem_ids:
            if rasp0.totalGroups > 1:
                key = str(rasp0.subjectId) + str(rasp0.type)
                if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 0:
                    continue
            rasp_mandatory = True if sem_id in rasp0.mandatory_in_semesterIds else False
            if rasp_mandatory: #or not PARALLEL_OPTIONALS_ALLOWED:
                self.untax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
            else:
                self.nast_untax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp0, slot.hour, rasp_rrules[rasp0.id]["all_dates"])

        NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
        NEW_UNTIL = rasp_rrules[rasp0.id]["UNTIL"]
        until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
        NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

        rasp_rrules[rasp0.id]["DTSTART"] = NEW_DTSTART
        rasp_rrules[rasp0.id]["UNTIL"] = NEW_UNTIL
        rasp_rrules[rasp0.id]["all_dates"] = time_api.get_rrule_dates(rasp0.rrule, NEW_DTSTART, NEW_UNTIL)

        self.tax_rrule_in_matrix3D(rooms_occupied[slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
        self.tax_rrule_in_matrix3D(profs_occupied[rasp0.professorId], rasp0, rasp_rrules[rasp0.id]["all_dates"])

        if rasp0.totalGroups > 1:
            key = str(rasp0.subjectId) + str(rasp0.type)
            if key not in groups_occupied:
                groups_occupied[key] = {}
            if slot not in groups_occupied[key]:
                groups_occupied[key][slot] = 0
            groups_occupied[key][slot]+=1

        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
        for sem_id in sem_ids:
            if rasp0.totalGroups > 1:
                key = str(rasp0.subjectId) + str(rasp0.type)
                if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 1:
                    continue

            rasp_mandatory = True if sem_id in rasp0.mandatory_in_semesterIds else False
            if rasp_mandatory: #or not PARALLEL_OPTIONALS_ALLOWED:
                self.tax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
            else:
                self.nast_tax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp0, slot.hour, rasp_rrules[rasp0.id]["all_dates"])

        data["grade"] = {k : v - rasp_grades[rasp0.id][k] for k,v in data["grade"].items()}
        rasp_grades[rasp0.id] = self.grade_rasp(rooms_occupied, profs_occupied, nasts_occupied, rasp0, slot, rasp_rrules)
        data["grade"] = {k : v + rasp_grades[rasp0.id][k] for k,v in data["grade"].items()}

        new_timetable[rasp0] = slot
        data["timetable"] = new_timetable

        return data


    def iterate(self, sample, generations=1000, starting_generation=1, population_cap=5):
        BEST_SAMPLE = (sample[0]["grade"], sample[0]["timetable"].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        for generation in tqdm(range(starting_generation, starting_generation+generations)):
            #print("SAMPLE: ", self.get_size(sample) / 10**6, "MB.")
            try:
                original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
                with Pool(7) as p:
                    signal.signal(signal.SIGINT, original_sigint_handler)

                    the_samples = [s for s in sample]

                    mutations = p.map_async(self.mutate, the_samples)
                    #probs = p.map_async(self.fix_problematic, the_samples)
                    correct = p.map_async(self.find_correct_place, the_samples)
                    mutations.wait()
                    #probs.wait()
                    correct.wait()

                sample += mutations.get() + correct.get() #+ probs.get() + correct.get()
                #sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x["grade"]["totalScore"], reverse=True)
                sample = sample[0:population_cap]
                if sample[0]["grade"]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0]["grade"], sample[0]["timetable"].copy())
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
                    mutation = self.mutate(s)
                    prob = self.fix_problematic(s)
                    sample.append(mutation)
                    sample.append(prob)

                sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
                sample = sample[0:population_cap]
                if sample[0][0]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

        return sample


    def fix_problematic(self, data):
        old_timetable = data["timetable"]
        rasp_rrules = data["rasp_rrules"]
        rooms_occupied = data["rooms_occupied"]
        profs_occupied = data["profs_occupied"]
        nasts_occupied = data["nasts_occupied"]
        optionals_occupied = data["optionals_occupied"]
        groups_occupied = data["groups_occupied"]
        rasp_grades = data["rasp_grades"]

        worst_type, worst_grade = "totalScore", 0
        for error_type, grade in data["grade"].items():
            if error_type == "totalScore":
                continue
            if grade < worst_grade:
                worst_grade = grade
                worst_type = error_type

        problematic_rasps = []
        for rasp, _ in old_timetable.items():
            if rasp_grades[rasp.id][worst_type] < 0:
                problematic_rasps.append(rasp)

        if not problematic_rasps:
            return data

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

        if worst_type == "professorScore":
            nonprof = set()
            for (room_id, week, day, hour) in all_avs:
                if any(profs_occupied[rasp0.professorId][week, day, hour:(hour+rasp0.duration)]>1):
                    nonprof.add((room_id, week, day, hour+i) for i in range(rasp0.duration))
            all_avs -= nonprof

        elif worst_type == "roomScore":
            nonroom = set()
            for (room_id, week, day, hour) in all_avs:
                if any(rooms_occupied[room_id][week, day, hour:(hour+rasp0.duration)]>1):
                    nonroom.add((room_id, week, day, hour+i) for i in range(rasp0.duration))
            all_avs -= nonroom

        elif worst_type == "capacityScore":
            noncapacity = set()
            for (room_id, week, day, hour) in all_avs:
                capacity = bool(self.students_estimate[rasp0.id] - self.room_capacity[room_id]>=0)
                if not capacity:
                    noncapacity.add((room_id, week, day, hour))
            all_avs -= noncapacity

        elif worst_type == "computerScore":
            nonpc = set()
            for (room_id, week, day, hour) in all_avs:
                if not room_id in self.computer_rooms and rasp0.needsComputers:
                    nonpc.add((room_id, week, day, hour))

                if room_id in self.computer_rooms and not rasp0.needsComputers:
                    nonpc.add((room_id, week, day, hour))
            all_avs -= nonpc

        elif worst_type == "nastScore":
            nonnast = set()
            sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
            for (room_id, week, day, hour) in all_avs:
                if any(any(nasts_occupied[sem_id][week, day, hour:(hour+rasp0.duration)]>1) for sem_id in sem_ids):
                    nonnast.add((room_id, week, day, hour+i) for i in range(rasp0.duration))
            all_avs -= nonnast

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
            print("nothing fix_prob")
            new_timetable[rasp0] = old_slot
            return data

        slot = random.choice(tuple(pool))

        self.untax_rrule_in_matrix3D(rooms_occupied[old_slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
        self.untax_rrule_in_matrix3D(profs_occupied[rasp0.professorId], rasp0, rasp_rrules[rasp0.id]["all_dates"])

        if rasp0.totalGroups > 1:
            key = str(rasp0.subjectId) + str(rasp0.type)
            if key in groups_occupied and slot in groups_occupied[key]:
                groups_occupied[key][slot] -= 1

        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
        for sem_id in sem_ids:
            if rasp0.totalGroups > 1:
                key = str(rasp0.subjectId) + str(rasp0.type)
                if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 0:
                    continue

        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
        for sem_id in sem_ids:
            if rasp0.totalGroups > 1:
                key = str(rasp0.subjectId) + str(rasp0.type)
                if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 0:
                    continue

            rasp_mandatory = True if sem_id in rasp0.mandatory_in_semesterIds else False
            if rasp_mandatory: #or not PARALLEL_OPTIONALS_ALLOWED:
                self.untax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
            else:
                self.nast_untax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp0, slot.hour, rasp_rrules[rasp0.id]["all_dates"])

        NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
        NEW_UNTIL = rasp_rrules[rasp0.id]["UNTIL"]
        until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
        NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

        rasp_rrules[rasp0.id]["DTSTART"] = NEW_DTSTART
        rasp_rrules[rasp0.id]["UNTIL"] = NEW_UNTIL
        rasp_rrules[rasp0.id]["all_dates"] = time_api.get_rrule_dates(rasp0.rrule, NEW_DTSTART, NEW_UNTIL)

        self.tax_rrule_in_matrix3D(rooms_occupied[slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
        self.tax_rrule_in_matrix3D(profs_occupied[rasp0.professorId], rasp0, rasp_rrules[rasp0.id]["all_dates"])

        if rasp0.totalGroups > 1:
            key = str(rasp0.subjectId) + str(rasp0.type)
            if key not in groups_occupied:
                groups_occupied[key] = {}
            if slot not in groups_occupied[key]:
                groups_occupied[key][slot] = 0
            groups_occupied[key][slot]+=1

        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
        for sem_id in sem_ids:
            if rasp0.totalGroups > 1:
                key = str(rasp0.subjectId) + str(rasp0.type)
                if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 1:
                    continue

            rasp_mandatory = True if sem_id in rasp0.mandatory_in_semesterIds else False
            if rasp_mandatory: #or not PARALLEL_OPTIONALS_ALLOWED:
                self.tax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
            else:
                self.nast_tax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp0, slot.hour, rasp_rrules[rasp0.id]["all_dates"])

        data["grade"] = {k : v - rasp_grades[rasp0.id][k] for k,v in data["grade"].items()}
        rasp_grades[rasp0.id] = self.grade_rasp(rooms_occupied, profs_occupied, nasts_occupied, rasp0, slot, rasp_rrules)
        data["grade"] = {k : v + rasp_grades[rasp0.id][k] for k,v in data["grade"].items()}

        new_timetable[rasp0] = slot
        data["timetable"] = new_timetable

        return data


    def find_correct_place(self, data):
        old_timetable = data["timetable"]
        rasp_rrules = data["rasp_rrules"]
        rooms_occupied = data["rooms_occupied"]
        profs_occupied = data["profs_occupied"]
        nasts_occupied = data["nasts_occupied"]
        optionals_occupied = data["optionals_occupied"]
        groups_occupied = data["groups_occupied"]
        rasp_grades = data["rasp_grades"]

        problematic_rasps = []
        for rasp, _ in old_timetable.items():
            if rasp_grades[rasp.id]["totalScore"] < 0:
                problematic_rasps.append(rasp)

        if not problematic_rasps:
            return data

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

        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
        pool = set()
        if rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, _ = time_api.date_to_index(dtstart_weekday)


                pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and rasp0.duration + slot.hour < self.NUM_HOURS \
                            and all(profs_occupied[rasp0.professorId][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and all(rooms_occupied[slot.room_id][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and bool(self.students_estimate[rasp0.id] - self.room_capacity[slot.room_id]>=0) \
                            and ((slot.room_id in self.computer_rooms and rasp0.needsComputers) or \
                                 (slot.room_id not in self.computer_rooms and not rasp0.needsComputers)) \
                            and all(all(nasts_occupied[sem_id][week, day, hour:(hour+rasp0.duration)]==0) for sem_id in sem_ids))

        elif rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, given_hour = time_api.date_to_index(dtstart_weekday)
                pool |= set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour and rasp0.duration + slot.hour < self.NUM_HOURS \
                            and all(profs_occupied[rasp0.professorId][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and all(rooms_occupied[slot.room_id][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and bool(self.students_estimate[rasp0.id] - self.room_capacity[slot.room_id]>=0) \
                            and ((slot.room_id in self.computer_rooms and rasp0.needsComputers) or \
                                 (slot.room_id not in self.computer_rooms and not rasp0.needsComputers)) \
                            and all(all(nasts_occupied[sem_id][week, day, hour:(hour+rasp0.duration)]==0) for sem_id in sem_ids))

        elif not rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, _ = time_api.date_to_index(dtstart)
            pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and rasp0.duration + slot.hour < self.NUM_HOURS \
                            and all(profs_occupied[rasp0.professorId][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and all(rooms_occupied[slot.room_id][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and bool(self.students_estimate[rasp0.id] - self.room_capacity[slot.room_id]>=0) \
                            and ((slot.room_id in self.computer_rooms and rasp0.needsComputers) or \
                                 (slot.room_id not in self.computer_rooms and not rasp0.needsComputers)) \
                            and all(all(nasts_occupied[sem_id][week, day, hour:(hour+rasp0.duration)]==0) for sem_id in sem_ids))

        elif not rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, given_hour = time_api.date_to_index(dtstart)
            pool = set(slot for slot in all_avs if slot.week == given_week and slot.day == given_day and slot.hour == given_hour and rasp0.duration + slot.hour < self.NUM_HOURS \
                            and all(profs_occupied[rasp0.professorId][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and all(rooms_occupied[slot.room_id][slot.week, slot.day, slot.hour:(slot.hour+rasp0.duration)]==0) \
                            and bool(self.students_estimate[rasp0.id] - self.room_capacity[slot.room_id]>=0) \
                            and ((slot.room_id in self.computer_rooms and rasp0.needsComputers) or \
                                 (slot.room_id not in self.computer_rooms and not rasp0.needsComputers)) \
                            and all(all(nasts_occupied[sem_id][week, day, hour:(hour+rasp0.duration)]==0) for sem_id in sem_ids))

        if not pool:
            #print("nothing find correct")
            new_timetable[rasp0] = old_slot
            return data
        print("found correct")

        slot = random.choice(tuple(pool))
        #print("BEFORE GRADE: ", rasp0.id, rasp_grades[rasp0.id])

        # Perhaps I'm not taxing/untaxing correctly. Maybe "all_dates" aren't correctly being refreshed.
        self.untax_rrule_in_matrix3D(rooms_occupied[old_slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
        self.untax_rrule_in_matrix3D(profs_occupied[rasp0.professorId], rasp0, rasp_rrules[rasp0.id]["all_dates"])

        if rasp0.totalGroups > 1:
            key = str(rasp0.subjectId) + str(rasp0.type)
            if key in groups_occupied and slot in groups_occupied[key]:
                groups_occupied[key][slot] -= 1

        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
        for sem_id in sem_ids:
            if rasp0.totalGroups > 1:
                key = str(rasp0.subjectId) + str(rasp0.type)
                if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 0:
                    continue

            rasp_mandatory = True if sem_id in rasp0.mandatory_in_semesterIds else False
            if rasp_mandatory: #or not PARALLEL_OPTIONALS_ALLOWED:
                self.untax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
            else:
                self.nast_untax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp0, slot.hour, rasp_rrules[rasp0.id]["all_dates"])

        NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
        NEW_UNTIL = rasp_rrules[rasp0.id]["UNTIL"]
        until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
        NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

        rasp_rrules[rasp0.id]["DTSTART"] = NEW_DTSTART
        rasp_rrules[rasp0.id]["UNTIL"] = NEW_UNTIL
        rasp_rrules[rasp0.id]["all_dates"] = time_api.get_rrule_dates(rasp0.rrule, NEW_DTSTART, NEW_UNTIL)

        self.tax_rrule_in_matrix3D(rooms_occupied[slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
        self.tax_rrule_in_matrix3D(profs_occupied[rasp0.professorId], rasp0, rasp_rrules[rasp0.id]["all_dates"])

        if rasp0.totalGroups > 1:
            key = str(rasp0.subjectId) + str(rasp0.type)
            if key not in groups_occupied:
                groups_occupied[key] = {}
            if slot not in groups_occupied[key]:
                groups_occupied[key][slot] = 0
            groups_occupied[key][slot]+=1

        sem_ids = rasp0.mandatory_in_semesterIds + rasp0.optional_in_semesterIds
        for sem_id in sem_ids:
            if rasp0.totalGroups > 1:
                key = str(rasp0.subjectId) + str(rasp0.type)
                if key in groups_occupied and slot in groups_occupied[key] and groups_occupied[key][slot] > 1:
                    continue

            rasp_mandatory = True if sem_id in rasp0.mandatory_in_semesterIds else False
            if rasp_mandatory: #or not PARALLEL_OPTIONALS_ALLOWED:
                self.tax_rrule_in_matrix3D(nasts_occupied[sem_id], rasp0, rasp_rrules[rasp0.id]["all_dates"])
            else:
                self.nast_tax_rrule_optional_rasp(optionals_occupied, nasts_occupied[sem_id], rasp0, slot.hour, rasp_rrules[rasp0.id]["all_dates"])

        data["grade"] = {k : v - rasp_grades[rasp0.id][k] for k,v in data["grade"].items()}
        rasp_grades[rasp0.id] = self.grade_rasp(rooms_occupied, profs_occupied, nasts_occupied, rasp0, slot, rasp_rrules)
        data["grade"] = {k : v + rasp_grades[rasp0.id][k] for k,v in data["grade"].items()}

        new_timetable[rasp0] = slot
        data["timetable"] = new_timetable

        #Nasts are being (re)calculated badly badly
        print(data["grade"])
        #print("AFTER GRADE: ", rasp0.id, rasp_grades[rasp0.id])
        return data
