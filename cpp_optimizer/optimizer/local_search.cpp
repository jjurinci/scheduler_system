#include "local_search.h"
#include "why_fail.h"
#include "common_optimizer.h"
#include "../taxing/tax_tool.h"
#include "../taxing/rasp_problems.h"
#include "../rrule_logic/rasp_slots.h"
#include "../common/common.h"
#include <set>

std::vector<std::pair<double, int>> ls_tracker;
std::vector<std::pair<double, int>> grasp_tracker;
std::vector<std::pair<double, int>> rls_tracker;
std::vector<std::pair<double, int>> ils_tracker;

std::vector<std::pair<double, int>> get_grasp_tracker() {
    return grasp_tracker;
}

std::vector<std::pair<double, int>> get_rls_tracker() {
    return rls_tracker;
}

std::vector<std::pair<double, int>> get_ils_tracker() {
    return ils_tracker;
}

void clear_ls_tracker() {
    ls_tracker.clear();
}

void set_rls_tracker() {
    rls_tracker = ls_tracker;
    clear_ls_tracker();
}

void set_ils_tracker() {
    ils_tracker = ls_tracker;
    clear_ls_tracker();
}

void set_grasp_tracker() {
    grasp_tracker = ls_tracker;
    ls_tracker.clear();
}

Slot* steepest_better_slot(State& state, Rasp& rasp0, Grade& only_old_slot_grade) {
    Slot* best_slot_ptr = NULL;
    Grade best_grade = only_old_slot_grade;
    BannedSlots banned = BannedSlots{};
    std::vector<Slot> pool = get_rasp_slots(state, rasp0, true);

    for(auto new_slot : pool) {
        if(is_skippable(banned, new_slot)) {
            continue;
        }
        update_rasp_rrules(state, new_slot, rasp0);

        Grade only_new_slot_grade = count_all_collisions(state, new_slot, rasp0);
        bool got_better_score = only_new_slot_grade.totalScore > best_grade.totalScore;
        if(got_better_score) {
            best_slot_ptr = new Slot{new_slot};
            best_grade = only_new_slot_grade;
        }
        else {
            update_failure_reason(banned, new_slot, only_new_slot_grade, only_old_slot_grade);
        }
    }
    return best_slot_ptr;
}

Slot* first_better_slot(State& state, Rasp& rasp0, Grade& only_old_slot_grade) {
    BannedSlots banned = BannedSlots{};
    std::vector<Slot> pool = get_rasp_slots(state, rasp0, true);
    Slot* chosen_slot_ptr = NULL;
    for(auto new_slot : pool) {
        if(is_skippable(banned, new_slot)) {
            continue;
        }
        update_rasp_rrules(state, new_slot, rasp0);

        Grade only_new_slot_grade = count_all_collisions(state, new_slot, rasp0);
        bool got_better_score = only_new_slot_grade.totalScore > only_old_slot_grade.totalScore;
        if(got_better_score) {
            chosen_slot_ptr = new Slot{new_slot};
            break;
        }
        else {
            update_failure_reason(banned, new_slot, only_new_slot_grade, only_old_slot_grade);
        }
    }
    return chosen_slot_ptr;
}

bool find_better_neighbor(State& state, double& current_best_grade, double CPU_TIME_SEC, time_point start_time) {
    bool searched_entire_neighborhood = false, improvement = false;
    std::set<id_rasp> tabu_list;

    while(!searched_entire_neighborhood) {
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            break;
        }

        Rasp* rasp_ptr = random_problematic_rasp(state, tabu_list);
        if(!rasp_ptr) {
            improvement = false;
            break;
        }
        Rasp rasp0 = *rasp_ptr;
        Slot old_slot = state.timetable[rasp0];
        Grade only_old_slot_grade = untax_old_slot(state, rasp0, old_slot);
        Slot* new_slot_ptr = first_better_slot(state, rasp0, only_old_slot_grade);
        improvement = (new_slot_ptr) ? true : false;
        update_tabu_list(tabu_list, rasp0, new_slot_ptr);
        Slot new_slot = (improvement) ? *new_slot_ptr : old_slot;
        tax_new_slot(state, rasp0, new_slot);

        if(improvement) {
            if(state.grade.totalScore > current_best_grade) {
                current_best_grade = state.grade.totalScore;
                double duration_sec = elapsed_secs(start_time, time_now());
                ls_tracker.push_back(std::make_pair(duration_sec, current_best_grade));
                std::cout<<duration_sec<<" | "<<state.grade<<"\n";
            }
            break;
        }
    }
    return improvement;
}

void local_search(State& state, double current_best_grade, double CPU_TIME_SEC, time_point start_time) {
    if(ls_tracker.empty() && current_best_grade != 1) {
        ls_tracker.push_back(std::make_pair(0, current_best_grade));
    }
    std::cout<<elapsed_secs(start_time, time_now())<<" STARTING LOCAL SEARCH.\n";
    while(true) {
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) break;
        bool better_neighbor_exists = find_better_neighbor(state, current_best_grade, CPU_TIME_SEC, start_time);
        if(state.grade.totalScore == 0 || !better_neighbor_exists) {
            break;
        }
    }
}
