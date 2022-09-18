#pragma once
#include "../types/my_types.h"
#include <set>
#include <map>

bool is_weak_computer_problematic(State& state, Rasp& rasp, id_room room_id);

bool is_strong_computer_problematic(State& state, Rasp& rasp, id_room room_id);

bool is_computer_problematic(State& state, Rasp& rasp, id_room room_id);

bool is_capacity_problematic(State& state, Rasp& rasp, id_room room_id);

bool is_room_problematic(State& state, id_room room_id, std::vector<triplet>& all_dates);

bool is_prof_problematic(State& state, Rasp& rasp, std::vector<triplet>& all_dates);

bool is_sem_problematic(State& state, Rasp& rasp, std::vector<triplet>& all_dates);

bool is_rasp_problematic(State& state, Rasp& rasp, id_room room_id);

int count_rrule_in_mandatory_rasp(State& state, Rasp& rasp, id_sem sem_id,
                                  std::set<triplet>& own_group_dates);

int count_rrule_in_optional_rasp(State& state, Rasp& rasp, id_sem sem_id,
                                 std::set<triplet>& own_group_dates,
                                 std::set<triplet>& other_group_dates);

int count_rrule_in_sems(State& state, Rasp& rasp);

int count_rrule_in_array3D(State& state, Rasp& rasp, array3D arr);

Grade count_all_collisions(State& state, Slot& slot, Rasp& rasp);

Rasp* random_problematic_rasp(State& state, std::set<id_rasp>& tabu_list);

std::pair<Rasp*, Rasp*> problematic_rasp_pair(State& state, std::set<id_rasp>& tabu_list1,
                                            std::map<id_rasp, std::set<id_rasp>>& tabu_list2);

std::vector<Rasp> most_problematic_rasps(State& state, float percent);
