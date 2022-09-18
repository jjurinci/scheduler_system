#include "state_to_json.h"
#include "../types/my_types.h"
#include "../types/state.h"
#include <iostream>
#include <json/json.h>
#include <json/value.h>
#include <json/writer.h>
#include <fstream>
#include <string>
#include <cmath>
#include <sstream>
#include <map>

Json::Value is_winter_to_js(State& state) {
    return state.is_winter;
}

Json::Value semesters_to_js(State& state) {
    Json::Value semesters_js;
    for(auto& semester : state.semesters) {
        id_sem sem_id = semester.first;

        Json::Value sem_obj_js;
        sem_obj_js["id"] = semester.second.id;
        sem_obj_js["season"] = semester.second.season;
        sem_obj_js["num_semester"] = semester.second.num_semester;
        sem_obj_js["num_students"] = semester.second.num_students;
        sem_obj_js["study_programme_id"] = semester.second.study_programme_id;
        semesters_js[sem_id] = sem_obj_js;
    }
    return semesters_js;
}

Json::Value time_structure_to_js(State& state) {
    Json::Value time_structure_js;
    int start_year = state.time_structure.START_SEMESTER_DATE.tm_year;
    int start_month = state.time_structure.START_SEMESTER_DATE.tm_mon;
    int start_day = state.time_structure.START_SEMESTER_DATE.tm_mday;
    int end_year = state.time_structure.END_SEMESTER_DATE.tm_year;
    int end_month = state.time_structure.END_SEMESTER_DATE.tm_mon;
    int end_day = state.time_structure.END_SEMESTER_DATE.tm_mday;

    std::string start_year_str = std::to_string(start_year);
    std::string start_month_str = (start_month < 10) ? "0" + std::to_string(start_month) : std::to_string(start_month);
    std::string start_day_str = (start_day < 10) ? "0" + std::to_string(start_day) : std::to_string(start_day);
    std::string end_year_str = std::to_string(end_year);
    std::string end_month_str = (end_month < 10) ? "0" + std::to_string(end_month) : std::to_string(end_month);
    std::string end_day_str = (end_day < 10) ? "0" + std::to_string(end_day) : std::to_string(end_day);

    Json::Value start_sem_js = start_year_str + "-" + start_month_str + "-" + start_day_str + "T" + "00:00:00";
    Json::Value end_sem_js = end_year_str + "-" + end_month_str + "-" + end_day_str + "T" + "00:00:00";

    time_structure_js["START_SEMESTER_DATE"] = start_sem_js;
    time_structure_js["END_SEMESTER_DATE"] = end_sem_js;
    time_structure_js["NUM_WEEKS"] = state.time_structure.NUM_WEEKS;
    time_structure_js["NUM_DAYS"] = state.time_structure.NUM_DAYS;
    time_structure_js["NUM_HOURS"] = state.time_structure.NUM_HOURS;

    Json::Value timeblocks_js;
    for(auto& tblock : state.time_structure.timeblocks) {
        Json::Value timeblock_obj_js;
        timeblock_obj_js["index"] = tblock.index;
        timeblock_obj_js["timeblock"] = tblock.timeblock;
        timeblocks_js.append(timeblock_obj_js);
    }
    time_structure_js["timeblocks"] = timeblocks_js;

    Json::Value hour_to_index_js;
    for(auto& ele : state.time_structure.hour_to_index) {
        hour_to_index_js[ele.first] = ele.second;
    }
    time_structure_js["hour_to_index"] = hour_to_index_js;

    Json::Value index_to_hour_js;
    for(auto& ele : state.time_structure.index_to_hour) {
        index_to_hour_js[std::to_string(ele.first)] = ele.second;
    }
    time_structure_js["index_to_hour"] = index_to_hour_js;

    return time_structure_js;
}

Json::Value rasps_to_js(State& state) {
    Json::Value rasps_js;
    for(auto& rasp : state.rasps) {
        Json::Value obj_rasp_js;
        obj_rasp_js["id"] = rasp.id;
        obj_rasp_js["subject_id"] = rasp.subject_id;
        obj_rasp_js["professor_id"] = rasp.professor_id;
        obj_rasp_js["type"] = rasp.type;
        obj_rasp_js["group"] = rasp.group;
        obj_rasp_js["duration"] = rasp.duration;
        obj_rasp_js["needs_computers"] = rasp.needs_computers;
        obj_rasp_js["total_groups"] = rasp.total_groups;
        obj_rasp_js["random_dtstart_weekday"] = rasp.random_dtstart_weekday;
        obj_rasp_js["rrule"] = rasp.rrule;

        if(rasp.fix_at_room_id == ""){
            obj_rasp_js["fix_at_room_id"] = Json::Value::null;
        }
        else {
            obj_rasp_js["fix_at_room_id"] = rasp.fix_at_room_id;
        }
        if(rasp.fixed_hour == ""){
            obj_rasp_js["fixed_hour"] = Json::Value::null;
        }
        else {
            obj_rasp_js["fixed_hour"] = std::stoi(rasp.fixed_hour);
        }

        Json::Value mandatory_in_sem_ids_js = Json::arrayValue;
        Json::Value optional_in_sem_ids_js = Json::arrayValue;
        for(id_sem sem_id : rasp.mandatory_in_semester_ids) {
            mandatory_in_sem_ids_js.append(sem_id);
        }
        for(id_sem sem_id : rasp.optional_in_semester_ids) {
            optional_in_sem_ids_js.append(sem_id);
        }
        obj_rasp_js["mandatory_in_semester_ids"] = mandatory_in_sem_ids_js;
        obj_rasp_js["optional_in_semester_ids"] = optional_in_sem_ids_js;
        rasps_js.append(obj_rasp_js);
    }
    return rasps_js;
}

Json::Value rooms_to_js(State& state) {
    Json::Value rooms_js;
    for(auto& room : state.rooms) {
        id_room room_id = room.first;
        Json::Value room_obj_js;
        room_obj_js["id"] = room.second.id;
        room_obj_js["name"] = room.second.name;
        room_obj_js["capacity"] = room.second.capacity;
        room_obj_js["has_computers"] = room.second.has_computers;
        rooms_js[room_id] = room_obj_js;
    }
    return rooms_js;
}

Json::Value students_per_rasp_to_js(State& state) {
    Json::Value students_per_rasp_js;
    for(auto& ele : state.students_per_rasp) {
        students_per_rasp_js[ele.first] = ele.second;
    }
    return students_per_rasp_js;
}

Json::Value dict_array3D_to_js(State& state, std::map<std::string, array3D>& dict) {
    int NUM_WEEKS = state.time_structure.NUM_WEEKS;
    int NUM_DAYS  = state.time_structure.NUM_DAYS;
    int NUM_HOURS = state.time_structure.NUM_HOURS;
    Json::Value dict_js;
    for(auto& key : dict) {
        std::string id = key.first;
        array3D arr = key.second;
        Json::Value arr_js = Json::arrayValue;
        for(int w=0; w<NUM_WEEKS; ++w) {
            arr_js.append(Json::arrayValue);
            for(int d=0; d<NUM_DAYS; ++d) {
                arr_js[w].append(Json::arrayValue);
                for(int h=0; h<NUM_HOURS; ++h) {
                    arr_js[w][d].append(arr[w][d][h]);
                }
            }
        }
        dict_js[id] = arr_js;
    }
    return dict_js;
}

Json::Value initial_constraints_to_js(State& state) {
    Json::Value initial_constraints_js;
    initial_constraints_js["rooms_occupied"]     = dict_array3D_to_js(state, state.initial_constraints.rooms_occupied);
    initial_constraints_js["profs_occupied"]     = dict_array3D_to_js(state, state.initial_constraints.profs_occupied);
    initial_constraints_js["sems_occupied"]      = dict_array3D_to_js(state, state.initial_constraints.sems_occupied);
    initial_constraints_js["optionals_occupied"] = dict_array3D_to_js(state, state.initial_constraints.optionals_occupied);
    initial_constraints_js["sems_collisions"]    = dict_array3D_to_js(state, state.initial_constraints.sems_collisions);
    return initial_constraints_js;
}

Json::Value mutable_constraints_to_js(State& state) {
    Json::Value mutable_constraints_js;
    mutable_constraints_js["rooms_occupied"]     = dict_array3D_to_js(state, state.mutable_constraints.rooms_occupied);
    mutable_constraints_js["profs_occupied"]     = dict_array3D_to_js(state, state.mutable_constraints.profs_occupied);
    mutable_constraints_js["sems_occupied"]      = dict_array3D_to_js(state, state.mutable_constraints.sems_occupied);
    mutable_constraints_js["optionals_occupied"] = dict_array3D_to_js(state, state.mutable_constraints.optionals_occupied);
    mutable_constraints_js["sems_collisions"]    = dict_array3D_to_js(state, state.mutable_constraints.sems_collisions);
    return mutable_constraints_js;
}

Json::Value groups_to_js(State& state) {
    Json::Value groups_js;
    for(auto& ele : state.groups) {
        std::string subject_type_js = ele.first;
        Json::Value rasp_ids_js(Json::arrayValue);
        for(auto& rasp_id : ele.second) {
            rasp_ids_js.append(rasp_id);
        }
        groups_js[subject_type_js] = rasp_ids_js;
    }
    return groups_js;
}

Json::Value subject_types_to_js(State& state) {
    Json::Value subject_types_js;
    for(auto& ele : state.subject_types) {
        std::string subject_id = ele.first;
        Json::Value sub_types_js(Json::arrayValue);
        for(auto& subject_type : ele.second) {
            sub_types_js.append(subject_type);
        }
        subject_types_js[subject_id] = sub_types_js;
    }
    return subject_types_js;
}

Json::Value timetable_to_js(State& state) {
    Json::Value timetable_js;
    for(auto& ele : state.timetable) {
        id_rasp rasp_id = ele.first.id;
        Json::Value slot_js;
        slot_js["room_id"] = ele.second.room_id;
        slot_js["week"] = ele.second.week;
        slot_js["day"] = ele.second.day;
        slot_js["hour"] = ele.second.hour;
        timetable_js[rasp_id] = slot_js;
    }
    return timetable_js;
}

Json::Value grade_to_js(State& state) {
    Json::Value grade_js;
    grade_js["totalScore"]     = state.grade.totalScore;
    grade_js["roomScore"]      = state.grade.roomScore;
    grade_js["professorScore"] = state.grade.professorScore;
    grade_js["capacityScore"]  = state.grade.capacityScore;
    grade_js["computerScore"]  = state.grade.computerScore;
    grade_js["semScore"]       = state.grade.semScore;
    return grade_js;
}

Json::Value rasp_rrules_to_js(State& state) {
    Json::Value rasp_rrules_js;

    for(auto& ele : state.rasp_rrules) {
        Json::Value rasp_rrule_obj;
        id_rasp rasp_id = ele.first;
        auto rasp_rrule = ele.second;
        int dt_week = std::get<0>(rasp_rrule.DTSTART);
        int dt_day  = std::get<1>(rasp_rrule.DTSTART);
        int dt_hour = std::get<2>(rasp_rrule.DTSTART);
        int un_week = std::get<0>(rasp_rrule.UNTIL);
        int un_day  = std::get<1>(rasp_rrule.UNTIL);
        int un_hour = std::get<2>(rasp_rrule.UNTIL);

        Json::Value DTSTART_js(Json::arrayValue);
        Json::Value UNTIL_js(Json::arrayValue);
        DTSTART_js.append(dt_week);
        DTSTART_js.append(dt_day);
        DTSTART_js.append(dt_hour);
        UNTIL_js.append(un_week);
        UNTIL_js.append(un_day);
        UNTIL_js.append(un_hour);

        Json::Value all_dates_js(Json::arrayValue);
        for(auto& date : rasp_rrule.all_dates) {
            int week = std::get<0>(date);
            int day  = std::get<1>(date);
            int hour = std::get<2>(date);
            Json::Value date_js(Json::arrayValue);
            date_js.append(week);
            date_js.append(day);
            date_js.append(hour);
            all_dates_js.append(date_js);
        }

        Json::Value dtstart_weekdays_js(Json::arrayValue);
        for(auto& weekday : rasp_rrule.dtstart_weekdays) {
            int week = std::get<0>(weekday);
            int day  = std::get<1>(weekday);
            Json::Value weekday_js(Json::arrayValue);
            weekday_js.append(week);
            weekday_js.append(day);
            dtstart_weekdays_js.append(weekday_js);
        }

        rasp_rrule_obj["DTSTART"] = DTSTART_js;
        rasp_rrule_obj["UNTIL"]   = UNTIL_js;
        rasp_rrule_obj["FREQ"]    = rasp_rrule.FREQ;
        rasp_rrule_obj["all_dates"]         = all_dates_js;
        rasp_rrule_obj["dtstart_weekdays"]  = dtstart_weekdays_js;
        rasp_rrule_obj["rrule_table_index"] = rasp_rrule.rrule_table_index;
        rasp_rrules_js[rasp_id] = rasp_rrule_obj;
    }
    return rasp_rrules_js;
}

Json::Value rrule_table_to_js(State& state) {
    Json::Value rrule_table_js(Json::arrayValue);
    for(auto& table_ele : state.rrule_table) {
        Json::Value obj_js;
        for(auto& obj : table_ele) {
            pair key = obj.first;
            std::string key_str = "(" + std::to_string(key.first) + ", " + std::to_string(key.second) + ")";

            Json::Value possible_all_dates_js(Json::arrayValue);
            auto possible_all_dates = obj.second;
            for(auto& date : possible_all_dates) {
                int week = std::get<0>(date);
                int day  = std::get<1>(date);
                Json::Value date_js(Json::arrayValue);
                date_js.append(week);
                date_js.append(day);
                possible_all_dates_js.append(date_js);
            }

            obj_js[key_str] = possible_all_dates_js;
        }
        rrule_table_js.append(obj_js);
    }
    return rrule_table_js;
}

void save_state_to_json(State& state, std::string path) {
    Json::Value state_js;
    state_js["is_winter"] = is_winter_to_js(state);
    state_js["semesters"] = semesters_to_js(state);
    state_js["time_structure"] = time_structure_to_js(state);
    state_js["rasps"] = rasps_to_js(state);
    state_js["rooms"] = rooms_to_js(state);
    state_js["students_per_rasp"] = students_per_rasp_to_js(state);
    state_js["initial_constraints"] = initial_constraints_to_js(state);
    state_js["mutable_constraints"] = mutable_constraints_to_js(state);
    state_js["groups"] = groups_to_js(state);
    state_js["subject_types"] = subject_types_to_js(state);
    state_js["timetable"] = timetable_to_js(state);
    state_js["grade"] = grade_to_js(state);
    state_js["rasp_rrules"] = rasp_rrules_to_js(state);
    state_js["rrule_table"] = rrule_table_to_js(state);

    std::ofstream file(path);
    Json::StyledWriter styledWriter;
    file << styledWriter.write(state_js);
    file.close();
}
