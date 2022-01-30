import pickle
import numpy as np
import data_api.time_structure as time_api
import data_api.classrooms     as room_api
from dateutil.rrule import rrulestr

NUM_WEEKS, NUM_DAYS, NUM_HOURS = 17, 5, 16

def load_timetable():
    name = "saved_timetables/zero_timetable.pickle"
    with open(name, "rb") as f:
        data = pickle.load(f)
    return data

def analyze_movement():
    data = load_timetable()
    timetable = data["timetable"]
    rooms_occupied = data["rooms_occupied"]
    professors_occupied = data["profs_occupied"]
    nasts_occupied = data["nasts_occupied"]
    rasp_rrules = data["rasp_rrules"]

    for rasp, slot in timetable.items():
        all_dates = rasp_rrules[rasp.id]["all_dates"]
        intersection = get_intersection(rasp, slot, all_dates, rooms_occupied, professors_occupied, nasts_occupied)
        print(rasp.id, rasp.professor_id, intersection, "\n")


def get_intersection(rasp, slot, all_dates, rooms_occupied, profs_occupied, nasts_occupied):
    dt_week = all_dates[0][0]
    until = rrulestr(rasp.rrule)._until
    un_week, un_day, _ = time_api.date_to_index(until)
    room_occupied = rooms_occupied[slot.room_id]
    prof_occupied = profs_occupied[rasp.professor_id]
    intersection = []
    why_failure = {}
    for day in range(NUM_DAYS):
        if rasp.fixed_hour:
            pass
        for hour in range(NUM_HOURS):
            NEW_DTSTART = time_api.index_to_date(dt_week, day, hour)
            NEW_UNTIL   = time_api.index_to_date(un_week, un_day, hour)
            new_all_dates = time_api.get_rrule_dates(rasp.rrule, NEW_DTSTART, NEW_UNTIL)

            sem_ids = rasp.mandatory_in_semester_ids + rasp.optional_in_semester_ids
            collision = False
            for new_week, new_day, new_hour in new_all_dates:
                room_problem = np.any(room_occupied[new_week, new_day, new_hour:(new_hour + rasp.duration)] > 0)
                prof_problem = np.any(prof_occupied[new_week, new_day, new_hour:(new_hour + rasp.duration)] > 0)

                nast_problem = False
                problematic_semesters = set()
                for sem_id in sem_ids:
                    if np.any(nasts_occupied[sem_id][new_week, new_day, new_hour:(new_hour + rasp.duration)] > 0):
                        problematic_semesters.add(sem_id)
                        nast_problem = True

                if room_problem or prof_problem or nast_problem:
                    if (dt_week, new_day, new_hour) not in why_failure:
                        why_failure[(dt_week, new_day, new_hour)] = {"rooms": [], "profs": [], "nasts": []}
                    collision = True

                if room_problem:
                    why_failure[(dt_week, new_day, new_hour)]["rooms"].append(f"Room {slot.room_id} taken at {new_week} {new_day} {new_hour}.")

                if prof_problem:
                    why_failure[(dt_week, new_day, new_hour)]["profs"].append(f"Professor {rasp.professor_id} taken at {new_week} {new_day} {new_hour}.")

                if nast_problem:
                    for sem_id in problematic_semesters:
                        why_failure[(dt_week, new_day, new_hour)]["nasts"].append(f"Nast {sem_id} taken at {new_week} {new_day} {new_hour}.")

            if not collision:
                intersection.append((dt_week, day, hour))

    return intersection


def change_room():
    data = load_timetable()
    timetable = data["timetable"]

    # TODO: Simply check which rooms have good capacity and computers
    #       No need to check if room has available time.

analyze_movement()
