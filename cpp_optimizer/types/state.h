#pragma once
#include "my_types.h"
#include <vector>
#include <map>
#include <set>
#include <json/json.h>
#include <json/value.h>

std::map<std::string, uint8_t***> get_map_array3D(Json::Value& js_dict, Json::Value::Members js_dict_mems, int NUM_WEEKS,int NUM_DAYS, int NUM_HOURS);

bool get_is_winter(Json::Value& js_is_winter);

std::map<id_sem, Semester> get_semesters(Json::Value& js_semesters);

TimeStructure get_time_structure(Json::Value& js_time_structure);

std::vector<Rasp> get_rasps(Json::Value& js_rasps);

std::vector<Rasp> get_timetable_rasps(std::vector<Rasp> rasps);

std::map<id_room, Room> get_rooms(Json::Value& js_rooms);

std::map<id_rasp, int> get_students_per_rasp(Json::Value& js_students_per_rasp);

InitialConstraints get_initial_constraints(Json::Value& js_initial_constraints, TimeStructure time_structure);

MutableConstraints get_mutable_constraints(Json::Value& js_mutable_constraints, TimeStructure time_structure);

std::map<subject_type, std::set<id_rasp>> get_groups(Json::Value& js_groups);

std::map<id_subj, std::set<subject_type>> get_subject_types(Json::Value& js_subject_types);

std::map<Rasp, Slot> get_timetable(Json::Value& js_timetable, std::vector<Rasp>& rasps);

Grade get_grade(Json::Value& js_grade);

std::map<id_rasp, RaspRRULE> get_rasp_rrules(Json::Value& js_rasp_rrules);

std::vector<RRULETable_ele> get_rrule_table(Json::Value& js_rrule_table);

void clear_mutable(State& state);

std::map<std::string, uint8_t***> deep_copy_constraints(State& state, std::map<std::string, uint8_t***> old_c);

State deep_copy(State& state);

State load_state(std::string path, bool mutable_clear);

