#include "tax_sems.h"
#include "../rrule_logic/cons_api.h"
#include <math.h>
#include <algorithm>
#include <set>

void update_grade_sems(State& state, int punish, bool plus) {
    if(plus) {
        state.grade.semScore   += punish;
        state.grade.totalScore += punish;
    }
    else {
        state.grade.semScore   -= punish;
        state.grade.totalScore -= punish;
    }
}

int sems_tax_punish(int old_cnt_occ, int old_cnt_colls, int new_cnt_occ, int new_cnt_colls) {
    int old_score = (old_cnt_colls <= 1) ? 0 : old_cnt_occ * -30;
    int new_score = (new_cnt_colls <= 1) ? 0 : new_cnt_occ * -30;
    return -std::abs(old_score - new_score);
}

void tax_rrule_in_sems_mandatory(State& state, id_sem sem_id, Rasp& rasp,
                                 std::set<triplet>& own_group_dates) {
    std::vector<triplet>& all_dates   = state.rasp_rrules[rasp.id].all_dates;
    array3D sem_occupied    = state.mutable_constraints.sems_occupied[sem_id];
    array3D sems_collisions = state.mutable_constraints.sems_collisions[sem_id];
    int punish = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        int old_cnt_occ   = int(sem_occupied[week][day][hour]);
        int old_cnt_colls = int(sems_collisions[week][day][hour]);

        if(own_group_dates.find(date) == own_group_dates.end()) {
            sems_collisions[week][day][hour] += 1;
        }

        int new_cnt_colls = int(sems_collisions[week][day][hour]);
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls);
        sem_occupied[week][day][hour] += 1;
    }
    if(punish) {
        update_grade_sems(state, punish, true);
    }
}

void tax_rrule_in_sems_optional(State& state, id_sem sem_id, Rasp& rasp,
                                std::set<triplet>& own_group_dates,
                                std::set<triplet>& other_group_dates) {
    std::vector<triplet>& all_dates     = state.rasp_rrules[rasp.id].all_dates;
    array3D sem_occupied                = state.mutable_constraints.sems_occupied[sem_id];
    array3D optionals_occupied          = state.mutable_constraints.optionals_occupied[sem_id];
    array3D sems_collisions             = state.mutable_constraints.sems_collisions[sem_id];

    int punish = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        int old_cnt_occ   = int(sem_occupied[week][day][hour]);
        int old_cnt_colls = int(sems_collisions[week][day][hour]);

        if(own_group_dates.find(date) == own_group_dates.end() &&
          (optionals_occupied[week][day][hour]==0 || other_group_dates.find(date) != other_group_dates.end())) {
            sems_collisions[week][day][hour] += 1;
        }

        int new_cnt_colls = int(sems_collisions[week][day][hour]);
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls);
        sem_occupied[week][day][hour] += 1;
        optionals_occupied[week][day][hour] += 1;
    }
    if(punish) {
        update_grade_sems(state, punish, true);
    }
}

void untax_rrule_in_sems_mandatory(State& state, id_sem sem_id, Rasp& rasp,
                                   std::set<triplet>& own_group_dates) {
    std::vector<triplet>& all_dates   = state.rasp_rrules[rasp.id].all_dates;
    array3D sem_occupied              = state.mutable_constraints.sems_occupied[sem_id];
    array3D sems_collisions           = state.mutable_constraints.sems_collisions[sem_id];

    int punish = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        int old_cnt_occ   = int(sem_occupied[week][day][hour]);
        int old_cnt_colls = int(sems_collisions[week][day][hour]);

        if(own_group_dates.find(date) == own_group_dates.end()) {
            sems_collisions[week][day][hour] -= 1;
        }

        int new_cnt_colls = int(sems_collisions[week][day][hour]);
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ-1, new_cnt_colls);
        sem_occupied[week][day][hour] -= 1;
    }
    if(punish) {
        update_grade_sems(state, punish, false);
    }
}

void untax_rrule_in_sems_optional(State& state, id_sem sem_id, Rasp& rasp,
                                  std::set<triplet>& own_group_dates,
                                  std::set<triplet>& other_group_dates) {
    std::vector<triplet>& all_dates     = state.rasp_rrules[rasp.id].all_dates;
    array3D sem_occupied                = state.mutable_constraints.sems_occupied[sem_id];
    array3D optionals_occupied          = state.mutable_constraints.optionals_occupied[sem_id];
    array3D sems_collisions             = state.mutable_constraints.sems_collisions[sem_id];

    int punish = 0;
    for(triplet date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        int old_cnt_occ   = int(sem_occupied[week][day][hour]);
        int old_cnt_colls = int(sems_collisions[week][day][hour]);

        if(own_group_dates.find(date) == own_group_dates.end() &&
          (optionals_occupied[week][day][hour] == 1 || other_group_dates.find(date) != other_group_dates.end())) {
            sems_collisions[week][day][hour] -= 1;
        }

        int new_cnt_colls = int(sems_collisions[week][day][hour]);
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ-1, new_cnt_colls);
        sem_occupied[week][day][hour] -= 1;
        optionals_occupied[week][day][hour] -= 1;
    }
    if(punish) {
        update_grade_sems(state, punish, false);
    }
}

void tax_rrule_in_sems(State& state, Rasp& rasp) {
    std::set<triplet> own_group_dates = get_own_groups_all_dates(state, rasp);
    std::set<triplet> other_group_dates = get_other_groups_all_dates(state, rasp);
    for(id_sem sem_id : rasp.mandatory_in_semester_ids) {
        tax_rrule_in_sems_mandatory(state, sem_id, rasp, own_group_dates);
    }
    for(id_sem sem_id : rasp.optional_in_semester_ids) {
        tax_rrule_in_sems_optional(state, sem_id, rasp, own_group_dates, other_group_dates);
    }
}

void untax_rrule_in_sems(State& state, Rasp& rasp) {
    std::set<triplet> own_group_dates   = get_own_groups_all_dates(state, rasp);
    std::set<triplet> other_group_dates = get_other_groups_all_dates(state, rasp);
    for(id_sem sem_id : rasp.mandatory_in_semester_ids) {
        untax_rrule_in_sems_mandatory(state, sem_id, rasp, own_group_dates);
    }
    for(id_sem sem_id : rasp.optional_in_semester_ids) {
        untax_rrule_in_sems_optional(state, sem_id, rasp, own_group_dates, other_group_dates);
    }
}
