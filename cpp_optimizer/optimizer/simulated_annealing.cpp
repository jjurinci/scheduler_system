#include "simulated_annealing.h"
#include "why_fail.h"
#include "common_optimizer.h"
#include "../rrule_logic/rasp_slots.h"
#include "../taxing/tax_tool.h"
#include "../taxing/rasp_problems.h"
#include "../common/common.h"
#include <algorithm>
#include <random>
#include <cmath>
#include <set>
#include <vector>

std::vector<std::pair<double, int>> sa_tracker;

std::vector<std::pair<double, int>> get_sa_tracker() {
    return sa_tracker;
}

void clear_sa_tracker() {
    sa_tracker.clear();
}

double P(int old_score, int new_score, double temp) {
    old_score = std::abs(old_score);
    new_score = std::abs(new_score);
    return (new_score < old_score) ? 1.0 : exp(double(old_score - new_score) / temp);
}

Slot* annealing_descent(State& state, Rasp& rasp, Grade only_old_slot_grade, double temp) {
    BannedSlots banned;
    std::vector<Slot> pool = get_rasp_slots(state, rasp, true);
    Slot* chosen_slot_ptr = NULL;
    for(Slot new_slot : pool) {
        if(is_skippable(banned, new_slot)) {
            continue;
        }
        update_rasp_rrules(state, new_slot, rasp);
        Grade only_new_slot_grade = count_all_collisions(state, new_slot, rasp);
        int old_score = only_old_slot_grade.totalScore;
        int new_score = only_new_slot_grade.totalScore;

        double rnd_01 = random_between_0_1();
        if(P(old_score, new_score, temp) >= rnd_01) {
            chosen_slot_ptr = new Slot{new_slot};
            break;
        }
        else {
            update_failure_reason(banned, new_slot, only_new_slot_grade, only_old_slot_grade);
        }
    }
    return chosen_slot_ptr;
}

bool next_neighbor(State& state, double& temp, double& current_best_grade, double CPU_TIME_SEC, time_point start_time) {
    bool searched_entire_neighborhood = false, local_optima = false;
    std::set<id_rasp> tabu_list;

    int old_total = state.grade.totalScore;
    while(!searched_entire_neighborhood) {
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            break;
        }

        Rasp* rasp_ptr = random_problematic_rasp(state, tabu_list);
        if(!rasp_ptr) {
            local_optima = true;
            break;
        }
        Rasp rasp0 = *rasp_ptr;
        Slot old_slot = state.timetable[rasp0];
        Grade only_old_slot_grade = untax_old_slot(state, rasp0, old_slot);
        Slot* new_slot_ptr = annealing_descent(state, rasp0, only_old_slot_grade, temp);
        update_tabu_list(tabu_list, rasp0, new_slot_ptr);
        Slot new_slot = (new_slot_ptr) ? *new_slot_ptr : old_slot;
        tax_new_slot(state, rasp0, new_slot);
        int new_total = state.grade.totalScore;
        bool improvement = (new_total > old_total) ? true : false;

        if(improvement) {
            if(state.grade.totalScore > current_best_grade) {
                current_best_grade = state.grade.totalScore;
                double duration_sec = elapsed_secs(start_time, time_now());
                sa_tracker.push_back(std::make_pair(duration_sec, current_best_grade));
                std::cout<<duration_sec<<" | "<<temp<<" | "<<state.grade<<"\n";
            }
            break;
        }
        temp *= 0.99;
        if(temp<0.001) temp=0;
    }
    return local_optima;
}

void run_sa(State& state, int temperature, double current_best_grade, double CPU_TIME_SEC, time_point start_time) {
    if(sa_tracker.empty()) {
        sa_tracker.push_back(std::make_pair(0, current_best_grade));
    }
    std::cout<<elapsed_secs(start_time, time_now())<<" STARTED SIMULATED ANNEALING.\n";
    double temp = (double)temperature;
    while(true) {
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            break;
        }
        bool local_optima = next_neighbor(state, temp, current_best_grade, CPU_TIME_SEC, start_time);
        if(state.grade.totalScore == 0 || local_optima) {
            break;
        }
    }
}
