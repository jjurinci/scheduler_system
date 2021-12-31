import random
import numpy as np
from tqdm import tqdm
from collections import defaultdict
from dateutil.rrule import rrulestr
import data_api.time_structure as time_api
from data_api.utilities.my_types import Slot
from data_api.utilities.get_size import get_size
import optimizer.grade_tool as grade_tool

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
        self.semesters_info = data["semesters_info"]
        self.rooms_occupied = dict(**data["rooms_occupied"])
        self.profs_occupied = dict(**data["profs_occupied"])


    def get_all_semester_ids(self, rasps):
        all_sem_ids = set()
        for rasp in rasps:
            rasp_sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
            for sem_id in rasp_sem_ids:
                all_sem_ids.add(sem_id)
        return all_sem_ids


    def init_groups_occupied(self, rasps):
        groups_occupied = {}
        for rasp in rasps:
            if rasp.total_groups > 1:
                key = str(rasp.subject_id) + str(rasp.type)
                groups_occupied[key] = {}
        return groups_occupied


    def init_grades(self, rasps, rooms_occupied):
        sem_ids = self.get_all_semester_ids(rasps)
        grade_obj = {"totalScore": 0, "roomScore": 0, "professorScore": 0,
                     "capacityScore": 0, "computerScore": 0, "nastScore": 0}
        grade_rooms = {"roomScore": 0, "capacityScore": 0, "computerScore": 0}
        grades = {"rooms": {room_id:grade_rooms.copy() for room_id in rooms_occupied},
                  "profs": {rasp.professor_id:0 for rasp in self.rasps},
                  "nasts": {sem_id:0 for sem_id in sem_ids},
                  "all": grade_obj.copy()}
        return grades


    def init_rrule_objects(self, rasps):
        rasp_rrules, possible_rrules = {}, {}
        for rasp in rasps:
            rrule_obj = rrulestr(rasp.rrule)
            dtstart = rrule_obj._dtstart
            until = rrule_obj._until
            dtstart_weekdays = time_api.all_dtstart_weekdays(dtstart) if rasp.random_dtstart_weekday else []

            # At most 5 starting days defined by (week, day). Since we don't allow hour manipulation I can leave out the hour
            possible_rrules[rasp.id] = {}
            if rasp.random_dtstart_weekday:
                for dtstart_weekday in dtstart_weekdays:
                    given_week, given_day, _ = time_api.date_to_index(dtstart_weekday)
                    key = (given_week, given_day)
                    rrule_obj = {"all_dates": time_api.get_rrule_dates(rasp.rrule, dtstart_weekday, until)}
                    rrule_obj["all_dates"] = list(rrule_obj["all_dates"])
                    for i, val in enumerate(rrule_obj["all_dates"]):
                        rrule_obj["all_dates"][i] = (val[0], val[1])
                    possible_rrules[rasp.id][key] = rrule_obj

            elif not rasp.random_dtstart_weekday:
                rrule_obj = {"all_dates": time_api.get_rrule_dates(rasp.rrule, dtstart, until)}
                rrule_obj["all_dates"] = list(rrule_obj["all_dates"])
                for i, val in enumerate(rrule_obj["all_dates"]):
                    rrule_obj["all_dates"][i] = (val[0], val[1])
                possible_rrules[rasp.id][key] = rrule_obj

            dtstart_weekdays = [time_api.date_to_index(dtstart_) for dtstart_ in dtstart_weekdays]
            dtstart = time_api.date_to_index(dtstart)
            until = time_api.date_to_index(until)
            rasp_rrules[rasp.id] = {"DTSTART": dtstart, "UNTIL": until, "dtstart_weekdays":dtstart_weekdays, "all_dates":[]}

        return rasp_rrules, possible_rrules


    def update_rasp_rrules(self, slot, rasp, rasp_rrules, possible_rrules):
        key = (slot.week, slot.day)
        all_dates = [(week, day, slot.hour) for week, day in possible_rrules[rasp.id][key]["all_dates"]]
        rasp_rrules[rasp.id]["DTSTART"] = all_dates[0]
        rasp_rrules[rasp.id]["UNTIL"] = all_dates[-1]
        rasp_rrules[rasp.id]["all_dates"] = all_dates


    def random_sample(self, N):
        sample = []
        for i in range(N):
            print(i)
            timetable = {}
            rooms_occupied = {k:v.copy() for k,v in self.rooms_occupied.items()}
            profs_occupied = {k:v.copy() for k,v in self.profs_occupied.items()}
            nasts_occupied = defaultdict(lambda: np.zeros((self.NUM_WEEKS, 5, self.NUM_HOURS), dtype=np.uint8))
            optionals_occupied = defaultdict(lambda: np.zeros((self.NUM_WEEKS, 5, self.NUM_HOURS), dtype=np.uint8))
            groups_occupied = self.init_groups_occupied(self.rasps)
            grades = self.init_grades(self.rasps, rooms_occupied)
            rasp_rrules, possible_rrules = self.init_rrule_objects(self.rasps)

            seen_avs = set()
            for rasp in self.rasps:
                slot = None
                while not slot:
                    pool = self.get_rasp_slots(rasp, rasp_rrules, rooms_occupied)
                    pool -= seen_avs
                    try_slot = random.choice(tuple(pool))
                    if try_slot.hour + rasp.duration < self.NUM_HOURS:
                        slot = try_slot

                seen_avs.add(slot)
                self.update_rasp_rrules(slot, rasp, rasp_rrules, possible_rrules)
                self.tax_all_constraints(slot, rasp, rasp_rrules[rasp.id]["all_dates"], rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades)
                timetable[rasp] = slot

            data = {"grades":grades,
                    "timetable":timetable,
                    "rooms_occupied":rooms_occupied,
                    "profs_occupied":profs_occupied,
                    "nasts_occupied":dict(**nasts_occupied),
                    "optionals_occupied": dict(**optionals_occupied),
                    "groups_occupied": groups_occupied,
                    "rasp_rrules": rasp_rrules,
                    "possible_rrules": possible_rrules,
                    "unsuccessful_rasps": set(),
                    "converged": False}

            sample.append(data)
        sample.sort(key=lambda data: data["grades"]["all"]["totalScore"], reverse=True)
        return sample


    def tax_all_constraints(self, slot, rasp, all_dates, rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades):
        self.tax_rrule_in_rooms(slot.room_id, rasp, all_dates, rooms_occupied[slot.room_id], grades)
        self.tax_rrule_in_profs(rasp, all_dates, profs_occupied[rasp.professor_id], grades)
        self.tax_rrule_in_nasts(slot, rasp, all_dates, nasts_occupied, optionals_occupied, groups_occupied, grades)
        self.tax_capacity(slot.room_id, rasp, grades)
        self.tax_computers(slot.room_id, rasp, grades)


    def untax_all_constraints(self, slot, rasp, all_dates, rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades):
        self.untax_rrule_in_rooms(slot.room_id, rasp, all_dates, rooms_occupied[slot.room_id], grades)
        self.untax_rrule_in_profs(rasp, all_dates, profs_occupied[rasp.professor_id], grades)
        self.untax_rasp_nasts(slot, rasp, all_dates, nasts_occupied, optionals_occupied, groups_occupied, grades)
        self.untax_capacity(slot.room_id, rasp, grades)
        self.untax_computers(slot.room_id, rasp, grades)


    def tax_rrule_in_nasts(self, slot, rasp, all_dates, nasts_occupied, optionals_occupied, groups_occupied, grades):
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        key = str(rasp.subject_id) + str(rasp.type)
        for sem_id in sem_ids:
            rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
            parallel_optionals = True if self.semesters_info[sem_id].has_optional_subjects == 1 else False
            if rasp.total_groups == 1:
                if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                    # Tax semester fully
                    self.tax_mandatory_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], grades)
                elif not rasp_mandatory and parallel_optionals:
                    # Tax only if it's the first optional at that slot
                    self.tax_optional_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], optionals_occupied[sem_id], grades)

            elif rasp.total_groups > 1:
                if slot not in groups_occupied[key]:
                    groups_occupied[key][slot] = 0
                if rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Tax only if it's the first "subject_id + type" at that slot
                    self.tax_mandatory_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], grades)
                elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Tax only if it's the first "subject_id + type" at that slot AND first optional at that slot
                    self.tax_optional_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], optionals_occupied[sem_id], grades)
                #assert groups_occupied[key][slot] >= 0
                groups_occupied[key][slot] += 1


    def untax_rasp_nasts(self, slot, rasp, all_dates, nasts_occupied, optionals_occupied, groups_occupied, grades):
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        key = str(rasp.subject_id) + str(rasp.type)
        for sem_id in sem_ids:
            rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
            parallel_optionals = True if self.semesters_info[sem_id].has_optional_subjects == 1 else False
            if rasp.total_groups == 1:
                if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                    # Untax semester
                    self.untax_mandatory_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], grades)
                elif not rasp_mandatory and parallel_optionals:
                    # Untax only if it's the last optional at that slot
                    self.untax_optional_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], optionals_occupied[sem_id], grades)

            elif rasp.total_groups > 1:
                groups_occupied[key][slot] -= 1
                assert groups_occupied[key][slot] >= 0
                if rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Untax only if it's the last "subject_id + type" at that slot
                    self.untax_mandatory_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], grades)
                elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                    # Untax only if it's the last "subject_id + type" at that slot AND last optional at that slot
                    self.untax_optional_in_nasts(sem_id, rasp, all_dates, nasts_occupied[sem_id], optionals_occupied[sem_id], grades)


    def untax_optional_in_nasts(self, sem_id, rasp, all_dates, nast_occupied, optionals_occupied, grades):
        for week, day, hour in all_dates:
            optionals_occupied[week, day, hour:(hour + rasp.duration)] -= 1
        for week, day, hour in all_dates:
            cnt = 0
            for hr in range(hour, hour + rasp.duration):
                if optionals_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] -= 1
                    if nast_occupied[week, day, hr]>=1:
                        cnt += 1
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, punish, grades, plus=False)


    def tax_optional_in_nasts(self, sem_id, rasp, all_dates, nast_occupied, optional_occupied, grades):
        for week, day, hour in all_dates:
            cnt = 0
            for hr in range(hour, hour + rasp.duration):
                if optional_occupied[week, day, hr] == 0.0:
                    nast_occupied[week, day, hr] += 1
                    if nast_occupied[week, day, hr]>1:
                        cnt += 1
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, punish, grades, plus=True)
            optional_occupied[week, day, hour:(hour + rasp.duration)] += 1


    def update_grades_profs(self, rasp, punish, grades, plus=True):
        if plus:
            grades["profs"][rasp.professor_id] += punish
            grades["all"]["professorScore"] += punish
            grades["all"]["totalScore"] += punish
        else:
            grades["profs"][rasp.professor_id] -= punish
            grades["all"]["professorScore"] -= punish
            grades["all"]["totalScore"] -= punish


    def update_grades_rooms(self, room_id, punish, grades, plus=True):
        if plus:
            grades["rooms"][room_id]["roomScore"] += punish
            grades["all"]["roomScore"] += punish
            grades["all"]["totalScore"] += punish
        else:
            grades["rooms"][room_id]["roomScore"] -= punish
            grades["all"]["roomScore"] -= punish
            grades["all"]["totalScore"] -= punish


    def update_grades_nasts(self, sem_id, punish, grades, plus=True):
        if plus:
            grades["nasts"][sem_id] += punish
            grades["all"]["nastScore"] += punish
            grades["all"]["totalScore"] += punish
        else:
            grades["nasts"][sem_id] -= punish
            grades["all"]["nastScore"] -= punish
            grades["all"]["totalScore"] -= punish


    def untax_capacity(self, room_id, rasp, grades):
        if bool(self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0):
            grades["all"]["capacityScore"] += 30
            grades["all"]["totalScore"] += 30


    def tax_capacity(self, room_id, rasp, grades):
        if bool(self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0):
            grades["all"]["capacityScore"] += -30
            grades["all"]["totalScore"] += -30


    def untax_computers(self, room_id, rasp, grades):
        if not room_id in self.computer_rooms and rasp.needs_computers:
            grades["all"]["computerScore"] += 30
            grades["all"]["totalScore"] += 30

        if room_id in self.computer_rooms and not rasp.needs_computers:
            grades["all"]["computerScore"] += 30 * 0.1
            grades["all"]["totalScore"] += 30 * 0.1


    def tax_computers(self, room_id, rasp, grades):
        if not room_id in self.computer_rooms and rasp.needs_computers:
            grades["all"]["computerScore"] += -30
            grades["all"]["totalScore"] += -30

        if room_id in self.computer_rooms and not rasp.needs_computers:
            grades["all"]["computerScore"] += -30*0.1
            grades["all"]["totalScore"] += -30*0.1


    def tax_rrule_in_rooms(self, room_id, rasp, all_dates, room_occupied, grades):
        for week, day, hour in all_dates:
            room_occupied[week, day, hour:(hour + rasp.duration)] += 1
            cnt = np.sum(room_occupied[week, day, hour:(hour + rasp.duration)]>1)
            if cnt:
                punish = -cnt*30
                self.update_grades_rooms(room_id, punish, grades, plus=True)


    def tax_rrule_in_profs(self, rasp, all_dates, prof_occupied, grades):
        for week, day, hour in all_dates:
            prof_occupied[week, day, hour:(hour + rasp.duration)] += 1
            cnt = np.sum(prof_occupied[week, day, hour:(hour + rasp.duration)]>1)
            if cnt:
                punish = -cnt*30
                self.update_grades_profs(rasp, punish, grades, plus=True)


    def tax_mandatory_in_nasts(self, sem_id, rasp, all_dates, nast_occupied, grades):
        for week, day, hour in all_dates:
            nast_occupied[week, day, hour:(hour + rasp.duration)] += 1
            cnt = np.sum(nast_occupied[week, day, hour:(hour + rasp.duration)]>1)
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, punish, grades, plus=True)


    def untax_rrule_in_rooms(self, room_id, rasp, all_dates, room_occupied, grades):
        for week, day, hour in all_dates:
            cnt = np.sum(room_occupied[week, day, hour:(hour + rasp.duration)]>1)
            room_occupied[week, day, hour:(hour + rasp.duration)] -= 1
            if cnt:
                punish = -cnt*30
                self.update_grades_rooms(room_id, punish, grades, plus=False)


    def untax_rrule_in_profs(self, rasp, all_dates, prof_occupied, grades):
        for week, day, hour in all_dates:
            cnt = np.sum(prof_occupied[week, day, hour:(hour + rasp.duration)]>1)
            prof_occupied[week, day, hour:(hour + rasp.duration)] -= 1
            if cnt:
                punish = -cnt*30
                self.update_grades_profs(rasp, punish, grades, plus=False)


    def untax_mandatory_in_nasts(self, sem_id, rasp, all_dates, nast_occupied, grades):
        for week, day, hour in all_dates:
            cnt = np.sum(nast_occupied[week, day, hour:(hour + rasp.duration)]>1)
            nast_occupied[week, day, hour:(hour + rasp.duration)] -= 1
            if cnt:
                punish = -cnt*30
                self.update_grades_nasts(sem_id, punish, grades, plus=False)


    def iterate_no_parallel(self, sample, generations=1000, starting_generation=1, population_cap=5):
        BEST_SAMPLE = (sample[0]["grades"]["all"].copy(), sample[0]["timetable"].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        for generation in tqdm(range(starting_generation, starting_generation+generations)):
                #print("SAMPLE: ", self.get_size(sample) / 10**6, "MB.")
                the_samples = [s for s in sample]
                for s in the_samples:
                    better_grade = self.find_better_grade(s)
                    sample.append(better_grade)

                sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x["grades"]["all"]["totalScore"], reverse=True)
                sample = sample[0:population_cap]

                if sample[0]["grades"]["all"]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0]["grades"]["all"].copy() , sample[0]["timetable"].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

                if sample[0]["grades"]["all"]["totalScore"] == 0:
                    return sample

                elif sample[0]["converged"]:
                    print("No 0 score solution.")
                    return sample

        return sample


    def get_possible_slots(self, rasp, rooms_occupied, week, day, hour = None):
        if hour:
            return set([Slot(room_id, week, day, hour)
                        for room_id in rooms_occupied])
        else:
            return set([Slot(room_id, week, day, hr)
                        for room_id in rooms_occupied
                        for hr in range(self.NUM_HOURS)
                        if hr+rasp.duration < self.NUM_HOURS])


    def get_rasp_slots(self, rasp, rasp_rrules, rooms_occupied):
        pool = set()
        if rasp.random_dtstart_weekday and not rasp.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp.id]["dtstart_weekdays"]
            for given_week, given_day, _ in dtstart_weekdays:
                pool |= self.get_possible_slots(rasp, rooms_occupied, given_week, given_day)

        elif rasp.random_dtstart_weekday and rasp.fixed_hour:
            dtstart_weekdays = rasp_rrules[rasp.id]["dtstart_weekdays"]
            for given_week, given_day, given_hour in dtstart_weekdays:
                pool |= self.get_possible_slots(rasp, rooms_occupied, given_week, given_day, given_hour)

        elif not rasp.random_dtstart_weekday and not rasp.fixed_hour:
            given_week, given_day, _ = rasp_rrules[rasp.id]["DTSTART"]
            pool |= self.get_possible_slots(rasp, rooms_occupied, given_week, given_day)

        elif not rasp.random_dtstart_weekday and rasp.fixed_hour:
            given_week, given_day, given_hour = rasp_rrules[rasp.id]["DTSTART"]
            pool |= self.get_possible_slots(rasp, rooms_occupied, given_week, given_day, given_hour)
        return pool


    def failure_reason(self, action, slot, new_grade_with_new_slot, old_grade_without_old_slot, pure_old_slot_grade):
        pure_new_slot_grade = {k:new_grade_with_new_slot[k] -
                               old_grade_without_old_slot[k]
                               for k in new_grade_with_new_slot}

        old_total     = pure_old_slot_grade["totalScore"]
        new_professor = pure_new_slot_grade["professorScore"]
        new_nast      = pure_new_slot_grade["nastScore"]
        new_capacity  = pure_new_slot_grade["capacityScore"]
        new_computer  = pure_new_slot_grade["computerScore"]
        _, week, day, hr = slot

        if new_professor + new_nast <= old_total:
            action["ban_dates"].add((week, day, hr))

        if new_capacity <= old_total:
            action["ban_capacity"] = True

        if new_computer <= old_total:
            action["ban_computers"] = True

        if new_professor + new_nast + new_capacity <= old_total:
            action["ban_capacity_with_dates"].add((week, day, hr))

        if new_professor + new_nast + new_computer <= old_total:
            action["ban_computers_with_dates"].add((week, day, hr))

        if new_capacity + new_computer <= old_total:
            action["ban_capacity_with_computers"] = True

        if new_professor + new_nast + new_capacity + new_computer <= old_total:
            action["ban_dates_with_capacity_with_computers"].add((week, day, hr))


    def insufficient_capacity(self, rasp, room_id):
        return self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0


    def insufficient_computers(self, rasp, room_id):
        return ((not room_id in self.computer_rooms and rasp.needs_computers) or (room_id in self.computer_rooms and not rasp.needs_computers))


    def is_skippable(self, slot, rasp, action):
        room_id, week,day,hr = slot
        if (week, day, hr) in action["ban_dates"]:
            return True
        if action["ban_capacity"] and self.insufficient_capacity(rasp, room_id):
            return True
        if action["ban_computers"] and self.insufficient_computers(rasp, room_id):
            return True
        if (week, day, hr) in action["ban_capacity_with_dates"] and self.insufficient_capacity(rasp, room_id):
            return True
        if (week, day, hr) in action["ban_computers_with_dates"] and self.insufficient_computers(rasp, room_id):
            return True
        if action["ban_capacity_with_computers"] and self.insufficient_computers(rasp, room_id) and self.insufficient_capacity(rasp, room_id):
            return True
        if (week, day, hr) in action["ban_dates_with_capacity_with_computers"] and self.insufficient_capacity(rasp, room_id) and self.insufficient_computers(rasp, room_id):
            return True
        return False


    def init_action(self):
        return {"ban_dates": set(),
                "ban_capacity": False,
                "ban_computers": False,
                "ban_capacity_with_dates": set(),
                "ban_computers_with_dates": set(),
                "ban_capacity_with_computers": False,
                "ban_dates_with_capacity_with_computers": set()}


    def find_better_grade(self, data):
        timetable = data["timetable"]
        rasp_rrules = data["rasp_rrules"]
        rooms_occupied = data["rooms_occupied"]
        profs_occupied = data["profs_occupied"]
        nasts_occupied = data["nasts_occupied"]
        optionals_occupied = data["optionals_occupied"]
        groups_occupied = data["groups_occupied"]
        grades = data["grades"]
        possible_rrules = data["possible_rrules"]

        # Pick a random problematic rasp
        rasps = list(timetable.keys())
        random.shuffle(rasps)
        rasp0 = None
        for rasp in rasps:
            if rasp.id in data["unsuccessful_rasps"]:
                continue
            room_id, _, _, _= timetable[rasp]
            if grade_tool.is_rasp_problematic(rasp, rasp_rrules[rasp.id]["all_dates"], room_id, rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, self.computer_rooms, self.room_capacity, self.students_estimate):
                rasp0 = rasp
                break

        if not rasp0:
            print("NO PROBLEMATIC RASPS.")
            data["converged"] = True
            return data

        old_slot = timetable[rasp0]
        old_grade_with_old_slot = grades["all"].copy()
        old_rrules = rasp_rrules[rasp0.id].copy()
        old_grade = grades["all"].copy()
        timetable.pop(rasp0, 0)
        pool = self.get_rasp_slots(rasp0, rasp_rrules, rooms_occupied)

        self.untax_all_constraints(old_slot, rasp0, rasp_rrules[rasp0.id]["all_dates"],
                                   rooms_occupied, profs_occupied, nasts_occupied,
                                   optionals_occupied, groups_occupied, grades)

        old_grade_without_old_slot = grades["all"].copy()
        pure_old_slot_grade = {k:old_grade_with_old_slot[k] - old_grade_without_old_slot[k] for k in old_grade_with_old_slot}

        #if pure old_slot_grade['totalScore'] is 0 here, it means I cannot improve it.
        #Also it means that it's not an problematic rasp. I'm not getting them now though.
        #Probably because of the improved problematic finding.
        assert pure_old_slot_grade["totalScore"] != 0 and all(x<=0 for x in pure_old_slot_grade.values())


        action = self.init_action()
        pool_list = list(pool)
        random.shuffle(pool_list)
        the_slot = None
        cnt = 0
        for new_slot in pool_list:
            if self.is_skippable(new_slot, rasp0, action):
                continue
            cnt += 1

            self.update_rasp_rrules(new_slot, rasp0, rasp_rrules, possible_rrules)
            self.tax_all_constraints(new_slot, rasp0, rasp_rrules[rasp0.id]["all_dates"], rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades)

            if grades["all"]["totalScore"] > old_grade["totalScore"]:
                the_slot = new_slot
                break

            if grades["all"]["totalScore"] != old_grade_with_old_slot["totalScore"]:
                self.failure_reason(action, new_slot, grades["all"],
                                    old_grade_without_old_slot, pure_old_slot_grade)

            self.untax_all_constraints(new_slot, rasp0, rasp_rrules[rasp0.id]["all_dates"], rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades)

        print("ITERS: ", cnt, rasp0.id)

        if not the_slot:
            data["unsuccessful_rasps"].add(rasp0.id)
            timetable[rasp0] = old_slot
            rasp_rrules[rasp0.id] = old_rrules
            self.tax_all_constraints(old_slot, rasp0, old_rrules["all_dates"], rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades)
            return data
        else:
            data["unsuccessful_rasps"] = set()

        timetable[rasp0] = the_slot
        return data
