#include <iostream>
#include "types/my_types.h"
#include "types/state.h"
#include "common/common.h"
#include "opt_algorithms.h"
#include "common/state_to_json.h"
#include "optimizer/variable_neighbor.h"
#include "optimizer/local_search.h"
#include "optimizer/simulated_annealing.h"
#include "common/save_tracker_to_json.h"

int main(int argc, char* argv[]){
    if(argc != 2 + 1) {
        throw std::invalid_argument("Need exactly 2 arguments but " + std::to_string(argc-1) + " were given.");
    }
    std::set<std::string> allowed_algorithms = {"vns", "sa", "rls", "ils", "grasp"};
    if(allowed_algorithms.find(argv[1]) == allowed_algorithms.end()) {
        throw std::invalid_argument(std::string("First argument needs to be one of: ") + "'vns','sa','rls','ils','grasp' but " +  argv[1] + " was given.");
    }
    if(!is_numeric(argv[2])) {
        throw std::invalid_argument(std::string("Second argument needs to a number, but ") + argv[2] + " was given.");
    }
    std::string algorithm = argv[1];
    double CPU_TIME_SEC   = std::stod(argv[2]);

    State state = load_state("cpp_optimizer/database/state.json", false);
    std::cout<<"Loaded state.\n";
    time_point start_time = time_now();
    State best_state = State{};
    if(algorithm == "vns") {
        best_state = variable_neighborhood_search(state, CPU_TIME_SEC);
    }
    else if(algorithm == "sa") {
        best_state = simulated_annealing(state, 100000, CPU_TIME_SEC);
    }
    else if(algorithm == "rls") {
        best_state = repeated_local_search(state, CPU_TIME_SEC);
    }
    else if(algorithm == "ils") {
        best_state = iterated_local_search(state, CPU_TIME_SEC);
    }
    else if(algorithm == "grasp") {
        best_state = grasp(state, 10, 5, CPU_TIME_SEC);
    }

    double secs = elapsed_secs(start_time, time_now());
    std::cout<<"Best: "<<best_state.grade<<"\n";
    std::cout<<"It took: "<<secs<<" seconds.\n";

    save_state_to_json(best_state, "cpp_optimizer/database/state.json");
    std::cout<<"Saved timetable.\n";
    return 0;
}
