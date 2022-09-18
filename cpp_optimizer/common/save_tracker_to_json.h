#include <json/json.h>
#include <json/value.h>
#include <vector>
#include <iostream>

Json::Value update_tracker_js(Json::Value& tracker_js,
                            std::vector<std::pair<double, int>> tracker,
                            std::string times_name, std::string scores_name);

void save_trackers_to_json();
