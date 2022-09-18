#include "common.h"
#include <random>
#include <algorithm>
#include <sstream>

std::random_device rd;
std::mt19937 gen(rd());

double random_between_0_1(){
    std::uniform_real_distribution<> dist(0, 1);
    return dist(gen);
}

std::vector<int> shuffled_indices(int N) {
    std::vector<int> indices;
    for(int i=0; i<N; i++) {
        indices.push_back(i);
    }
    std::shuffle(indices.begin(), indices.end(), gen);
    return indices;
}

std::set<int> pickSet(int N, int k)
{
    std::set<int> elems;
    for (int r = N - k; r < N; ++r) {
        int v = std::uniform_int_distribution<>(0, r)(gen);

        if (!elems.insert(v).second) {
            elems.insert(r);
        }
    }
    return elems;
}

time_point time_now() {
    return std::chrono::high_resolution_clock::now();
}

double elapsed_secs(time_point start, time_point end) {
    std::chrono::duration<double, std::milli> elapsed = end - start;
    return elapsed.count() / 1000;
}

bool TIME_LIMIT_REACHED(double CPU_TIME_SEC, time_point start) {
    return elapsed_secs(start, time_now()) >= CPU_TIME_SEC;
}

bool is_numeric(std::string const & str)
{
    auto result = double();
    auto i = std::istringstream(str);
    i >> result;
    return !i.fail() && i.eof();
}
