#include "rasp_slots.h"
#include "../common/common.h"
#include <vector>
#include <random>
#include <algorithm>
#include <set>

Slot get_random_slot(State& state, Rasp& rasp) {
    std::vector<pair> dtstart_weekdays = state.rasp_rrules[rasp.id].dtstart_weekdays;
    pair dtstart_weekday = *select_randomly(dtstart_weekdays.begin(), dtstart_weekdays.end());
    int week = dtstart_weekday.first;
    int day = dtstart_weekday.second;
    int hour = -1;
    if(!rasp.fixed_hour.empty()) {
        hour = std::stoi(rasp.fixed_hour);
    }
    else {
        int NUM_HOURS = state.time_structure.NUM_HOURS;
        std::set<int> hours = pickSet(NUM_HOURS - rasp.duration + 1, 1);
        hour = *select_randomly(hours.begin(), hours.end());
    }
    id_room room_id = "";
    if(!rasp.fix_at_room_id.empty()) {
        room_id = rasp.fix_at_room_id;
    }
    else {
        room_id = select_randomly(state.rooms.begin(), state.rooms.end())->first;
    }
    return Slot{room_id, week, day, hour};
}

void update_possible_slots(State& state, std::vector<Slot>& pool, Rasp& rasp, int week, int day, std::string fixed_hour) {
    int NUM_HOURS = state.time_structure.NUM_HOURS;
    std::set<id_room> room_pool;
    if(!rasp.fix_at_room_id.empty()){
        room_pool.insert(rasp.fix_at_room_id);
    }
    else {
        for(auto& it : state.mutable_constraints.rooms_occupied) {
            room_pool.insert(it.first);
        }
    }

    if(fixed_hour.empty()) {
        for(id_room room_id : room_pool) {
            for(int hour=0; hour<NUM_HOURS; ++hour){
                if(hour+rasp.duration >= NUM_HOURS){
                    break;
                }
                pool.push_back(Slot{room_id, week, day, hour});
            }
        }
    }
    else {
        int hour = std::stoi(fixed_hour);
        for(id_room room_id : room_pool) {
            pool.push_back(Slot{room_id, week, day, hour});
        }
    }
}

std::vector<Slot> get_rasp_slots(State& state, Rasp& rasp, bool shuffle_slots) {
    std::vector<Slot> pool;
    std::vector<pair> dtstart_weekdays = state.rasp_rrules[rasp.id].dtstart_weekdays;
    for(pair weekday : dtstart_weekdays) {
        int week = weekday.first;
        int day  = weekday.second;
        update_possible_slots(state, pool, rasp, week, day, rasp.fixed_hour);
    }
    if(shuffle_slots) {
        shuffle_vector(pool);
    }
    return pool;
}

void update_rasp_rrules(State& state, Slot& slot, Rasp& rasp) {
    int index = state.rasp_rrules[rasp.id].rrule_table_index;
    pair key = std::make_pair(slot.week, slot.day);
    std::vector<pair> rrule_table_element = state.rrule_table[index][key];

    std::vector<triplet> all_dates;
    for(pair weekday : rrule_table_element) {
        int week = weekday.first;
        int day  = weekday.second;
        for(int hour=slot.hour; hour<slot.hour+rasp.duration; ++hour) {
            triplet date = std::make_tuple(week, day, hour);
            all_dates.push_back(date);
        }
    }
    state.rasp_rrules[rasp.id].DTSTART   = all_dates[0];
    state.rasp_rrules[rasp.id].UNTIL     = all_dates[all_dates.size()-1];
    state.rasp_rrules[rasp.id].all_dates = all_dates;
}

void clear_rasp_rrules(State& state, Rasp& rasp) {
    state.rasp_rrules[rasp.id].DTSTART = std::make_tuple(-1, -1, -1);
    state.rasp_rrules[rasp.id].UNTIL   = std::make_tuple(-1, -1, -1);
    state.rasp_rrules[rasp.id].all_dates.clear();
}

bool can_swap_rasp_slots(State& state, Rasp& rasp0, Rasp& rasp1, Slot& slot0, Slot& slot1) {
    int NUM_HOURS = state.time_structure.NUM_HOURS;
    int index0 = state.rasp_rrules[rasp0.id].rrule_table_index;
    int index1 = state.rasp_rrules[rasp1.id].rrule_table_index;
    pair key0  = std::make_pair(slot0.week, slot0.day);
    pair key1  = std::make_pair(slot1.week, slot1.day);

    bool condition1 = state.rrule_table[index0].find(key1) == state.rrule_table[index0].end();
    bool condition2 = state.rrule_table[index1].find(key0) == state.rrule_table[index1].end();
    bool condition3 = rasp0.duration + slot1.hour >= NUM_HOURS;
    bool condition4 = rasp1.duration + slot0.hour >= NUM_HOURS;
    bool condition5 = rasp0.fixed_hour != rasp1.fixed_hour;
    bool condition6 = rasp0.fix_at_room_id != rasp1.fix_at_room_id;
    return !(condition1 || condition2 || condition3 || condition4 || condition5 || condition6);
}
