import pickle
import data_api.subjects as subj_api

def load_timetables():
    name = "saved_timetables/saved_timetable.pickle"
    with open(name, "rb") as f:
        timetables = pickle.load(f)
    return timetables

def analyze_movement():
    data = load_timetables()[0]
    timetable = data["timetable"]
    rooms_occupied = data["rooms_occupied"]
    professors_occupied = data["professors_occupied"]
    nasts_occupied = data["nasts_occupied"]

    for rasp in timetable.keys():
        room_id, _, _ = timetable[rasp]

        # Load rasp (semesterIds) for nasts_occupied
        subject = subj_api.get_subject_by_id(rasp.subjectId)
        if subject == -1:
            print(f"For {rasp.subjectId} {rasp.type} {rasp.group} subject: '{rasp.subjectId}' doesn't exist.")
            return
        semester_ids = subject.semesterIds
        intersection = get_intersection(rasp, room_id, semester_ids, rooms_occupied, professors_occupied, nasts_occupied)
        print(intersection, "\n")


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

analyze_movement()
