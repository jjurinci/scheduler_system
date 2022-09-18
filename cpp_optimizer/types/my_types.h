#pragma once
#include <iostream>
#include <vector>
#include <map>
#include <set>
#include <chrono>

typedef std::string id_sem;
typedef std::string id_room;
typedef std::string id_subj;
typedef std::string id_prof;
typedef std::string id_rasp;
typedef std::string subject_type;
typedef std::tuple<int, int, int> triplet;
typedef std::pair<int, int> pair;
typedef std::map<pair, std::vector<pair>> RRULETable_ele;
typedef std::map<id_room, uint8_t***> RoomsOccupied;
typedef uint8_t*** array3D;
typedef std::chrono::system_clock::time_point time_point;

struct BannedSlots {
    std::set<triplet> ban_dates;
    std::set<id_room> ban_rooms;
};

struct Rasp {
    std::string id;
    id_subj subject_id;
    id_prof professor_id;
    std::string type;
    std::string group;
    int duration;
    std::set<id_sem> mandatory_in_semester_ids;
    std::set<id_sem> optional_in_semester_ids;
    bool needs_computers;
    int total_groups;
    std::string fix_at_room_id;
    bool random_dtstart_weekday;
    std::string fixed_hour;
    std::string rrule;
    bool operator<(const Rasp &r) const { return id < r.id; }
    bool operator==(const Rasp &r) const { return id == r.id; }
};

struct Slot {
    id_room room_id;
    int week, day, hour;
    bool operator<(const Slot &s) const { return room_id != s.room_id || week != s.week || day != s.day || hour != s.hour; }
    bool operator==(const Slot &s) const { return room_id == s.room_id && week == s.week && day == s.day && hour == s.hour; }
};

struct Grade {
    int totalScore;
    int roomScore;
    int professorScore;
    int capacityScore;
    int computerScore;
    int semScore;

    Grade operator-(Grade& obj) {
        return Grade{totalScore-obj.totalScore, roomScore-obj.roomScore,
                     professorScore-obj.professorScore, capacityScore-obj.capacityScore,
                     computerScore-obj.computerScore, semScore-obj.semScore};
    }
};

struct Room {
    id_room id;
    std::string name;
    int capacity;
    bool has_computers;
};

struct Semester {
    id_sem id;
    std::string season;
    int num_semester;
    int num_students;
    std::string study_programme_id;
};

struct Timeblock {
    std::string index;
    std::string timeblock;
};

struct TimeStructure {
    tm START_SEMESTER_DATE;
    tm END_SEMESTER_DATE;
    int NUM_WEEKS, NUM_DAYS, NUM_HOURS;
    std::vector<Timeblock> timeblocks;
    std::map<std::string, int> hour_to_index;
    std::map<int, std::string> index_to_hour;
};

struct InitialConstraints {
    std::map<id_room, uint8_t***> rooms_occupied;
    std::map<id_prof, uint8_t***> profs_occupied;
    std::map<id_sem,  uint8_t***> sems_occupied;
    std::map<id_sem,  uint8_t***> optionals_occupied;
    std::map<id_sem,  uint8_t***> sems_collisions;
};

struct MutableConstraints {
    std::map<id_room, uint8_t***> rooms_occupied;
    std::map<id_prof, uint8_t***> profs_occupied;
    std::map<id_sem,  uint8_t***> sems_occupied;
    std::map<id_sem,  uint8_t***> optionals_occupied;
    std::map<id_sem,  uint8_t***> sems_collisions;
};

struct RaspRRULE {
    triplet DTSTART;
    triplet UNTIL;
    std::string FREQ;
    std::vector<triplet> all_dates;
    std::vector<pair> dtstart_weekdays;
    int rrule_table_index;
};

struct State {
    bool is_winter;
    std::map<id_sem, Semester> semesters;
    TimeStructure time_structure;
    std::vector<Rasp> rasps;
    std::vector<Rasp> rasps_in_timetable;
    std::map<id_room, Room> rooms;
    std::map<id_rasp, int> students_per_rasp;
    InitialConstraints initial_constraints;
    MutableConstraints mutable_constraints;
    std::map<subject_type, std::set<id_rasp>> groups;
    std::map<id_subj, std::set<subject_type>> subject_types;
    std::map<Rasp, Slot> timetable;
    Grade grade;
    std::map<id_rasp, RaspRRULE> rasp_rrules;
    std::vector<RRULETable_ele> rrule_table;
};

inline std::ostream& operator<< (std::ostream& o, const Grade& g) {
    o << "totalScore: "<<g.totalScore<<" roomScore: "<<g.roomScore<<" professorScore: "<<g.professorScore<<" capacityScore: "<<g.capacityScore<<" computerScore: "<<g.computerScore<<" semScore: "<<g.semScore;
    return o;
}

inline std::ostream& operator<< (std::ostream& o, const Slot& s) {
    o << "room_id: "<<s.room_id<<" week: "<<s.week<<" day: "<<s.day<<" hour: "<<s.hour;
    return o;
}

inline std::ostream& operator<< (std::ostream& o, const Rasp& r) {
    o << "rasp_id: "<<r.id<<" type: "<<r.type<<" group: "<<r.group<<" duration: "<<r.duration;
    return o;
}
