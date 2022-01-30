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
        self.NUM_DAYS = 5
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
        rasp_rrules, possible_rrules, rasp_freqs = {}, {}, {}
        freqs = {0:"YEARLY", 1:"MONTHLY", 2:"WEEKLY", 3:"DAILY"}
        for rasp in rasps:
            rrule_obj = rrulestr(rasp.rrule)
            rasp_freqs[rasp.id] = freqs[rrule_obj._freq]
            dtstart = rrule_obj._dtstart
            until = rrule_obj._until
            dtstart_weekdays = time_api.all_dtstart_weekdays(dtstart) if rasp.random_dtstart_weekday else []

            # At most 5 starting days defined by (week, day). Since we don't allow hour manipulation we can leave out the hour
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

        return rasp_rrules, possible_rrules, rasp_freqs


    def update_rasp_rrules(self, slot, rasp, rasp_rrules, possible_rrules):
        key = (slot.week, slot.day)
        all_dates = [(week, day, slot.hour) for week, day in possible_rrules[rasp.id][key]["all_dates"]]
        rasp_rrules[rasp.id]["DTSTART"] = all_dates[0]
        rasp_rrules[rasp.id]["UNTIL"] = all_dates[-1]
        rasp_rrules[rasp.id]["all_dates"] = all_dates


    def random_timetable(self):
        print("Generating random timetable.")

        timetable = {}
        rooms_occupied = {k:v.copy() for k,v in self.rooms_occupied.items()}
        profs_occupied = {k:v.copy() for k,v in self.profs_occupied.items()}
        nasts_occupied = defaultdict(lambda: np.zeros((self.NUM_WEEKS, self.NUM_DAYS, self.NUM_HOURS), dtype=np.uint8))
        optionals_occupied = defaultdict(lambda: np.zeros((self.NUM_WEEKS, self.NUM_DAYS, self.NUM_HOURS), dtype=np.uint8))
        groups_occupied = self.init_groups_occupied(self.rasps)
        grades = self.init_grades(self.rasps, rooms_occupied)
        rasp_rrules, possible_rrules, rasp_freqs = self.init_rrule_objects(self.rasps)

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
                "rasp_freqs": rasp_freqs,
                "unsuccessful_rasps": set(),
                "converged": False}
        return data


    def count_all_constraints(self, slot, rasp, all_dates, rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied):
        grade_obj                   = {"totalScore": 0, "roomScore": 0, "professorScore": 0, "capacityScore": 0, "computerScore": 0, "nastScore": 0}
        grade_obj["roomScore"]      = self.count_rrule_in_matrix3D(rasp, all_dates, rooms_occupied[slot.room_id])
        grade_obj["professorScore"] = self.count_rrule_in_matrix3D(rasp, all_dates, profs_occupied[rasp.professor_id])
        grade_obj["nastScore"]      = self.count_rrule_in_nasts(slot, rasp, all_dates, nasts_occupied, optionals_occupied, groups_occupied)
        grade_obj["capacityScore"]  = -30 * self.insufficient_capacity(rasp, slot.room_id)
        grade_obj["computerScore"]  = -30 * self.insufficient_strong_computers(rasp, slot.room_id) + (-3 * self.insufficient_weak_computers(rasp, slot.room_id))
        grade_obj["totalScore"]     = sum(grade_obj.values())
        return grade_obj


    def count_rrule_in_matrix3D(self, rasp, all_dates, matrix3D):
        return -30 * sum(np.sum(matrix3D[week, day, hour:(hour + rasp.duration)]+1 > 1)
                     for week,day,hour in all_dates)


    def count_rrule_in_optional_rasp(self, rasp, all_dates, nast_occupied, optional_occupied):
        cnt = 0
        for week, day, hour in all_dates:
            for hr in range(hour, hour + rasp.duration):
                if optional_occupied[week, day, hr] == 0.0:
                    if nast_occupied[week, day, hr]+1 > 1:
                        cnt += 1
        return -30 * cnt


    def count_rrule_in_nasts(self, slot, rasp, all_dates, nasts_occupied, optionals_occupied, groups_occupied):
        sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
        key = str(rasp.subject_id) + str(rasp.type)
        grade = 0
        for sem_id in sem_ids:
            rasp_mandatory = True if sem_id in rasp.mandatory_in_semester_ids else False
            parallel_optionals = True if self.semesters_info[sem_id].has_optional_subjects == 1 else False
            if rasp.total_groups == 1:
                if rasp_mandatory or (not rasp_mandatory and not parallel_optionals):
                    grade += self.count_rrule_in_matrix3D(rasp, all_dates, nasts_occupied[sem_id])
                elif not rasp_mandatory and parallel_optionals:
                    grade += self.count_rrule_in_optional_rasp(rasp, all_dates, nasts_occupied[sem_id], optionals_occupied[sem_id])

            elif rasp.total_groups > 1:
                if slot not in groups_occupied[key]:
                    groups_occupied[key][slot] = 0
                if rasp_mandatory and groups_occupied[key][slot] == 0:
                    grade += self.count_rrule_in_matrix3D(rasp, all_dates, nasts_occupied[sem_id])
                elif not rasp_mandatory and groups_occupied[key][slot] == 0:
                    grade += self.count_rrule_in_optional_rasp(rasp, all_dates, nasts_occupied[sem_id], optionals_occupied[sem_id])
        return grade


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
                assert groups_occupied[key][slot] >= 0
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


    def iterate(self, data, iterations=1000):
        BEST_GRADE = data["grades"]["all"].copy()
        print(0, BEST_GRADE)

        for iteration in tqdm(range(iterations)):
            #print("DATA: ", get_size(data) / 10**6, "MB.")
            data = self.find_better_grade(data)

            if data["grades"]["all"]["totalScore"] > BEST_GRADE["totalScore"]:
                BEST_GRADE = data["grades"]["all"].copy()
                tqdm.write(f"{iteration}, {BEST_GRADE}")

            if data["grades"]["all"]["totalScore"] == 0:
                return data

            elif data["converged"]:
                print("No 0 score solution.")
                return data
        return data


    def get_possible_slots(self, rasp, rooms_occupied, week, day, hour = None):
        if hour != None: # hour=0 should trigger this if
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


    def failure_reason(self, action, slot, rasp, rasp_freqs, pure_new_slot_grade, pure_old_slot_grade):
        old_total     = pure_old_slot_grade["totalScore"]
        new_professor = pure_new_slot_grade["professorScore"]
        new_nast      = pure_new_slot_grade["nastScore"]
        new_capacity  = pure_new_slot_grade["capacityScore"]
        new_computer  = pure_new_slot_grade["computerScore"]
        _, week, day, hr = slot

        ban_slot = (day, hr) if rasp_freqs[rasp.id] == "WEEKLY" else (week, day, hr)

        if new_professor + new_nast <= old_total:
            action["ban_dates"].add(ban_slot)

        if new_capacity <= old_total:
            action["ban_capacity"] = True

        if new_computer <= old_total:
            action["ban_computers"] = True

        if new_professor + new_nast + new_capacity <= old_total:
            action["ban_capacity_with_dates"].add(ban_slot)

        if new_professor + new_nast + new_computer <= old_total:
            action["ban_computers_with_dates"].add(ban_slot)

        if new_capacity + new_computer <= old_total:
            action["ban_capacity_with_computers"] = True

        if new_professor + new_nast + new_capacity + new_computer <= old_total:
            action["ban_dates_with_capacity_with_computers"].add(ban_slot)


    def failure_reason_rigorous(self, action, slot, rasp, rasp_freqs, pure_new_slot_grade):
        new_professor = pure_new_slot_grade["professorScore"]
        new_nast      = pure_new_slot_grade["nastScore"]
        new_capacity  = pure_new_slot_grade["capacityScore"]
        new_computer  = pure_new_slot_grade["computerScore"]
        _, week, day, hr = slot

        ban_slot = (day, hr) if rasp_freqs[rasp.id] == "WEEKLY" else (week, day, hr)

        if new_professor + new_nast:
            action["ban_dates"].add(ban_slot)

        if new_capacity:
            action["ban_capacity"] = True

        if new_computer:
            action["ban_computers"] = True

        if new_professor + new_nast + new_capacity:
            action["ban_capacity_with_dates"].add(ban_slot)

        if new_professor + new_nast + new_computer:
            action["ban_computers_with_dates"].add(ban_slot)

        if new_capacity + new_computer:
            action["ban_capacity_with_computers"] = True

        if new_professor + new_nast + new_capacity + new_computer:
            action["ban_dates_with_capacity_with_computers"].add(ban_slot)


    def insufficient_capacity(self, rasp, room_id):
        return self.students_estimate[rasp.id] - self.room_capacity[room_id]>=0


    def insufficient_computers(self, rasp, room_id):
        return ((not room_id in self.computer_rooms and rasp.needs_computers) or (room_id in self.computer_rooms and not rasp.needs_computers))


    def insufficient_strong_computers(self, rasp, room_id):
        return not room_id in self.computer_rooms and rasp.needs_computers


    def insufficient_weak_computers(self, rasp, room_id):
        return room_id in self.computer_rooms and not rasp.needs_computers


    def is_skippable(self, slot, rasp, rasp_freqs, action):
        room_id, week,day,hr = slot
        ban_slot = (day, hr) if rasp_freqs[rasp.id] == "WEEKLY" else (week, day, hr)

        if ban_slot in action["ban_dates"]:
            return True
        if action["ban_capacity"] and self.insufficient_capacity(rasp, room_id):
            return True
        if action["ban_computers"] and self.insufficient_computers(rasp, room_id):
            return True
        if ban_slot in action["ban_capacity_with_dates"] and self.insufficient_capacity(rasp, room_id):
            return True
        if ban_slot in action["ban_computers_with_dates"] and self.insufficient_computers(rasp, room_id):
            return True
        if action["ban_capacity_with_computers"] and self.insufficient_computers(rasp, room_id) and self.insufficient_capacity(rasp, room_id):
            return True
        if ban_slot in action["ban_dates_with_capacity_with_computers"] and self.insufficient_capacity(rasp, room_id) and self.insufficient_computers(rasp, room_id):
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
        rasp_freqs = data["rasp_freqs"]

        # Pick a random problematic rasp
        rasps = list(timetable.keys())
        random.shuffle(rasps)
        rasp0 = None
        first_iters = 0
        for rasp in rasps:
            if rasp.id in data["unsuccessful_rasps"]:
                continue
            first_iters += 1
            room_id, _, _, _= timetable[rasp]
            if grade_tool.is_rasp_problematic(rasp, rasp_rrules[rasp.id]["all_dates"], room_id, rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, self.computer_rooms, self.room_capacity, self.students_estimate):
                rasp0 = rasp
                break

        print("FIRST ITERS: ", first_iters)

        if not rasp0:
            print("NO PROBLEMATIC RASPS.")
            data["converged"] = True
            return data

        old_slot = timetable[rasp0]
        old_grade_with_old_slot = grades["all"].copy()
        old_rrules = rasp_rrules[rasp0.id].copy()
        timetable.pop(rasp0, 0)
        pool = self.get_rasp_slots(rasp0, rasp_rrules, rooms_occupied)

        self.untax_all_constraints(old_slot, rasp0, rasp_rrules[rasp0.id]["all_dates"],
                                   rooms_occupied, profs_occupied, nasts_occupied,
                                   optionals_occupied, groups_occupied, grades)

        old_grade_without_old_slot = grades["all"].copy()
        pure_old_slot_grade = {k:old_grade_with_old_slot[k] - old_grade_without_old_slot[k] for k in old_grade_with_old_slot}

        #assert all(x<=0 for x in pure_old_slot_grade.values())

        need_same_score   = pure_old_slot_grade["totalScore"] == 0
        need_better_score = pure_old_slot_grade["totalScore"] != 0

        action = self.init_action()
        pool_list = list(pool)
        random.shuffle(pool_list)
        the_slot = None
        cnt, skipped = 0, 0
        new_grade_with_new_slot = None
        for new_slot in pool_list:
            if self.is_skippable(new_slot, rasp0, rasp_freqs, action):
                skipped += 1
                continue
            cnt += 1

            self.update_rasp_rrules(new_slot, rasp0, rasp_rrules, possible_rrules)

            pure_new_slot_grade = self.count_all_constraints(new_slot, rasp0, rasp_rrules[rasp0.id]["all_dates"], rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied)
            new_grade_with_new_slot = {k:old_grade_without_old_slot[k] + pure_new_slot_grade[k] for k in pure_new_slot_grade}

            got_same_score   = new_grade_with_new_slot["totalScore"] == old_grade_with_old_slot["totalScore"]
            got_better_score = new_grade_with_new_slot["totalScore"] >  old_grade_with_old_slot["totalScore"]

            # Regular case: normal problematic rasps
            if need_better_score and got_better_score:
                the_slot = new_slot
                break
            elif need_better_score:
                self.failure_reason(action, new_slot, rasp0, rasp_freqs, pure_new_slot_grade, pure_old_slot_grade)

            # Special case: problematic parallel groups and/or optionals at some slot
            if need_same_score and got_same_score:
                the_slot = new_slot
                break
            elif need_same_score:
                self.failure_reason_rigorous(action, new_slot, rasp0, rasp_freqs, pure_new_slot_grade)


        print("ITERS: ", cnt, rasp0.id, "SKIPPED: ", skipped)

        if not the_slot:
            data["unsuccessful_rasps"].add(rasp0.id)
            timetable[rasp0] = old_slot
            rasp_rrules[rasp0.id] = old_rrules
            self.tax_all_constraints(old_slot, rasp0, old_rrules["all_dates"], rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades)
            return data
        else:
            data["unsuccessful_rasps"] = set()

        self.tax_all_constraints(the_slot, rasp0, rasp_rrules[rasp0.id]["all_dates"], rooms_occupied, profs_occupied, nasts_occupied, optionals_occupied, groups_occupied, grades)

        #assert(grades["all"][k]<=0 and grades["all"][k] == new_grade_with_new_slot[k] for k in grades["all"])
        timetable[rasp0] = the_slot
        return data
