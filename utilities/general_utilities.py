import sys
import pickle
import json

"""
Returns complete state from a .pickle file. (local search)
"""
def load_state():
    settings = load_settings()
    path = settings["path_state"]
    with open(path, "rb") as f:
        state = pickle.load(f)
    return state


"""
Returns settings of the algorithm (paths, etc)
"""
def load_settings():
    name = "settings.json"
    with open(name, "r", encoding="utf-8") as f:
        settings = json.load(f)
    return settings


"""
Saves state to a .pickle file.
"""
def save_timetable_to_file(state, path):
    print(f"Saving sample to {path}")
    with open(path, "wb") as p:
        #print(get_size_recordclass(state))
        pickle.dump(state, p)


"""
Returns the size of an object (recursive) in bytes.
"""
def get_size(obj, seen=None):
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
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


"""
Returns size of recordclass object in MB.
"""
def get_size_recordclass(state):
    total_size = sum(get_size(state[index]) for index, _ in enumerate(state.__fields__))
    return round(total_size / 10**6, 4)


"""
Prints state size in MB.
"""
def print_size(state):
    total = get_size_recordclass(state)
    space = " " * (20 - len("TOTAL"))
    print("TOTAL" + space, ":", total, "\tMB. ", "100%")
    print("-"*20)
    size_list = []
    for index, key in enumerate(state.__fields__):
        size = round(get_size(state[index]) / 10**6, 4)
        percentage = round((size / total) * 100, 2)
        size_list.append((size, key, percentage))

    size_list.sort(key=lambda x: x[0], reverse=True)
    for size, key, percentage in size_list:
        space = " " * (20 - len(key))
        print_key = key + space
        print(print_key, ":", size, "\tMB. ", percentage, "%")
