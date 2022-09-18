#include "perturbation.h"
#include "../types/state.h"
#include "../optimizer/local_search.h"
#include "../taxing/tax_tool.h"
#include "../taxing/rasp_problems.h"
#include "../rrule_logic/cons_api.h"
#include "../rrule_logic/rasp_slots.h"
#include "../common/common.h"
#include <algorithm>

void set_random_slots(State& state, std::vector<Rasp>& rasps) {
    for(Rasp& rasp : rasps) {
        Slot rnd_slot = get_random_slot(state, rasp);
        tax_new_slot(state, rasp, rnd_slot);
        state.rasps_in_timetable.push_back(rasp);
    }
}

void set_semi_random_slots(State& state, float percent, time_point start_time) {
    std::vector<Rasp> problematic_rasps = most_problematic_rasps(state, percent);
    clear_mutable(state);
    set_random_slots(state, problematic_rasps);

    double SECONDS = elapsed_secs(start_time, time_now()) + 5;
    local_search(state, 1, SECONDS, start_time);

    std::vector<Rasp> other_rasps;
    for(Rasp& rasp : state.rasps) {
        if(std::find(problematic_rasps.begin(), problematic_rasps.end(), rasp) != problematic_rasps.end()) {
            continue;
        }
        other_rasps.push_back(rasp);
    }
    set_random_slots(state, other_rasps);
}

void random_timetable(State& state, time_point start_time) {
    std::cout<<elapsed_secs(start_time, time_now())<<" Generating random timetable.\n";
    clear_mutable(state);
    set_random_slots(state, state.rasps);
}

void semi_random_timetable(State& state, float percent, time_point start_time) {
    bool first_iteration = (state.timetable.empty()) ? true : false;
    if(first_iteration) {
        random_timetable(state, start_time);
    }
    else {
        std::cout<<elapsed_secs(start_time, time_now())<<" Generating semi random timetable.\n";
        set_semi_random_slots(state, percent, start_time);
    }
}
