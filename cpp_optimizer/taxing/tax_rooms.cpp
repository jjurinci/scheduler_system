#include "tax_rooms.h"
#include <iostream>
#include <vector>

void update_grade_rooms(State& state, int punish, bool plus) {
    if(plus) {
        state.grade.roomScore  += punish;
        state.grade.totalScore += punish;
    }
    else {
        state.grade.roomScore  -= punish;
        state.grade.totalScore -= punish;
    }
}

void tax_rrule_in_rooms(State& state, id_room room_id, Rasp& rasp) {
    array3D room_occupied = state.mutable_constraints.rooms_occupied[room_id];
    std::vector<triplet>& all_dates = state.rasp_rrules[rasp.id].all_dates;

    int cnt = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        room_occupied[week][day][hour] +=1;
        int collisions = room_occupied[week][day][hour];
        cnt = (collisions > 1) ? (cnt + collisions) : cnt;
    }

    if(cnt) {
        int punish = -cnt * 30;
        update_grade_rooms(state, punish, true);
    }
}

void untax_rrule_in_rooms(State& state, id_room room_id, Rasp& rasp) {
    array3D room_occupied = state.mutable_constraints.rooms_occupied[room_id];
    std::vector<triplet>& all_dates = state.rasp_rrules[rasp.id].all_dates;

    int cnt = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        int collisions = room_occupied[week][day][hour];
        cnt = (collisions > 1) ? (cnt + collisions) : cnt;
        room_occupied[week][day][hour] -=1;
    }

    if(cnt) {
        int punish = -cnt * 30;
        update_grade_rooms(state, punish, false);
    }
}
