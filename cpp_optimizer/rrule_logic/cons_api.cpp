#include "cons_api.h"
#include "../types/state.h"
#include <algorithm>

std::set<triplet> get_own_groups_all_dates(State &state, Rasp &rasp) {
    std::string own_type          = rasp.subject_id + rasp.type;
    std::set<id_rasp>& own_groups = state.groups[own_type];
    std::set<triplet> own_group_dates;
    for(id_rasp rasp_id : own_groups) {
        if(rasp_id != rasp.id) {
            std::vector<triplet>& all_dates = state.rasp_rrules[rasp_id].all_dates;
            for(triplet date : all_dates) {
                own_group_dates.insert(date);
            }
        }
    }
    return own_group_dates;
}

std::set<triplet> get_other_groups_all_dates(State& state, Rasp& rasp) {
    std::string own_type = rasp.subject_id + rasp.type;
    std::set<subject_type>& other_types = state.subject_types[rasp.subject_id];
    std::set<triplet> other_all_dates;
    for(subject_type other_type : other_types) {
        if(other_type == own_type) {
            continue;
        }
        std::set<id_rasp>& type_groups = state.groups[other_type];
        for(id_rasp rasp_id : type_groups) {
            std::vector<triplet>& all_dates = state.rasp_rrules[rasp_id].all_dates;
            for(triplet date : all_dates) {
                other_all_dates.insert(date);
            }
        }
    }
    return other_all_dates;
}
