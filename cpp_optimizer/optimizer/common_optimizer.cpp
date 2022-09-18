#include "../types/my_types.h"

void update_tabu_list(std::set<id_rasp>& tabu_list, Rasp& rasp0, Slot* new_slot_ptr) {
    if(!new_slot_ptr) {
        tabu_list.insert(rasp0.id);
    }
    else {
        tabu_list.clear();
    }
}
