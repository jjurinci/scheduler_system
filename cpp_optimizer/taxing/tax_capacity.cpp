#include "tax_capacity.h"

void tax_capacity(State& state, id_room room_id, Rasp& rasp) {
    if(state.students_per_rasp[rasp.id] > state.rooms[room_id].capacity){
        state.grade.capacityScore += -30;
        state.grade.totalScore    += -30;
    }
}

void untax_capacity(State& state, id_room room_id, Rasp& rasp) {
    if(state.students_per_rasp[rasp.id] > state.rooms[room_id].capacity){
        state.grade.capacityScore += 30;
        state.grade.totalScore    += 30;
    }
}
