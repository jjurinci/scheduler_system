#include "state.h"
#include <fstream>
#include <json/writer.h>

std::map<std::string, uint8_t***> get_map_array3D(Json::Value& js_dict,
                                                  Json::Value::Members js_dict_mems,
                                                  int NUM_WEEKS,int NUM_DAYS, int NUM_HOURS){
    std::map<std::string, uint8_t***> dict_array3D;
    for(auto it=js_dict_mems.begin(); it!=js_dict_mems.end(); ++it){
        std::string id = it->data();
        uint8_t*** array3D = new uint8_t**[NUM_WEEKS];
        for(int week=0; week<NUM_WEEKS; week++){
            array3D[week] = new uint8_t*[NUM_DAYS];
            for(int day=0; day<NUM_DAYS; day++){
                array3D[week][day] = new uint8_t[NUM_HOURS]{0};
                for(int hour=0; hour<NUM_HOURS; hour++){
                    array3D[week][day][hour] = js_dict[id][week][day][hour].asInt();
                }
            }
        }
        dict_array3D[id] = array3D;
    }
    return dict_array3D;
}

bool get_is_winter(Json::Value& js_is_winter){
    return js_is_winter.asBool();
}

std::map<id_sem, Semester> get_semesters(Json::Value& js_semesters){
    std::map<id_sem, Semester> semesters;
    Json::Value::Members semester_ids = js_semesters.getMemberNames();
    for(auto it=semester_ids.begin(); it!=semester_ids.end(); ++it){
        id_sem semester_id = it->data();
        Json::Value semester = js_semesters[semester_id];
        std::string season = semester["season"].asString();
        int num_semester = semester["num_semester"].asInt();
        int num_students = semester["num_students"].asInt();
        std::string study_programme_id = semester["study_programme_id"].asString();
        Semester sem = Semester{semester_id, season, num_semester, num_students, study_programme_id};
        semesters[semester_id] = sem;
    }
    return semesters;
}

TimeStructure get_time_structure(Json::Value& js_time_structure){
    std::string START_SEMESTER_DATE_str = js_time_structure["START_SEMESTER_DATE"].asString();
    std::string END_SEMESTER_DATE_str   = js_time_structure["END_SEMESTER_DATE"].asString();
    int NUM_WEEKS                       = js_time_structure["NUM_WEEKS"].asInt();
    int NUM_DAYS                        = js_time_structure["NUM_DAYS"].asInt();
    int NUM_HOURS                       = js_time_structure["NUM_HOURS"].asInt();

    struct tm START_SEMESTER_DATE;
    strptime(START_SEMESTER_DATE_str.c_str(), "%Y-%m-%d", &START_SEMESTER_DATE);
    START_SEMESTER_DATE.tm_year += 1900;
    START_SEMESTER_DATE.tm_mon += 1;

    struct tm END_SEMESTER_DATE;
    strptime(END_SEMESTER_DATE_str.c_str(), "%Y-%m-%d", &END_SEMESTER_DATE);
    END_SEMESTER_DATE.tm_year += 1900;
    END_SEMESTER_DATE.tm_mon += 1;

    Json::Value js_timeblocks = js_time_structure["timeblocks"];
    std::vector<Timeblock> timeblocks;
    for(auto it=js_timeblocks.begin(); it!=js_timeblocks.end(); ++it){
        std::string index  = (*it)["index"].asString();
        std::string tblock = (*it)["timeblock"].asString();
        Timeblock timeblock = Timeblock{index, tblock};
        timeblocks.push_back(timeblock);
    }

    Json::Value::Members js_hr_to_idx_mems = js_time_structure["hour_to_index"].getMemberNames();
    std::map<std::string, int> hour_to_index;
    for(auto it=js_hr_to_idx_mems.begin(); it!=js_hr_to_idx_mems.end(); ++it){
        std::string hour = it->data();
        int index = js_time_structure["hour_to_index"][hour].asInt();
        hour_to_index[hour] = index;
    }

    Json::Value::Members js_idx_to_hr_mems = js_time_structure["index_to_hour"].getMemberNames();
    std::map<int, std::string> index_to_hour;
    for(auto it=js_idx_to_hr_mems.begin(); it!=js_idx_to_hr_mems.end(); ++it){
        std::string index = it->data();
        std::string hour  = js_time_structure["index_to_hour"][index].asString();
        index_to_hour[std::stoi(index)] = hour;
    }
    return TimeStructure{START_SEMESTER_DATE, END_SEMESTER_DATE, NUM_WEEKS, NUM_DAYS, NUM_HOURS, timeblocks, hour_to_index, index_to_hour};
}

std::vector<Rasp> get_rasps(Json::Value& js_rasps){
    std::vector<Rasp> rasps;
    std::map<id_rasp, Rasp> rasp_dict;
    for(auto it=js_rasps.begin(); it!=js_rasps.end(); ++it){
        std::string id  = (*it)["id"].asString();
        std::string subject_id = (*it)["subject_id"].asString();
        std::string professor_id = (*it)["professor_id"].asString();
        std::string type = (*it)["type"].asString();
        std::string group = (*it)["group"].asString();
        int duration = (*it)["duration"].asInt();
        bool needs_computers = (*it)["needs_computers"].asBool();
        int total_groups = (*it)["total_groups"].asInt();
        std::string fix_at_room_id = "";
        if(!(*it)["fix_at_room_id"].isNull())
            fix_at_room_id = (*it)["fix_at_room_id"].asString();
        bool random_dtstart_weekday = (*it)["random_dtstart_weekday"].asBool();
        std::string fixed_hour = "";
        if (!(*it)["fixed_hour"].isNull())
            fixed_hour = (*it)["fixed_hour"].asString();
        std::string rrule = (*it)["rrule"].asString();

        std::set<id_sem> mandatory_in_semester_ids;
        Json::Value js_man_in_sem_ids = (*it)["mandatory_in_semester_ids"];
        for(auto it2=js_man_in_sem_ids.begin(); it2!=js_man_in_sem_ids.end(); ++it2){
            id_sem semester_id = (*it2).asString();
            mandatory_in_semester_ids.insert(semester_id);
        }

        std::set<id_sem> optional_in_semester_ids;
        Json::Value js_opt_in_sem_ids = (*it)["optional_in_semester_ids"];
        for(auto it2=js_opt_in_sem_ids.begin(); it2!=js_opt_in_sem_ids.end(); ++it2){
            id_sem semester_id = (*it2).asString();
            optional_in_semester_ids.insert(semester_id);
        }

        Rasp rasp = Rasp{id, subject_id, professor_id, type, group, duration, mandatory_in_semester_ids, optional_in_semester_ids, needs_computers, total_groups, fix_at_room_id, random_dtstart_weekday, fixed_hour, rrule};
        rasps.push_back(rasp);
        rasp_dict[id] = rasp;
    }
    return rasps;
}

std::vector<Rasp> get_timetable_rasps(std::vector<Rasp> rasps) {
    std::vector<Rasp> rasps_in_timetable = rasps;
    return rasps_in_timetable;
}

std::map<id_room, Room> get_rooms(Json::Value& js_rooms){
    Json::Value::Members room_ids = js_rooms.getMemberNames();
    std::map<id_room, Room> rooms;
    for(auto it=room_ids.begin(); it!=room_ids.end(); ++it){
        id_room room_id = it->data();
        Json::Value classroom = js_rooms[room_id];
        std::string name = classroom["name"].asString();
        int capacity = classroom["capacity"].asInt();
        bool has_computers = classroom["has_computers"].asBool();
        Room room = Room{room_id, name, capacity, has_computers};
        rooms[room_id] = room;
    }
    return rooms;
}

std::map<id_rasp, int> get_students_per_rasp(Json::Value& js_students_per_rasp){
    std::map<id_rasp, int> students_per_rasp;
    Json::Value::Members js_students_per_rasp_mems = js_students_per_rasp.getMemberNames();
    for(auto it=js_students_per_rasp_mems.begin(); it!=js_students_per_rasp_mems.end(); ++it){
        id_rasp rasp_id = it->data();
        students_per_rasp[rasp_id] = std::stoi(js_students_per_rasp[rasp_id].asString());
    }
    return students_per_rasp;
}

InitialConstraints get_initial_constraints(Json::Value& js_initial_constraints, TimeStructure time_structure){
    int NUM_WEEKS = time_structure.NUM_WEEKS;
    int NUM_DAYS = time_structure.NUM_DAYS;
    int NUM_HOURS = time_structure.NUM_HOURS;
    std::map<id_room, uint8_t***> i_rooms_occupied     = get_map_array3D(js_initial_constraints["rooms_occupied"], js_initial_constraints["rooms_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> i_profs_occupied     = get_map_array3D(js_initial_constraints["profs_occupied"], js_initial_constraints["profs_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> i_sems_occupied      = get_map_array3D(js_initial_constraints["sems_occupied"],  js_initial_constraints["sems_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> i_optionals_occupied = get_map_array3D(js_initial_constraints["optionals_occupied"], js_initial_constraints["optionals_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> i_sems_collisions    = get_map_array3D(js_initial_constraints["sems_collisions"], js_initial_constraints["sems_collisions"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    return InitialConstraints{i_rooms_occupied, i_profs_occupied, i_sems_occupied, i_optionals_occupied, i_sems_collisions};
}

MutableConstraints get_mutable_constraints(Json::Value& js_mutable_constraints, TimeStructure time_structure){
    int NUM_WEEKS = time_structure.NUM_WEEKS;
    int NUM_DAYS = time_structure.NUM_DAYS;
    int NUM_HOURS = time_structure.NUM_HOURS;
    std::map<id_room, uint8_t***> m_rooms_occupied     = get_map_array3D(js_mutable_constraints["rooms_occupied"], js_mutable_constraints["rooms_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> m_profs_occupied     = get_map_array3D(js_mutable_constraints["profs_occupied"], js_mutable_constraints["profs_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> m_sems_occupied      = get_map_array3D(js_mutable_constraints["sems_occupied"],  js_mutable_constraints["sems_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> m_optionals_occupied = get_map_array3D(js_mutable_constraints["optionals_occupied"], js_mutable_constraints["optionals_occupied"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    std::map<id_room, uint8_t***> m_sems_collisions    = get_map_array3D(js_mutable_constraints["sems_collisions"], js_mutable_constraints["sems_collisions"].getMemberNames(), NUM_WEEKS, NUM_DAYS, NUM_HOURS);
    return MutableConstraints{m_rooms_occupied, m_profs_occupied, m_sems_occupied, m_optionals_occupied, m_sems_collisions};
}

std::map<subject_type, std::set<id_rasp>> get_groups(Json::Value& js_groups){
    std::map<subject_type, std::set<id_rasp>> groups;
    Json::Value::Members js_groups_mems = js_groups.getMemberNames();
    for(auto it=js_groups_mems.begin(); it!=js_groups_mems.end(); ++it){
        subject_type sub_type = it->data();
        Json::Value rasp_id_array = js_groups[sub_type];
        std::set<id_rasp> rasp_set;
        for(auto it2=rasp_id_array.begin(); it2!=rasp_id_array.end(); ++it2){
            rasp_set.insert((*it2).asString());
        }
        groups[sub_type] = rasp_set;
    }
    return groups;
}

std::map<id_subj, std::set<subject_type>> get_subject_types(Json::Value& js_subject_types){
    std::map<id_subj, std::set<subject_type>> subject_types;
    Json::Value::Members js_sub_type_mems = js_subject_types.getMemberNames();
    for(auto it=js_sub_type_mems.begin(); it!=js_sub_type_mems.end(); ++it){
        id_subj subject_id = it->data();
        Json::Value subject_type_array = js_subject_types[subject_id];
        std::set<subject_type> subject_type_set;
        for(auto it2=subject_type_array.begin(); it2!=subject_type_array.end(); ++it2){
            subject_type_set.insert((*it2).asString());
        }
        subject_types[subject_id] = subject_type_set;
    }
    return subject_types;
}

std::map<Rasp, Slot> get_timetable(Json::Value& js_timetable, std::vector<Rasp>& rasps){
    std::map<id_rasp, Rasp> rasp_dict;
    for(auto rasp : rasps)
        rasp_dict[rasp.id] = rasp;

    std::map<Rasp, Slot> timetable;
    Json::Value::Members timetable_mems = js_timetable.getMemberNames();
    for(auto it=timetable_mems.begin(); it!=timetable_mems.end(); ++it){
        id_rasp rasp_id = it->data();
        Json::Value the_slot = js_timetable[rasp_id];
        id_room room_id = the_slot["room_id"].asString();
        int week        = the_slot["week"].asInt();
        int day         = the_slot["day"].asInt();
        int hour        = the_slot["hour"].asInt();
        Rasp rasp = rasp_dict[rasp_id];
        Slot slot = Slot{room_id, week, day, hour};
        timetable[rasp] = slot;
    }
    return timetable;
}

Grade get_grade(Json::Value& js_grade){
    int totalScore     = js_grade["totalScore"].asInt();
    int roomScore      = js_grade["roomScore"].asInt();
    int professorScore = js_grade["professorScore"].asInt();
    int capacityScore  = js_grade["capacityScore"].asInt();
    int computerScore  = js_grade["computerScore"].asInt();
    int semScore       = js_grade["semScore"].asInt();
    return Grade{totalScore, roomScore, professorScore, capacityScore, computerScore, semScore};
}

std::map<id_rasp, RaspRRULE> get_rasp_rrules(Json::Value& js_rasp_rrules){
    std::map<id_rasp, RaspRRULE> rasp_rrules;
    Json::Value::Members js_rasp_rrules_mems = js_rasp_rrules.getMemberNames();
    for(auto it=js_rasp_rrules_mems.begin(); it!=js_rasp_rrules_mems.end(); ++it){
        id_rasp rasp_id = it->data();
        Json::Value js_DTSTART           = js_rasp_rrules[rasp_id]["DTSTART"];
        Json::Value js_UNTIL             = js_rasp_rrules[rasp_id]["UNTIL"];
        Json::Value js_FREQ              = js_rasp_rrules[rasp_id]["FREQ"];
        Json::Value js_all_dates         = js_rasp_rrules[rasp_id]["all_dates"];
        Json::Value js_dtstart_weekdays  = js_rasp_rrules[rasp_id]["dtstart_weekdays"];
        Json::Value js_rrule_table_index = js_rasp_rrules[rasp_id]["rrule_table_index"];

        triplet DTSTART = triplet(-1,-1,-1);
        triplet UNTIL = triplet(-1,-1,-1);
        std::string FREQ =  js_FREQ.asString();
        std::vector<triplet> all_dates;
        std::vector<pair> dtstart_weekdays;
        int rrule_table_index = js_rrule_table_index.asInt();

        for(auto it2 = js_dtstart_weekdays.begin(); it2!=js_dtstart_weekdays.end(); ++it2){
            pair weekday = pair((*it2)[0].asInt(), (*it2)[1].asInt());
            dtstart_weekdays.push_back(weekday);
        }
        RaspRRULE rasp_rrule = RaspRRULE{DTSTART, UNTIL, FREQ, all_dates, dtstart_weekdays, rrule_table_index};
        rasp_rrules[rasp_id] = rasp_rrule;
    }
    return rasp_rrules;
}

std::vector<RRULETable_ele> get_rrule_table(Json::Value& js_rrule_table){
    std::vector<RRULETable_ele> rrule_table;
    for(unsigned int i=0; i<js_rrule_table.size(); ++i){
        Json::Value::Members rrule_table_obj_mems = js_rrule_table[i].getMemberNames();
        RRULETable_ele element;
        for(auto it2=rrule_table_obj_mems.begin(); it2!=rrule_table_obj_mems.end(); ++it2){
            std::string key = it2->data();
            Json::Value js_possible_all_dates = js_rrule_table[i][key];
            std::vector<pair> possible_all_dates;
            for(unsigned int j=0; j<js_possible_all_dates.size(); ++j){
                pair date = pair(js_possible_all_dates[j][0].asInt(), js_possible_all_dates[j][1].asInt());
                possible_all_dates.push_back(date);
            }

            int week = std::stoi(key.substr(1, key.find(",")));
            int day  = std::stoi(key.substr(key.find(" ")+1, key.find(")")));
            pair key_pair = pair{week, day};
            element[key_pair] = possible_all_dates;
        }
        rrule_table.push_back(element);
    }
    return rrule_table;
}

void clear_mutable(State& state) {
    state.timetable.clear();
    state.rasps_in_timetable.clear();
    state.grade = Grade{0,0,0,0,0,0};

    for(auto& it : state.rasp_rrules) {
        id_rasp rasp_id = it.first;
        it.second.DTSTART = triplet{-1, -1, -1};
        it.second.UNTIL   = triplet{-1, -1, -1};
        it.second.all_dates.clear();
    }

    int NUM_WEEKS = state.time_structure.NUM_WEEKS;
    int NUM_DAYS  = state.time_structure.NUM_DAYS;
    int NUM_HOURS = state.time_structure.NUM_HOURS;

    auto& i_rooms_occupied     = state.initial_constraints.rooms_occupied;
    auto& i_profs_occupied     = state.initial_constraints.profs_occupied;
    auto& i_sems_occupied      = state.initial_constraints.sems_occupied;
    auto& i_optionals_occupied = state.initial_constraints.optionals_occupied;
    auto& i_sems_collisions    = state.initial_constraints.sems_collisions;

    auto& m_rooms_occupied     = state.mutable_constraints.rooms_occupied;
    auto& m_profs_occupied     = state.mutable_constraints.profs_occupied;
    auto& m_sems_occupied      = state.mutable_constraints.sems_occupied;
    auto& m_optionals_occupied = state.mutable_constraints.optionals_occupied;
    auto& m_sems_collisions    = state.mutable_constraints.sems_collisions;

    for(int w=0; w<NUM_WEEKS; ++w) {
        for(int d=0; d<NUM_DAYS; ++d) {
            for(int h=0; h<NUM_HOURS; ++h) {
                for(auto it : m_rooms_occupied) {
                    id_room room_id = it.first;
                    m_rooms_occupied[room_id][w][d][h] = i_rooms_occupied[room_id][w][d][h];
                }
                for(auto it : m_profs_occupied) {
                    id_prof prof_id = it.first;
                    m_profs_occupied[prof_id][w][d][h] = i_profs_occupied[prof_id][w][d][h];
                }
                for(auto it : m_sems_occupied) {
                    id_sem sem_id = it.first;
                    m_sems_occupied[sem_id][w][d][h] = i_sems_occupied[sem_id][w][d][h];
                }
                for(auto it : m_optionals_occupied) {
                    id_sem sem_id = it.first;
                    m_optionals_occupied[sem_id][w][d][h] = i_optionals_occupied[sem_id][w][d][h];
                }
                for(auto it : m_sems_collisions) {
                    id_sem sem_id = it.first;
                    m_sems_collisions[sem_id][w][d][h] = i_sems_collisions[sem_id][w][d][h];
                }
            }
        }
    }
}


std::map<std::string, uint8_t***> deep_copy_constraints(State& state, std::map<std::string, uint8_t***> old_c){
    int NUM_WEEKS = state.time_structure.NUM_WEEKS;
    int NUM_DAYS  = state.time_structure.NUM_DAYS;
    int NUM_HOURS = state.time_structure.NUM_HOURS;
    std::map<std::string, uint8_t***> new_c;
    for(auto& it : old_c){
        std::string id = it.first;
        uint8_t*** array3D = new uint8_t**[NUM_WEEKS];
        for(int week=0; week<NUM_WEEKS; week++){
            array3D[week] = new uint8_t*[NUM_DAYS];
            for(int day=0; day<NUM_DAYS; day++){
                array3D[week][day] = new uint8_t[NUM_HOURS]{0};
                for(int hour=0; hour<NUM_HOURS; hour++){
                    array3D[week][day][hour] = old_c[id][week][day][hour];
                }
            }
        }
        new_c[id] = array3D;
    }
    return new_c;
}

State deep_copy(State& state) {
    State new_state = state;

    auto& old_m_rooms_occupied     = state.mutable_constraints.rooms_occupied;
    auto& old_m_profs_occupied     = state.mutable_constraints.profs_occupied;
    auto& old_m_sems_occupied      = state.mutable_constraints.sems_occupied;
    auto& old_m_optionals_occupied = state.mutable_constraints.optionals_occupied;
    auto& old_m_sems_collisions    = state.mutable_constraints.sems_collisions;

    auto new_m_rooms_occupied      = deep_copy_constraints(state, old_m_rooms_occupied);
    auto new_m_profs_occupied      = deep_copy_constraints(state, old_m_profs_occupied);
    auto new_m_sems_occupied       = deep_copy_constraints(state, old_m_sems_occupied);
    auto new_m_optionals_occupied  = deep_copy_constraints(state, old_m_optionals_occupied);
    auto new_m_sems_collisions     = deep_copy_constraints(state, old_m_sems_collisions);

    new_state.mutable_constraints.rooms_occupied     = new_m_rooms_occupied;
    new_state.mutable_constraints.profs_occupied     = new_m_profs_occupied;
    new_state.mutable_constraints.sems_occupied      = new_m_sems_occupied;
    new_state.mutable_constraints.optionals_occupied = new_m_optionals_occupied;
    new_state.mutable_constraints.sems_collisions    = new_m_sems_collisions;

    return new_state;
}

State load_state(std::string path, bool mutable_clear){
    std::ifstream state_file(path);
    Json::Value js_state;
    state_file >> js_state;

    Json::Value js_is_winter           = js_state["is_winter"];
    Json::Value js_semesters           = js_state["semesters"];
    Json::Value js_time_structure      = js_state["time_structure"];
    Json::Value js_rasps               = js_state["rasps"];
    Json::Value js_rooms               = js_state["rooms"];
    Json::Value js_students_per_rasp   = js_state["students_per_rasp"];
    Json::Value js_initial_constraints = js_state["initial_constraints"];
    Json::Value js_mutable_constraints = js_state["mutable_constraints"];
    Json::Value js_groups              = js_state["groups"];
    Json::Value js_subject_types       = js_state["subject_types"];
    Json::Value js_timetable           = js_state["timetable"];
    Json::Value js_grade               = js_state["grade"];
    Json::Value js_rasp_rrules         = js_state["rasp_rrules"];
    Json::Value js_rrule_table         = js_state["rrule_table"];

    bool                                      is_winter = get_is_winter(js_is_winter);
    std::map<id_sem, Semester>                semesters = get_semesters(js_semesters);
    TimeStructure                             time_structure = get_time_structure(js_time_structure);
    std::vector<Rasp>                         rasps = get_rasps(js_rasps);
    std::vector<Rasp>                         rasps_in_timetable = get_timetable_rasps(rasps);
    std::map<id_room, Room>                   rooms = get_rooms(js_rooms);
    std::map<id_rasp, int>                    students_per_rasp = get_students_per_rasp(js_students_per_rasp);
    InitialConstraints                        initial_constraints = get_initial_constraints(js_initial_constraints, time_structure);
    MutableConstraints                        mutable_constraints = get_mutable_constraints(js_mutable_constraints, time_structure);
    std::map<subject_type, std::set<id_rasp>> groups = get_groups(js_groups);
    std::map<id_subj, std::set<subject_type>> subject_types = get_subject_types(js_subject_types);
    std::map<Rasp, Slot>                      timetable = get_timetable(js_timetable, rasps);
    Grade                                     grade = get_grade(js_grade);
    std::map<id_rasp, RaspRRULE>              rasp_rrules = get_rasp_rrules(js_rasp_rrules);
    std::vector<RRULETable_ele>               rrule_table = get_rrule_table(js_rrule_table);

    State state = State{is_winter, semesters, time_structure, rasps, rasps_in_timetable, rooms, students_per_rasp, initial_constraints, mutable_constraints, groups, subject_types, timetable, grade, rasp_rrules, rrule_table};
    if(mutable_clear) clear_mutable(state);
    return state;
}
