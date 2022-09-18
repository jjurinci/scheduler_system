#pragma once
#include "../types/my_types.h"

void update_grade_sems(State& state, int punish, bool plus=true);

int sems_tax_punish(int old_cnt_occ, int old_cnt_colls, int new_cnt_occ, int new_cnt_colls);

void tax_rrule_in_sems_mandatory(State& state, id_sem sem_id, Rasp& rasp,
                                 std::set<triplet>& own_group_dates);

void tax_rrule_in_sems_optional(State& state, id_sem sem_id, Rasp& rasp,
                                std::set<triplet>& own_group_dates,
                                std::set<triplet>& other_group_dates);

void untax_rrule_in_sems_mandatory(State& state, id_sem sem_id, Rasp& rasp,
                                   std::set<triplet>& own_group_dates);

void untax_rrule_in_sems_optional(State& state, id_sem sem_id, Rasp& rasp,
                                  std::set<triplet>& own_group_dates,
                                  std::set<triplet>& other_group_dates);

void tax_rrule_in_sems(State& state, Rasp& rasp);

void untax_rrule_in_sems(State& state, Rasp& rasp);
