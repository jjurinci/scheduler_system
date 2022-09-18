#include "tax_profs.h"
#include <iostream>
#include <vector>

void update_grade_profs(State& state, int punish, bool plus) {
    if(plus) {
        state.grade.professorScore += punish;
        state.grade.totalScore     += punish;
    }
    else {
        state.grade.professorScore -= punish;
        state.grade.totalScore     -= punish;
    }
}

void tax_rrule_in_profs(State& state, Rasp& rasp) {
    array3D prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id];
    std::vector<triplet>& all_dates = state.rasp_rrules[rasp.id].all_dates;

    int cnt = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        prof_occupied[week][day][hour] +=1;
        int collisions = prof_occupied[week][day][hour];
        cnt = (collisions > 1) ? (cnt + collisions) : cnt;
    }

    if(cnt) {
        int punish = -cnt * 30;
        update_grade_profs(state, punish, true);
    }
}

void untax_rrule_in_profs(State& state, Rasp& rasp) {
    array3D prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id];
    std::vector<triplet>& all_dates = state.rasp_rrules[rasp.id].all_dates;

    int cnt = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        int collisions = prof_occupied[week][day][hour];
        cnt = (collisions > 1) ? (cnt + collisions) : cnt;
        prof_occupied[week][day][hour] -=1;
    }

    if(cnt) {
        int punish = -cnt * 30;
        update_grade_profs(state, punish, false);
    }
}
