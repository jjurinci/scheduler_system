import utilities.input_csv_to_json as input_csv_to_json
import utilities.print_timetable   as print_timetable
from utilities.general_utilities import save_timetable_to_file
from utilities.converter import pickle_to_json, json_to_pickle
import algorithms as a
import data_api.state as state_api
import subprocess

print("Loading .csv input from 'database/input/' and 'database/constraints/'")
input_csv_to_json.run()

# Choosing programming language
print("\n> Which programming language to use for optimizer?")
print("1 = C++\n2 = Python")
lang = ""
valid_inputs = ["1", "2"]
while lang not in valid_inputs:
    lang = input("Your input: ")
    if lang not in valid_inputs:
        print(lang, "is not a valid input.")
lang = "c++" if lang == "1" else "py"

# Choosing optimization algorithm
print("\n> Which optimization algorithm to use?")
print("1 = Variable Neighborhood Search\n2 = Simulated Annealing")
print("3 = Repeated Local Search\n4 = Iterated Local Search")
print("5 = Greedy Randomized Adaptive Search Procedure")
algo = ""
valid_inputs = ["1", "2", "3", "4", "5"]
while algo not in valid_inputs:
    algo = input("Your input: ")
    if algo not in valid_inputs:
        print(algo, "is not a valid input.")
valid_input_names = {"1": "vns", "2": "sa", "3": "rls", "4": "ils", "5": "grasp"}
algo = valid_input_names[algo]

# Choosing number of seconds for the optimization algorithm
print("\n> Choose the number of seconds to run the algorithm.")
CPU_SECONDS = ""
is_float = lambda s: s.replace('.','',1).isdigit()
while not is_float(CPU_SECONDS):
    CPU_SECONDS = input("Your input: ")
    if not is_float(CPU_SECONDS):
        print(CPU_SECONDS, "is not a valid input.")
CPU_SECONDS = float(CPU_SECONDS)

# Running the algorithms and saving results
if lang == "py":
    state = None
    if algo == "vns":
        state = a.vns_iterate(CPU_SECONDS)
    elif algo == "sa":
        state = a.simulated_annealing_iterate(CPU_SECONDS, 10**4)
    elif algo == "rls":
        state = a.repeated_local_search(CPU_SECONDS)
    elif algo == "ils":
        state = a.iterated_local_search(CPU_SECONDS)
    elif algo == "grasp":
        state = a.grasp_iterate(CPU_SECONDS, 10, 5)

    save_timetable_to_file(state, "saved_timetables/state.pickle")
    print_timetable.run()
    print("\n> Results saved to timetable.txt.")

elif lang == "c++":
    # Convert .csv input to .pickle State
    state = state_api.get_state()
    save_timetable_to_file(state, "saved_timetables/state.pickle")

    # Convert .pickle State to .json State
    pickle_to_json("saved_timetables/state.pickle", "cpp_optimizer/database/state.json")

    # Compile the C++ optimizer
    print("\n> Compiling C++ optimizer. Please wait...")
    make_process = subprocess.Popen(["make"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd="./cpp_optimizer")
    if make_process.wait() != 0:
        print("Failed to compile.")
    else:
        print("Compiled successfully.")
        print("> Running the optimizer.")
        try:
            # Run the C++ optimizer
            run_process = subprocess.run(["cpp_optimizer/build/a.out", algo, str(CPU_SECONDS)], check=True)
            print("Optimizer finished running successfully.")

            # Convert C++ optimizer .json to .pickle State
            json_to_pickle("cpp_optimizer/database/state.json", "saved_timetables/state.pickle")
            print("\nSaving results...")
            print_timetable.run()
            print("> Results saved to timetable.txt")
        except subprocess.CalledProcessError:
            print("Failed to run the optimizer.")
