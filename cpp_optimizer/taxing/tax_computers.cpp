#include "tax_computers.h"

void tax_computers(State& state, id_room room_id, Rasp& rasp) {
    if(!state.rooms[room_id].has_computers && rasp.needs_computers){
        state.grade.computerScore += -30;
        state.grade.totalScore    += -30;
    }
    //else if(state.rooms[room_id].has_computers && !rasp.needs_computers){
    //    state.grade.computerScore += (-30 * 0.1);
    //    state.grade.totalScore    += (-30 * 0.1);
    //}
}

void untax_computers(State& state, id_room room_id, Rasp& rasp) {
    if(!state.rooms[room_id].has_computers && rasp.needs_computers){
        state.grade.computerScore += 30;
        state.grade.totalScore    += 30;
    }
    //else if(state.rooms[room_id].has_computers && !rasp.needs_computers){
    //    state.grade.computerScore += (30 * 0.1);
    //    state.grade.totalScore    += (30 * 0.1);
    //}
}
