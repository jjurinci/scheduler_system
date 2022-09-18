#include "save_tracker_to_json.h"
#include "../optimizer/local_search.h"
#include "../optimizer/variable_neighbor.h"
#include "../optimizer/simulated_annealing.h"
#include <json/json.h>
#include <json/value.h>
#include <json/writer.h>
#include <fstream>

Json::Value update_tracker_js(Json::Value& tracker_js,
                            std::vector<std::pair<double, int>> tracker,
                            std::string times_name, std::string scores_name) {
    Json::Value times  = Json::arrayValue;
    Json::Value scores = Json::arrayValue;
    for(std::pair<double, int> ele : tracker) {
        double time = ele.first;
        int    score = ele.second;
        times.append(time);
        scores.append(score);
    }
    tracker_js[times_name]  = times;
    tracker_js[scores_name] = scores;
    return tracker_js;
}

void save_trackers_to_json() {
    auto vns_tracker   = get_vns_tracker();
    auto grasp_tracker = get_grasp_tracker();
    auto rls_tracker   = get_rls_tracker();
    auto ils_tracker   = get_ils_tracker();
    auto sa_tracker    = get_sa_tracker();
    Json::Value tracker_js;
    update_tracker_js(tracker_js, vns_tracker, "vns_times", "vns_scores");
    update_tracker_js(tracker_js, grasp_tracker, "grasp_times", "grasp_scores");
    update_tracker_js(tracker_js, rls_tracker, "rls_times", "rls_scores");
    update_tracker_js(tracker_js, ils_tracker, "ils_times", "ils_scores");
    update_tracker_js(tracker_js, sa_tracker, "sa_times", "sa_scores");

    std::ofstream file("../results/tracker.json");
    Json::StyledWriter styledWriter;
    file << styledWriter.write(tracker_js);
    file.close();
}
