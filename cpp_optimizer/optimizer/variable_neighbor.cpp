#include "variable_neighbor.h"
#include "local_search.h"
#include "common_optimizer.h"
#include "../rrule_logic/rasp_slots.h"
#include "../taxing/tax_tool.h"
#include "../taxing/rasp_problems.h"
#include "../common/common.h"
#include "../types/state.h"
#include <random>
#include <map>
#include <set>

std::vector<std::pair<double, int>> vns_tracker;

std::vector<std::pair<double, int>> get_vns_tracker() {
    return vns_tracker;
}

void clear_vns_tracker() {
    vns_tracker.clear();
}

bool swap_pairs(State& state, Rasp rasp0, Rasp rasp1) {
    Grade old_total_grade = state.grade;

    Slot rasp0_old_slot = state.timetable[rasp0];
    Slot rasp1_old_slot = state.timetable[rasp1];

    untax_old_slot(state, rasp0, rasp0_old_slot);
    tax_new_slot(state, rasp0, rasp1_old_slot);
    untax_old_slot(state, rasp1, rasp1_old_slot);

    if(state.grade.totalScore <= old_total_grade.totalScore) {
        tax_new_slot(state, rasp1, rasp1_old_slot);
        untax_old_slot(state, rasp0, rasp1_old_slot);
        tax_new_slot(state, rasp0, rasp0_old_slot);
        return false;
    }

    Grade untaxed_rasp1_grade = state.grade;
    Grade difference_grade = old_total_grade - untaxed_rasp1_grade;
    Slot* chosen_slot_ptr = first_better_slot(state, rasp1, difference_grade);

    if(chosen_slot_ptr) {
        tax_new_slot(state, rasp1, *chosen_slot_ptr);
    }
    else {
        tax_new_slot(state, rasp1, rasp1_old_slot);
        untax_old_slot(state, rasp0, rasp1_old_slot);
        tax_new_slot(state, rasp0, rasp0_old_slot);
    }
    return (chosen_slot_ptr) ? true : false;
}

bool vnd_neighborhood_2(State& state) {
    bool searched_entire_neighborhood = false, improvement = false;
    std::set<id_rasp> tabu_list1;
    std::map<id_rasp, std::set<id_rasp>> tabu_list2;

    while(!searched_entire_neighborhood) {
        std::pair<Rasp*, Rasp*> two_rasps = problematic_rasp_pair(state, tabu_list1, tabu_list2);
        Rasp *rasp0_ptr = two_rasps.first, *rasp1_ptr = two_rasps.second;

        if(!rasp0_ptr && !rasp1_ptr){
            improvement = false;
            break;
        }
        else if(rasp0_ptr && !rasp1_ptr) {
            tabu_list1.insert(rasp0_ptr->id);
            continue;
        }

        Rasp rasp0 = *rasp0_ptr, rasp1 = *rasp1_ptr;
        bool got_better_score = swap_pairs(state, rasp0, rasp1);
        if(!got_better_score) {
            tabu_list2[rasp0.id].insert(rasp1.id);
        }
        else {
            improvement = true;
            break;
        }
    }
    return improvement;
}

bool vnd_neighborhood_1(State& state) {
    bool searched_entire_neighborhood = false, improvement = false;
    std::set<id_rasp> tabu_list1;

    while(!searched_entire_neighborhood) {
        Rasp* rasp_ptr = random_problematic_rasp(state, tabu_list1);
        if(!rasp_ptr) {
            improvement = false;
            break;
        }
        Rasp rasp0 = *rasp_ptr;
        Slot old_slot = state.timetable[rasp0];
        Grade only_old_slot_grade = untax_old_slot(state, rasp0, old_slot);
        Slot* new_slot_ptr = first_better_slot(state, rasp0, only_old_slot_grade);
        improvement = (new_slot_ptr) ? true : false;
        update_tabu_list(tabu_list1, rasp0, new_slot_ptr);

        Slot new_slot = (improvement) ? (*new_slot_ptr) : old_slot;
        tax_new_slot(state, rasp0, new_slot);
        if(improvement) {
            break;
        }
    }
    return improvement;
}

void variable_neighborhood_descent(State& state, double& current_best_grade, double CPU_TIME_SEC, time_point start_time) {
    int neighbor_l = 1, l_max = 2;
    bool improvement = true;
    std::cout<<elapsed_secs(start_time, time_now())<<" [IN VNS]: Running variable neighborhood descent.\n";

    while(neighbor_l <= l_max) {
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            break;
        }

        if(neighbor_l == 1) {
            improvement = vnd_neighborhood_1(state);
        }
        else if(neighbor_l == 2) {
            improvement = vnd_neighborhood_2(state);
        }
        if(improvement && state.grade.totalScore > current_best_grade) {
            current_best_grade = state.grade.totalScore;
            double duration_sec = elapsed_secs(start_time, time_now());
            vns_tracker.push_back(std::make_pair(duration_sec, current_best_grade));
            std::cout<<duration_sec<<" | "<<neighbor_l<<" | "<<state.grade<<"\n";
        }
        neighbor_l = (improvement) ? 1 : neighbor_l + 1;
    }
}

void shake(State& state, int neighbor_k, double& current_best_grade, time_point start_time) {
    std::cout<<elapsed_secs(start_time, time_now())<<" [IN VNS]: Shaking "<<neighbor_k<<"\n";
    if(neighbor_k == 1) {
        int percent20 = ceil((float)state.timetable.size() * 0.2);
        while(percent20--){
            Rasp rasp0 = select_randomly(state.timetable.begin(), state.timetable.end())->first;
            untax_old_slot(state, rasp0, state.timetable[rasp0]);
            Slot rnd_slot = get_random_slot(state, rasp0);
            tax_new_slot(state, rasp0, rnd_slot);
        }
    }
    else if(neighbor_k == 2) {
        std::set<id_rasp> tabu_list1;
        std::map<id_rasp, std::set<id_rasp>> tabu_list2;

        int percent20 = ceil((float)state.timetable.size() * 0.2);
        while(percent20--) {
            std::pair<Rasp*, Rasp*> two_rasps = problematic_rasp_pair(state, tabu_list1, tabu_list2);
            Rasp *rasp0_ptr = two_rasps.first, *rasp1_ptr = two_rasps.second;

            if(!rasp0_ptr || !rasp1_ptr) {
                break;
            }
            Rasp rasp0 = *rasp0_ptr, rasp1 = *rasp1_ptr;
            Slot old_rasp0_slot = state.timetable[rasp0];
            Slot old_rasp1_slot = state.timetable[rasp1];
            Slot new_rasp0_slot = old_rasp1_slot;
            Slot new_rasp1_slot = old_rasp0_slot;

            untax_old_slot(state, rasp0, old_rasp0_slot);
            tax_new_slot(state, rasp0, new_rasp0_slot);
            untax_old_slot(state, rasp1, old_rasp1_slot);
            tax_new_slot(state, rasp1, new_rasp1_slot);
        }
    }

    if(state.grade.totalScore > current_best_grade) {
        current_best_grade = state.grade.totalScore;
        double duration_sec = elapsed_secs(start_time, time_now());
        vns_tracker.push_back(std::make_pair(duration_sec, current_best_grade));
        std::cout<<duration_sec<<" | "<<state.grade<<"\n";
    }
}

void run_vns(State& state, double current_best_grade, double CPU_TIME_SEC, time_point start_time) {
    if(vns_tracker.empty()) {
        vns_tracker.push_back(std::make_pair(0, current_best_grade));
    }
    int neighbor_k = 1, k_max = 2;
    Grade best_grade = state.grade;
    State best_state = deep_copy(state);
    std::cout<<elapsed_secs(start_time, time_now())<<" STARTING VARIABLE NEIGHBORHOOD SEARCH.\n";

    while(neighbor_k <= k_max) {
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            break;
        }

        shake(state, neighbor_k, current_best_grade, start_time);
        variable_neighborhood_descent(state, current_best_grade, CPU_TIME_SEC, start_time);

        bool improvement = state.grade.totalScore > best_grade.totalScore;
        if(improvement) {
            neighbor_k = 1;
            best_grade = state.grade;
            best_state = deep_copy(state);
        }
        else {
            neighbor_k += 1;
        }
        bool perfect_grade = state.grade.totalScore == 0;
        if(perfect_grade) {
            break;
        }
    }
    state = best_state;
}
