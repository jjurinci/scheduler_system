#pragma once
#include <set>
#include <random>
#include <chrono>
#include <algorithm>

typedef std::chrono::system_clock::time_point time_point;

double random_between_0_1();

std::vector<int> shuffled_indices(int N);

std::set<int> pickSet(int N, int k);

time_point time_now();

double elapsed_secs(time_point start, time_point end);

bool TIME_LIMIT_REACHED(double CPU_TIME_SEC, time_point start);

bool is_numeric(std::string const & str);

template<typename T>
void shuffle_vector(std::vector<T>& vec) {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::shuffle(vec.begin(), vec.end(), gen);
}

template<typename Iter>
Iter select_randomly(Iter start, Iter end) {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, std::distance(start, end) - 1);
    std::advance(start, dis(gen));
    return start;
}
