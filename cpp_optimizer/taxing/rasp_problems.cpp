#include "rasp_problems.h"
#include "../taxing/tax_tool.h"
#include "../rrule_logic/cons_api.h"
#include "../taxing/tax_sems.h"
#include "../rrule_logic/rasp_slots.h"
#include "../common/common.h"
#include <algorithm>
#include <cmath>

bool is_weak_computer_problematic(State& state, Rasp& rasp, id_room room_id) {
    return state.rooms[room_id].has_computers && !rasp.needs_computers;
}

bool is_strong_computer_problematic(State& state, Rasp& rasp, id_room room_id) {
    return !state.rooms[room_id].has_computers && rasp.needs_computers;
}

bool is_computer_problematic(State& state, Rasp& rasp, id_room room_id) {
    return is_strong_computer_problematic(state, rasp, room_id);
           //|| is_weak_computer_problematic(state, rasp, room_id);
}

bool is_capacity_problematic(State& state, Rasp& rasp, id_room room_id) {
    return state.students_per_rasp[rasp.id] > state.rooms[room_id].capacity;
}

bool is_room_problematic(State& state, id_room room_id, std::vector<triplet>& all_dates) {
    array3D room_occupied = state.mutable_constraints.rooms_occupied[room_id];
    for(triplet& date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        if(room_occupied[week][day][hour]>1) return true;
    }
    return false;
}

bool is_prof_problematic(State& state, Rasp& rasp, std::vector<triplet>& all_dates) {
    array3D prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id];
    for(triplet& date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        if(prof_occupied[week][day][hour]>1) return true;
    }
    return false;
}

bool is_sem_problematic(State& state, Rasp& rasp, std::vector<triplet>& all_dates) {
    for(id_sem sem_id : rasp.mandatory_in_semester_ids) {
        array3D sem_collisions = state.mutable_constraints.sems_collisions[sem_id];
        for(triplet& date : all_dates) {
            int week = std::get<0>(date);
            int day  = std::get<1>(date);
            int hour = std::get<2>(date);
            if(sem_collisions[week][day][hour]>1) return true;
        }
    }
    for(id_sem sem_id : rasp.optional_in_semester_ids) {
        array3D sem_collisions = state.mutable_constraints.sems_collisions[sem_id];
        for(triplet& date : all_dates) {
            int week = std::get<0>(date);
            int day  = std::get<1>(date);
            int hour = std::get<2>(date);
            if(sem_collisions[week][day][hour]>1) return true;
        }
    }
    return false;
}

bool is_rasp_problematic(State& state, Rasp& rasp, id_room room_id) {
    if(is_computer_problematic(state, rasp, room_id) ||
       is_capacity_problematic(state, rasp, room_id)) {
        return true;
    }
    std::vector<triplet>& all_dates = state.rasp_rrules[rasp.id].all_dates;
    if(is_room_problematic(state, room_id, all_dates) ||
       is_prof_problematic(state, rasp, all_dates) ||
       is_sem_problematic(state, rasp, all_dates)) {
        return true;
    }
    return false;
}

int count_rrule_in_mandatory_rasp(State& state, Rasp& rasp, id_sem sem_id,
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
        int new_cnt_colls = old_cnt_colls;
        if(own_group_dates.find(date) == own_group_dates.end()) {
            new_cnt_colls += 1;
        }
        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls);
    }
    return punish;
}

int count_rrule_in_optional_rasp(State& state, Rasp& rasp, id_sem sem_id,
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

        int new_cnt_colls = old_cnt_colls;
        if(own_group_dates.find(date) == own_group_dates.end() &&
           (optionals_occupied[week][day][hour]==0 || other_group_dates.find(date) != other_group_dates.end())) {
            new_cnt_colls += 1;
        }

        punish += sems_tax_punish(old_cnt_occ, old_cnt_colls, old_cnt_occ+1, new_cnt_colls);
    }
    return punish;
}


int count_rrule_in_sems(State& state, Rasp& rasp) {
    std::set<triplet> own_group_dates   = get_own_groups_all_dates(state, rasp);
    std::set<triplet> other_group_dates = get_other_groups_all_dates(state, rasp);
    int punish = 0;
    for(id_sem sem_id : rasp.mandatory_in_semester_ids) {
        punish += count_rrule_in_mandatory_rasp(state, rasp, sem_id, own_group_dates);
    }
    for(id_sem sem_id : rasp.optional_in_semester_ids) {
        punish += count_rrule_in_optional_rasp(state, rasp, sem_id, own_group_dates, other_group_dates);
    }
    return punish;
}

int count_rrule_in_array3D(State& state, Rasp& rasp, array3D arr) {
    std::vector<triplet>& all_dates = state.rasp_rrules[rasp.id].all_dates;
    int cnt = 0;
    for(triplet& date : all_dates) {
        int week = std::get<0>(date);
        int day  = std::get<1>(date);
        int hour = std::get<2>(date);
        if(arr[week][day][hour] + 1 > 1) cnt += (arr[week][day][hour] + 1);
    }
    return -30 * cnt;
}

Grade count_all_collisions(State& state, Slot& slot, Rasp& rasp) {
    array3D room_occupied = state.mutable_constraints.rooms_occupied[slot.room_id];
    array3D prof_occupied = state.mutable_constraints.profs_occupied[rasp.professor_id];
    Grade grade = Grade{0,0,0,0,0,0};
    grade.roomScore      = count_rrule_in_array3D(state, rasp, room_occupied);
    grade.professorScore = count_rrule_in_array3D(state, rasp, prof_occupied);
    grade.semScore       = count_rrule_in_sems(state, rasp);
    grade.capacityScore  = -30 * is_capacity_problematic(state, rasp, slot.room_id);
    grade.computerScore  = -30 * is_strong_computer_problematic(state, rasp, slot.room_id);
    grade.totalScore = grade.roomScore + grade.professorScore + grade.semScore + grade.capacityScore + grade.computerScore;

    return grade;
}

Rasp* random_problematic_rasp(State& state, std::set<id_rasp>& tabu_list) {
    std::vector<Rasp>& shuffled_rasps = state.rasps_in_timetable;
    shuffle_vector(shuffled_rasps);

    for(Rasp& rasp : shuffled_rasps) {
        if(tabu_list.find(rasp.id) != tabu_list.end()) {
            continue;
        }
        id_room room_id = state.timetable[rasp].room_id;
        if(is_rasp_problematic(state, rasp, room_id)) {
            return new Rasp{rasp};
        }
    }
    return NULL;
}

std::pair<Rasp*, Rasp*> problematic_rasp_pair(State& state, std::set<id_rasp>& tabu_list1,
        std::map<id_rasp, std::set<id_rasp>>& tabu_list2) {
    std::vector<Rasp>& shuffled_rasps = state.rasps_in_timetable;
    shuffle_vector(shuffled_rasps);

    Rasp *rasp0=NULL, *rasp1=NULL;
    for(Rasp& rasp : shuffled_rasps) {
        if(tabu_list1.find(rasp.id) != tabu_list1.end()) {
            continue;
        }
        id_room room_id = state.timetable[rasp].room_id;
        if(is_rasp_problematic(state, rasp, room_id)) {
            rasp0 = &rasp;
            break;
        }
    }

    if(!rasp0) {
        return std::pair<Rasp*, Rasp*> {NULL, NULL};
    }

    for(Rasp& pot_rasp1 : shuffled_rasps) {
        bool condition1 = rasp0->id != pot_rasp1.id;
        bool condition2 = tabu_list2[rasp0->id].find(pot_rasp1.id) == tabu_list2[rasp0->id].end();
        bool condition3 = can_swap_rasp_slots(state, *rasp0, pot_rasp1, state.timetable[*rasp0], state.timetable[pot_rasp1]);
        if(condition1 && condition2 && condition3){
            rasp1 = &pot_rasp1;
            break;
        }
    }

    if(!rasp1) {
        return std::pair<Rasp*, Rasp*> {new Rasp{*rasp0}, NULL};
    }
    else {
        return std::pair<Rasp*, Rasp*>{new Rasp{*rasp0}, new Rasp{*rasp1}};
    }
}

std::vector<Rasp> most_problematic_rasps(State& state, float percent) {
    std::vector<std::pair<Rasp, int>> problematic_rasps;
    for(auto it=state.timetable.begin(); it!=state.timetable.end(); ++it) {
        Rasp rasp = it->first;
        Slot old_slot = it->second;
        if(!is_rasp_problematic(state, rasp, old_slot.room_id)) {
            continue;
        }
        Grade only_old_slot_grade = untax_old_slot(state, rasp, old_slot);
        tax_new_slot(state, rasp, old_slot);
        problematic_rasps.emplace_back(rasp, only_old_slot_grade.totalScore);
    }

    std::sort(problematic_rasps.begin(), problematic_rasps.end(),
            [](const std::pair<Rasp, int> &a, const std::pair<Rasp, int> &b) {
                return a.second < b.second;
            });

    int num_keep = std::ceil(problematic_rasps.size() * percent);
    std::vector<Rasp> ret_vector;
    for(int i=0; i<num_keep; i++) {
        ret_vector.push_back(problematic_rasps[i].first);
    }

    return ret_vector;
}
