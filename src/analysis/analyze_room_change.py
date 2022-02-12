import pickle
import random
import data_api.subjects as subj_api
import data_api.classrooms as room_api
from collections import defaultdict

def load_timetables():
    name = "saved_timetables/saved_timetable.pickle"
    with open(name, "rb") as f:
        timetables = pickle.load(f)
    return timetables


def analyze_room_change():
    data = load_timetables()[0]
    timetable = data["timetable"]
    rooms_occupied = data["rooms_occupied"]
    professors_occupied = data["professors_occupied"]
    nasts_occupied = data["nasts_occupied"]
    students_per_rasp = data["students_per_rasp"]
    room_ids = list(rooms_occupied.keys())
    rooms = room_api.get_rooms_by_ids(room_ids)

    rasp_bad_rooms, rasp_good_rooms = defaultdict(lambda: []), defaultdict(lambda: [])
    for rasp in timetable.keys():
        subject = subj_api.get_subject_by_id(rasp.subjectId)
        if subject == -1:
            print(f"For {rasp.subjectId} {rasp.type} {rasp.group} subject: '{rasp.subjectId}' doesn't exist.")
            return
        semester_ids = subject.semesterIds

        for room in rooms:
            room_id = room.id
            intersection = get_intersection(rasp, room_id, semester_ids, rooms_occupied, professors_occupied, nasts_occupied)

            bad_room = {"roomId" : room_id, "subId": rasp.subjectId, "capacity_problem": False, "computer_problem": False, "free_time_problem": False}

            problems = False
            if students_per_rasp[rasp] > room.capacity:
                problems = True
                bad_room["capacity_problem"] = (True, students_per_rasp[rasp], room.capacity)

            if rasp.needsComputers and not room.hasComputers:
                problems = True
                bad_room["computer_problem"] = True

            if not intersection:
                problems = True
                bad_room["free_time_problem"] = True

            if problems:
                rasp_bad_rooms[rasp.id].append(bad_room)
                continue

            rasp_good_rooms[rasp.id].append(intersection[0])

    print(len(rasp_good_rooms), len(rasp_bad_rooms))
    return rasp_good_rooms, rasp_bad_rooms


def get_intersection(rasp, room_id, semester_ids, rooms_occupied, professors_occupied, nasts_occupied):
    intersection = []
    other_area = []
    for day in range(5):
        for hour in range(16):
            room_free = all(rooms_occupied[room_id][day][hour:(hour + rasp.duration)] == 0.0)
            prof_free = all(professors_occupied[rasp.professorId][day][hour:(hour + rasp.duration)] == 0.0)

            if not room_free:
                other_area.append((room_id, day, hour))
                continue

            if not prof_free:
                other_area.append((room_id, day, hour))
                continue

            nast_free = True
            for sem_id in semester_ids:
                nast_free = all(nasts_occupied[sem_id][day][hour:(hour + rasp.duration)] == 0.0)
                if not nast_free:
                    break
            if not nast_free:
                other_area.append((room_id, day, hour))
                continue

            intersection.append((room_id, day, hour))

    return intersection

analyze_room_change()
