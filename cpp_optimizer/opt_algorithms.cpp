#include "opt_algorithms.h"
#include "optimizer/perturbation.h"
#include "optimizer/simulated_annealing.h"
#include "optimizer/variable_neighbor.h"
#include "optimizer/local_search.h"
#include "optimizer/grasp.h"
#include "common/common.h"
#include "types/state.h"
#include "common/save_tracker_to_json.h"

State variable_neighborhood_search(State& state, double CPU_TIME_SEC) {
    std::cout<<"Starting variable neighborhood search.\n";
    time_point start_time = time_now();

    double best_grade = 1;
    State best_state = state;
    while(true){
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            std::cout<<"Time limit reached. Stopping.\n";
            break;
        }
        semi_random_timetable(state, 0.2, start_time);
        if(best_grade == 1) {
            best_grade = state.grade.totalScore;
        }
        run_vns(state, best_grade, CPU_TIME_SEC, start_time);

        if(state.grade.totalScore > best_grade) {
            best_grade = state.grade.totalScore;
            best_state = deep_copy(state);
        }
        if(best_grade == 0) {
            break;
        }
    }
    return best_state;
}

State grasp(State& state, int num_candidates, int num_restrict, double CPU_TIME_SEC) {
    std::cout<<"Starting grasp.\n";
    time_point start_time = time_now();

    double best_grade = 1;
    State best_state = state;
    while(true){
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            std::cout<<"Time limit reached. Stopping.\n";
            break;
        }
        construct_solution(state, num_candidates, num_restrict, CPU_TIME_SEC, start_time);
        if(best_grade == 1) {
            best_grade = state.grade.totalScore;
        }
        local_search(state, best_grade, CPU_TIME_SEC, start_time);

        if(state.grade.totalScore > best_grade) {
            best_grade = state.grade.totalScore;
            best_state = deep_copy(state);
        }
        if(best_grade == 0) {
            break;
        }
    }
    set_grasp_tracker();
    return best_state;
}

State repeated_local_search(State& state, double CPU_TIME_SEC) {
    std::cout<<"Starting repeated local search.\n";
    time_point start_time = time_now();

    double best_grade = 1;
    State best_state = state;
    while(true){
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            std::cout<<"Time limit reached. Stopping.\n";
            break;
        }
        random_timetable(state, start_time);
        if(best_grade == 1) {
            best_grade = state.grade.totalScore;
        }
        local_search(state, best_grade, CPU_TIME_SEC, start_time);

        if(state.grade.totalScore > best_grade) {
            best_grade = state.grade.totalScore;
            best_state = deep_copy(state);
        }
        if(best_grade == 0) {
            break;
        }
    }
    set_rls_tracker();
    return best_state;
}

State iterated_local_search(State& state, double CPU_TIME_SEC) {
    std::cout<<"Starting iterated local search.\n";
    time_point start_time = time_now();

    double best_grade = 1;
    State best_state = state;
    while(true){
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            std::cout<<"Time limit reached. Stopping.\n";
            break;
        }
        semi_random_timetable(state, 0.2, start_time);
        if(best_grade == 1) {
            best_grade = state.grade.totalScore;
        }
        local_search(state, best_grade, CPU_TIME_SEC, start_time);

        if(state.grade.totalScore > best_grade) {
            best_grade = state.grade.totalScore;
            best_state = deep_copy(state);
        }
        if(best_grade == 0) {
            break;
        }
    }
    set_ils_tracker();
    return best_state;
}

State simulated_annealing(State& state, int temperature, double CPU_TIME_SEC) {
    std::cout<<"Starting simulated annealing.\n";
    time_point start_time = time_now();

    double best_grade = 1;
    State best_state = state;
    while(true){
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            std::cout<<"Time limit reached. Stopping.\n";
            break;
        }
        random_timetable(state, start_time);
        if(best_grade == 1) {
            best_grade = state.grade.totalScore;
        }
        run_sa(state, temperature, best_grade, CPU_TIME_SEC, start_time);

        if(state.grade.totalScore > best_grade) {
            best_grade = state.grade.totalScore;
            best_state = deep_copy(state);
        }
        if(best_grade == 0) {
            break;
        }
    }
    return best_state;
}
