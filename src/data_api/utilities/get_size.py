import sys
def get_size(obj, seen=None):
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
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


def print_size(state):
    total = round(get_size(state) / 10**6,4)
    space = " " * (20 - len("TOTAL"))
    print("TOTAL" + space, ":", total, "\tMB. ", "100%")
    print("-"*20)
    size_list = []
    for index, key in enumerate(state._fields):
        size = round(get_size(state[index]) / 10**6, 4)
        percentage = round((size / total) * 100, 2)
        size_list.append((size, key, percentage))

    size_list.sort(key=lambda x: x[0], reverse=True)
    for size, key, percentage in size_list:
        space = " " * (20 - len(key))
        print_key = key + space
        print(print_key, ":", size, "\tMB. ", percentage, "%")
