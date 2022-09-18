#include "grasp.h"
#include "local_search.h"
#include "../types/state.h"
#include "../rrule_logic/cons_api.h"
#include "../rrule_logic/rasp_slots.h"
#include "../taxing/tax_tool.h"
#include "../taxing/rasp_problems.h"
#include "../common/common.h"
#include <algorithm>
#include <random>
#include <set>

typedef std::vector<std::pair<Slot, int>> Rcl;

void select_random_element(State& state, Rcl& rcl, Rasp& rasp0) {
    Slot slot = select_randomly(rcl.begin(), rcl.end())->first;
    tax_new_slot(state, rasp0, slot);
}

void apply_greedy(State& state, Rcl& candidate_list, int& num_candidates, Rasp& rasp0,
                  double CPU_TIME_SEC, time_point start_time) {

    std::vector<Slot> pool = get_rasp_slots(state, rasp0, true);
    num_candidates = (num_candidates > int(pool.size())) ? int(pool.size()) : num_candidates;
    num_candidates = (num_candidates < 1) ? 1 : num_candidates;
    pool.resize(num_candidates);

    for(Slot new_slot : pool) {
        update_rasp_rrules(state, new_slot, rasp0);
        Grade only_new_slot_grade = count_all_collisions(state, new_slot, rasp0);
        candidate_list.emplace_back(new_slot, only_new_slot_grade.totalScore);

        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            break;
        }
    }
}

Rcl make_rcl(State& state, int& num_candidates, int& num_restrict, Rasp& rasp0,
             double CPU_TIME_SEC, time_point start_time) {
    Rcl rcl;
    apply_greedy(state, rcl, num_candidates, rasp0, CPU_TIME_SEC, start_time);
    std::sort(rcl.begin(), rcl.end(), [](const std::pair<Slot, int>& a, const std::pair<Slot, int>& b) {
            return a.second > b.second;
    });
    num_restrict = (num_restrict > int(rcl.size())) ? int(rcl.size()) : num_restrict;
    num_restrict = (num_restrict < 1) ? 1 : num_restrict;
    rcl.resize(num_restrict);
    return rcl;
}

void construct_solution(State& state, int num_candidates, int num_restrict, double CPU_TIME_SEC, time_point start_time) {
    clear_mutable(state);
    std::cout<<elapsed_secs(start_time, time_now())<<" Constructing solution.\n";

    std::vector<int> indices = shuffled_indices(int(state.rasps.size()));
    for(int idx : indices) {
        if(TIME_LIMIT_REACHED(CPU_TIME_SEC, start_time)) {
            num_candidates = num_restrict = 1;
        }
        Rasp rasp0 = state.rasps[idx];
        Rcl rcl = make_rcl(state, num_candidates, num_restrict, rasp0, CPU_TIME_SEC, start_time);
        select_random_element(state, rcl, rasp0);
        state.rasps_in_timetable.push_back(rasp0);
    }
}
