import sys
import random
import numpy as np
from tqdm import tqdm
from collections import defaultdict
from dateutil.rrule import rrulestr
import data_api.time_structure as time_api
from data_api.utilities.my_types import Slot

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
        self.semesters_info = data["semesters_info"]
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
            optionals_occupied = defaultdict(lambda: np.zeros((self.NUM_WEEKS, 5, self.NUM_HOURS), dtype=np.uint8))
            groups_occupied = {}
            for rasp in self.rasps:
                if rasp.total_groups > 1:
                    key = str(rasp.subject_id) + str(rasp.type)
                    groups_occupied[key] = {}

            grade_obj = {"totalScore": 0, "roomScore": 0, "professorScore": 0, "capacityScore": 0, "computerScore": 0, "nastScore": 0}

            sem_ids = set()
            for rasp in self.rasps:
                sem_ids_ = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
                for sem_id in sem_ids_:
                    sem_ids.add(sem_id)

            grade_rooms = {"roomScore": 0, "capacityScore": 0, "computerScore": 0}
            grades = {"rooms": {room_id:grade_rooms.copy() for room_id in rooms_occupied},
                      "profs": {rasp.professor_id:0 for rasp in self.rasps},
                      "nasts": {sem_id:0 for sem_id in sem_ids},
                      "all": grade_obj.copy()}

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

                self.tax_rrule_in_rooms(slot, rooms_occupied[slot.room_id], rasp, rasp_rrules[rasp.id]["all_dates"], grades)
                self.tax_rrule_in_profs(slot, profs_occupied[rasp.professor_id], rasp, rasp_rrules[rasp.id]["all_dates"], grades)
                self.tax_rasp_nasts(slot, rasp, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied, grades)
                self.tax_capacity_computers(slot, rasp, grades)

                timetable[rasp] = slot

            data = {"grades":grades,
                    "timetable":timetable,
                    "rooms_occupied":rooms_occupied,
                    "profs_occupied":profs_occupied,
                    "nasts_occupied":dict(**nasts_occupied),
                    "optionals_occupied": dict(**optionals_occupied),
                    "groups_occupied": groups_occupied,
                    "rasp_rrules": rasp_rrules}
            sample.append(data)

        return sample


    def tax_rasp_nasts(self, slot, rasp, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied, grades):
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        key = str(rasp.subject_id) + str(rasp.type)
        for sem_id in sem_ids:
            rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
            parallel_optionals = True if self.semesters_info[sem_id].has_optional_subjects == 1 else False
            if rasp.total_groups == 1:
                if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                    # Tax semester fully
                    self.tax_rrule_in_nasts(sem_id, nasts_occupied[sem_id], rasp, all_dates, grades)
                elif not rasp_mandatory and parallel_optionals:
                    # Tax only if it's the first optional at that slot
                    self.nast_tax_rrule_optional_rasp(sem_id, nasts_occupied[sem_id], optionals_occupied[sem_id], rasp, slot.hour, all_dates, grades)

            elif rasp.total_groups > 1:
                if slot not in groups_occupied[key]:
                    groups_occupied[key][slot] = 0
                if rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Tax only if it's the first "subject_id + type" at that slot
                    self.tax_rrule_in_nasts(sem_id, nasts_occupied[sem_id], rasp, all_dates, grades)
                elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Tax only if it's the first "subject_id + type" at that slot AND first optional at that slot
                    self.nast_tax_rrule_optional_rasp(sem_id, nasts_occupied[sem_id], optionals_occupied[sem_id], rasp, slot.hour, all_dates, grades)

                #assert groups_occupied[key][slot] >= 0
                groups_occupied[key][slot] += 1



    def untax_rasp_nasts(self, slot, rasp, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied, grades):
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        key = str(rasp.subject_id) + str(rasp.type)
        for sem_id in sem_ids:
            rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
            parallel_optionals = True if self.semesters_info[sem_id].has_optional_subjects == 1 else False
            if rasp.total_groups == 1:
                if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                    # Untax semester
                    self.untax_rrule_in_nasts(sem_id, nasts_occupied[sem_id], rasp, all_dates, grades)
                elif not rasp_mandatory and parallel_optionals:
                    # Untax only if it's the last optional at that slot
                    self.nast_untax_rrule_optional_rasp(sem_id, nasts_occupied[sem_id], optionals_occupied[sem_id], rasp, slot.hour, all_dates, grades)

            elif rasp.total_groups > 1:
                groups_occupied[key][slot] -= 1
                assert groups_occupied[key][slot] >= 0
                if rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Untax only if it's the last "subject_id + type" at that slot
                    self.untax_rrule_in_nasts(sem_id, nasts_occupied[sem_id], rasp, all_dates, grades)
                elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Untax only if it's the last "subject_id + type" at that slot AND last optional at that slot
                    self.nast_untax_rrule_optional_rasp(sem_id, nasts_occupied[sem_id], optionals_occupied[sem_id], rasp, slot.hour, all_dates, grades)


    def nast_untax_rrule_optional_rasp(self, sem_id, nast_occupied, optionals_occupied, rasp, hour, rrule_dates, grades):
        self.untax_rrule_in_matrix3D(optionals_occupied, rasp, rrule_dates)
        for week, day, _ in rrule_dates:
            cnt = 0
            for hr in range(hour, hour + rasp.duration):
                if optionals_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] -= 1
                    if nast_occupied[week, day, hr]>=1:
                        cnt += 1
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, rasp, punish, grades, plus=False)


    def nast_tax_rrule_optional_rasp(self, sem_id, nast_occupied, optionals_occupied, rasp, hour, rrule_dates, grades):
        for week, day, _ in rrule_dates:
            cnt = 0
            for hr in range(hour, hour + rasp.duration):
                if optionals_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] += 1
                    if nast_occupied[week, day, hr]>1:
                        cnt += 1
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, rasp, punish, grades, plus=True)

            optionals_occupied[week, day, hour:(hour + rasp.duration)] += 1
        #self.tax_rrule_in_matrix3D(optionals_occupied, rasp, rrule_dates)


    def untax_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] -= 1


    def tax_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1


    def update_grades_profs(self, slot, rasp, punish, grades, plus=True):
        if plus:
            grades["profs"][rasp.professor_id] += punish
            grades["all"]["professorScore"] += punish
            grades["all"]["totalScore"] += punish
        else:
            grades["profs"][rasp.professor_id] -= punish
            grades["all"]["professorScore"] -= punish
            grades["all"]["totalScore"] -= punish


    def update_grades_rooms(self, slot, rasp, punish, grades, plus=True):
        if plus:
            grades["rooms"][slot.room_id]["roomScore"] += punish
            grades["all"]["roomScore"] += punish
            grades["all"]["totalScore"] += punish
        else:
            grades["rooms"][slot.room_id]["roomScore"] -= punish
            grades["all"]["roomScore"] -= punish
            grades["all"]["totalScore"] -= punish


    def update_grades_nasts(self, sem_id, rasp, punish, grades, plus=True):
        if plus:
            grades["nasts"][sem_id] += punish
            grades["all"]["nastScore"] += punish
            grades["all"]["totalScore"] += punish
        else:
            grades["nasts"][sem_id] -= punish
            grades["all"]["nastScore"] -= punish
            grades["all"]["totalScore"] -= punish


    def untax_capacity_computers(self, old_slot, rasp, grades):
        if bool(self.students_estimate[rasp.id] - self.room_capacity[old_slot.room_id]>=0):
            grades["all"]["capacityScore"] -= -30
            grades["all"]["totalScore"] -= -30

        if not old_slot.room_id in self.computer_rooms and rasp.needs_computers:
            grades["all"]["computerScore"] -= -30
            grades["all"]["totalScore"] -= -30

        if old_slot.room_id in self.computer_rooms and not rasp.needs_computers:
            grades["all"]["computerScore"] -= round(-30*0.1,2)
            grades["all"]["totalScore"] -= round(-30*0.1,2)


    def tax_capacity_computers(self, slot, rasp, grades):
        if bool(self.students_estimate[rasp.id] - self.room_capacity[slot.room_id]>=0):
            grades["all"]["capacityScore"] += -30
            grades["all"]["totalScore"] += -30

        if not slot.room_id in self.computer_rooms and rasp.needs_computers:
            grades["all"]["computerScore"] += -30
            grades["all"]["totalScore"] += -30

        if slot.room_id in self.computer_rooms and not rasp.needs_computers:
            grades["all"]["computerScore"] += round(-30*0.1,2)
            grades["all"]["totalScore"] += round(-30*0.1,2)


    def tax_rrule_in_rooms(self, slot, matrix3D, rasp, rrule_dates, grades):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1
            cnt = np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>1)
            if cnt:
                punish = -cnt*30
                self.update_grades_rooms(slot, rasp, punish, grades, plus=True)


    def tax_rrule_in_profs(self, slot, matrix3D, rasp, rrule_dates, grades):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1
            cnt = np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>1)
            if cnt:
                punish = -cnt*30
                self.update_grades_profs(slot, rasp, punish, grades, plus=True)


    def tax_rrule_in_nasts(self, sem_id, matrix3D, rasp, rrule_dates, grades):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] += 1
            cnt = np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>1)
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, rasp, punish, grades, plus=True)


    def untax_rrule_in_rooms(self, slot, matrix3D, rasp, rrule_dates, grades):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] -= 1
            cnt = np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>=1)
            if cnt:
                punish = -cnt*30
                self.update_grades_rooms(slot, rasp, punish, grades, plus=False)


    def untax_rrule_in_profs(self, slot, matrix3D, rasp, rrule_dates, grades):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] -= 1
            cnt = np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>=1)
            if cnt:
                punish = -cnt*30
                self.update_grades_profs(slot, rasp, punish, grades, plus=False)


    def untax_rrule_in_nasts(self, sem_id, matrix3D, rasp, rrule_dates, grades):
        for week, day, hour in rrule_dates:
            matrix3D[week, day, hour:(hour + rasp.duration)] -= 1
            cnt = np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>=1)
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, rasp, punish, grades, plus=False)


    def count_rrule_in_matrix3D(self, matrix3D, rasp, rrule_dates):
        return sum(np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]>1)
                   for week, day, hour in rrule_dates)


    #Just for testing
    def iterate_no_parallel(self, sample, generations=1000, starting_generation=1, population_cap=5):
        BEST_SAMPLE = (sample[0]["grades"]["all"].copy(), sample[0]["timetable"].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        fruitless_attempts = 0
        for generation in tqdm(range(starting_generation, starting_generation+generations)):
                #print("SAMPLE: ", self.get_size(sample) / 10**6, "MB.")
                the_samples = [s for s in sample]
                for s in the_samples:
                    better_grade = self.find_better_grade(s)
                    sample.append(better_grade)

                sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x["grades"]["all"]["totalScore"], reverse=True)
                sample = sample[0:population_cap]

                if sample[0]["grades"]["all"]["totalScore"] <= BEST_SAMPLE[0]["totalScore"]:
                    fruitless_attempts += 1

                if sample[0]["grades"]["all"]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    fruitless_attempts = 0
                    BEST_SAMPLE = (sample[0]["grades"]["all"].copy() , sample[0]["timetable"].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

                if sample[0]["grades"]["all"]["totalScore"] == 0:
                    return sample

                if fruitless_attempts == 10:
                    print("10 fruitless attempts - Exiting.")
                    return sample


        return sample


    def get_slots(self, rasp, rooms_occupied, week, day, hour = None):
        pool = set()
        for room_id in rooms_occupied:
            if hour and np.all(rooms_occupied[room_id][week, day, hour:(hour+rasp.duration)]==0):
                pool.add(Slot(room_id, week, day, hour))
            elif not hour:
                for hr in range(self.NUM_HOURS):
                    if hr+rasp.duration >= self.NUM_HOURS:
                        break
                    if np.all(rooms_occupied[room_id][week, day, hr:(hr+rasp.duration)]==0):
                        pool.add(Slot(room_id, week, day, hr))
        return pool


    def find_better_grade(self, data):
        old_timetable = data["timetable"]
        rasp_rrules = data["rasp_rrules"]
        rooms_occupied = data["rooms_occupied"]
        profs_occupied = data["profs_occupied"]
        nasts_occupied = data["nasts_occupied"]
        optionals_occupied = data["optionals_occupied"]
        groups_occupied = data["groups_occupied"]
        grades = data["grades"]

        why_ = {}
        problematic_rasps = []
        prob_profs = set()
        for rasp, (room_id, week, day, hour) in old_timetable.items():
            why_[rasp.id] = set()
            sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
            #if (not room_id in self.computer_rooms and rasp.needs_computers) or \
            #   (room_id in self.computer_rooms and not rasp.needs_computers) or \
            #   bool(self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0) or \
            #   any(profs_occupied[rasp.professor_id][week, day, hour:(hour+rasp.duration)]>1) or \
            #   any(rooms_occupied[room_id][week, day, hour:(hour+rasp.duration)]>1) or \
            #   any(any(nasts_occupied[sem_id][week, day, hour:(hour+rasp.duration)]>1) for sem_id in sem_ids):
            #    problematic_rasps.append(rasp)

            if (not room_id in self.computer_rooms and rasp.needs_computers) or (room_id in self.computer_rooms and not rasp.needs_computers):
                why_[rasp.id].add("computers")
            if bool(self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0):
                why_[rasp.id].add("capacity")
            if any(profs_occupied[rasp.professor_id][week, day, hour:(hour+rasp.duration)]>1):
                why_[rasp.id].add("professors")
                prob_profs.add((rasp.professor_id, rasp.id))
            if any(rooms_occupied[room_id][week, day, hour:(hour+rasp.duration)]>1):
                why_[rasp.id].add("rooms")
            if any(any(nasts_occupied[sem_id][week, day, hour:(hour+rasp.duration)]>1) for sem_id in sem_ids):
                why_[rasp.id].add("nasts")

            if len(why_[rasp.id]):
               problematic_rasps.append(rasp)

        if not problematic_rasps:
            return data

        new_timetable = old_timetable.copy()

        # Choose a random problematic rasp
        rasp0 = random.choice(problematic_rasps)
        old_slot = new_timetable[rasp0]
        new_timetable.pop(rasp0, 0)

        ## This takes a while
        pool = set()
        if rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, _ = time_api.date_to_index(dtstart_weekday)
                pool |= self.get_slots(rasp0, rooms_occupied, given_week, given_day)

        elif rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp0.id]["dtstart_weekdays"]
            for dtstart_weekday in dtstart_weekdays:
                given_week, given_day, given_hour = time_api.date_to_index(dtstart_weekday)
                pool |= self.get_slots(rasp0, rooms_occupied, given_week, given_day, given_hour)

        elif not rasp0.random_dtstart_weekday and not rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, _ = time_api.date_to_index(dtstart)
            pool |= self.get_slots(rasp0, rooms_occupied, given_week, given_day)

        elif not rasp0.random_dtstart_weekday and rasp0.fixed_hour:
            dtstart = rasp_rrules[rasp0.id]["DTSTART"]
            given_week, given_day, given_hour = time_api.date_to_index(dtstart)
            pool |= self.get_slots(rasp0, rooms_occupied, given_week, given_day, given_hour)

        #TODO: I once got a rasp0 without any "all_dates", also its occupied was all 0

        #print("nasts b4: ", nasts_occupied[old_slot.room_id][old_slot.week, old_slot.day, old_slot.hour])

        BEFORE_GRADE = grades["all"].copy()
        self.untax_rrule_in_rooms(old_slot, rooms_occupied[old_slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
        self.untax_rrule_in_profs(old_slot, profs_occupied[rasp0.professor_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
        self.untax_rasp_nasts(old_slot, rasp0, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied, grades)
        self.untax_capacity_computers(old_slot, rasp0, grades)

        # This takes a while
        pool_list = list(pool)
        random.shuffle(pool_list)
        the_slot = None

        old_rrules = rasp_rrules[rasp0.id].copy()
        skip = set()
        for slot in pool_list:
            if (slot.day, slot.hour) in skip:
                continue

            if slot.room_id in skip:
                continue

            NEW_DTSTART = time_api.index_to_date(slot.week, slot.day, slot.hour)
            NEW_UNTIL = rasp_rrules[rasp0.id]["UNTIL"]
            until_week, until_day, _ = time_api.date_to_index(NEW_UNTIL)
            NEW_UNTIL = time_api.index_to_date(until_week, until_day, slot.hour)

            rasp_rrules[rasp0.id]["DTSTART"] = NEW_DTSTART
            rasp_rrules[rasp0.id]["UNTIL"] = NEW_UNTIL
            rasp_rrules[rasp0.id]["all_dates"] = time_api.get_rrule_dates(rasp0.rrule, NEW_DTSTART, NEW_UNTIL)

            self.tax_rrule_in_rooms(slot, rooms_occupied[slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
            self.tax_rrule_in_profs(slot, profs_occupied[rasp0.professor_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
            self.tax_rasp_nasts(slot, rasp0, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied, grades)
            self.tax_capacity_computers(slot, rasp0, grades)

            if grades["all"]["totalScore"] > BEFORE_GRADE["totalScore"]:
                the_slot = slot
                break

            percent_prof_nast = ((grades["all"]["professorScore"] + grades["all"]["nastScore"]) / grades["all"]["totalScore"])
            percent_room = ((grades["all"]["capacityScore"] + grades["all"]["computerScore"] + grades["all"]["roomScore"]) / grades["all"]["totalScore"])
            if percent_prof_nast >= 0.7:
                skip.add((slot.day, slot.hour))
            if percent_room >= 0.7:
                skip.add(slot.room_id)

            self.untax_rrule_in_rooms(slot, rooms_occupied[slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
            self.untax_rrule_in_profs(slot, profs_occupied[rasp0.professor_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
            self.untax_rasp_nasts(slot, rasp0, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied, grades)
            self.untax_capacity_computers(slot, rasp0, grades)


        if not the_slot:
            print("nothing find better")
            new_timetable[rasp0] = old_slot
            rasp_rrules[rasp0.id] = old_rrules
            self.tax_rrule_in_rooms(old_slot, rooms_occupied[old_slot.room_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
            self.tax_rrule_in_profs(old_slot, profs_occupied[rasp0.professor_id], rasp0, rasp_rrules[rasp0.id]["all_dates"], grades)
            self.tax_rasp_nasts(old_slot, rasp0, rasp_rrules, nasts_occupied, optionals_occupied, groups_occupied, grades)
            self.tax_capacity_computers(old_slot, rasp0, grades)
            return data

        slot = the_slot

        new_timetable[rasp0] = slot
        data["timetable"] = new_timetable

        return data
