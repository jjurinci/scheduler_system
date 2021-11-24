from rasptools import Optimizer
import pandas as pd
import pickle
from construct_data import summer_rasps, nasts, FIXED, \
                           FREE_TERMS, professor_occupied, classroom_occupied, \
                           computer_rooms, room_capacity, students_estimate

data = {
        "rasps": summer_rasps,
        "nasts": nasts,
        "fixed": FIXED,
        "free_terms": FREE_TERMS,
        "professor_occupied": professor_occupied,
        "classroom_occupied": classroom_occupied,
        "computer_rooms": computer_rooms,
        "room_capacity": room_capacity,
        "students_estimate": students_estimate
}

OPT = Optimizer(data)
sample = OPT.initialize_random_sample(10)
start = pd.Series([s[0]["totalScore"] for s in sample]).describe()
sample = OPT.iterate(sample, 5000, population_cap = 10)
end = pd.Series([s[0]["totalScore"] for s in sample]).describe()
print(start, end, start-end)

with open("saved_timetable.pickle", "wb") as f:
    pickle.dump(sample, f)
