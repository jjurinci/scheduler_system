#include "../types/my_types.h"
#include "../types/state.h"
#include <iostream>
#include <json/json.h>
#include <json/value.h>
#include <json/writer.h>

Json::Value is_winter_to_js(State& state);

Json::Value semesters_to_js(State& state);

Json::Value time_structure_js(State& state);

Json::Value rasps_to_js(State& state);

Json::Value rooms_to_js(State& state);

Json::Value students_per_rasp_to_js(State& state);

Json::Value dict_array3D_to_js(State& state, std::map<std::string, array3D>& dict);

Json::Value initial_constraints_to_js(State& state);

Json::Value mutable_constraints_to_js(State& state);

Json::Value groups_to_js(State& state);

Json::Value subject_types_to_js(State& state);

Json::Value timetable_to_js(State& state);

Json::Value grade_to_js(State& state);

Json::Value rasp_rrules_to_js(State& state);

Json::Value rrule_table_to_js(State& state);

void save_state_to_json(State& state, std::string path);
