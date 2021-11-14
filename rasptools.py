from collections import defaultdict
from operator import itemgetter
from tqdm import tqdm
import random
import numpy as np
from multiprocessing import Pool
from itertools import product


class Optimizer:
    def __init__(self, raspovi, nastovi, fixed, free_terms, professor_available, classroom_available, computer_rooms, room_capacity, students):
        self.rasps = raspovi
        self.nasts = nastovi
        self.fixed = fixed
        self.professor_available = dict(**professor_available)
        self.students = students
        self.free_terms = free_terms

        self.computer_rooms = computer_rooms
        self.room_capacity = room_capacity

        occupied = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.int32))
        for room, day, hour in free_terms:
            occupied[room][day,hour] = 0

        for rasp, (room, day, hour) in self.fixed.items():
            occupied[room][day, hour:(hour+rasp.duration)] = 0
        self.occupied = dict(**occupied)

    def initialize_random_sample(self, N):
        sample = []
        for _ in tqdm(range(10*N)):
            avs = self.free_terms.copy()
            avs = list(avs)
            timetable = {}
            for rasp in self.rasps:
                okay = False
                slot = None
                while not okay:
                    slot = random.choice(avs)
                    if slot[2]+rasp.duration<=15:
                        okay = True
                timetable[rasp] = slot
                avs.remove(slot)
            timetable.update(self.fixed)
            sample.append((self.grade(timetable), timetable))
        sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
        sample = sample[:N]
        return sample

    def initialize_from_single_timetable(self, sample0, N):
        sample = [(self.grade(sample0), sample0)]
        for _ in tqdm(range(10*N)):
            s = self.mutate(sample0)
            sample.append((self.grade(s), s))
        sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
        sample = sample[:N]
        return sample


    def grade(self, timetable, verbose=False):
        room_taken = {k:v.copy() for k,v in self.occupied.items()}
        if verbose:
            initial_room_taken = {k:v.copy() for k,v in self.occupied.items()}

        prof_taken = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.int32))
        prof_taken.update({k:v.copy() for k,v in self.professor_available.items()})

        for rasp, (room, day, hour) in timetable.items():
            room_taken[room][day, hour:(hour + rasp.duration)] += 1
            prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)] -= 1

        total_score = 0
        total_room_score, total_professor_score = 0, 0
        total_capacity_score, total_computers_score = 0, 0
        for rasp, (room, day, hour) in timetable.items():

            # Room collisions
            cnt = sum(room_taken[room][day, hour:(hour + rasp.duration)]>1)
            score_rooms = cnt * self.students[rasp]
            if verbose and score_rooms:
                print(f"Room collision ({room}): {score_rooms}")
                print(initial_room_taken[room])
                print(room_taken[room])
                print(rasp)
            total_room_score -= score_rooms
            total_score -= score_rooms

            # Professor collisions
            cnt = sum(prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)]<0)
            score_professors = cnt * self.students[rasp]
            if verbose and score_professors:
                print(f"Professor collision ({rasp.professorId}): {score_professors}")
                print(prof_taken[rasp.professorId])
                print(rasp)
            total_professor_score -= score_professors
            total_score -= score_professors

            # Insufficient room capacity
            capacity = bool(self.students[rasp] - self.room_capacity[room]>=0)
            score_capacity = capacity * rasp.duration * self.students[rasp]
            if verbose and capacity:
                print(f"Capacity ({room},{rasp.subjectId},{self.students[rasp]}): {score_capacity}")
            total_capacity_score -= score_capacity
            total_score -= score_capacity

            # Computer room & computer rasp collisions
            if not room in self.computer_rooms and rasp.needsComputers:
                score_computers = self.students[rasp]
                if verbose and score_computers:
                    print(f"Computer rasp in non-computer room {rasp.subjectId}/{room}: {score_computers}")
                total_computers_score -= score_computers
                total_score -= score_computers

            if room in self.computer_rooms and not rasp.needsComputers:
                score_computers = self.students[rasp] * 0.1
                if verbose and score_computers:
                    print(f"Non-computer rasp in computer room {rasp.subjectId}/{room}: {score_computers}")
                total_computers_score -= score_computers
                total_score -= score_computers

        # Nast collisions
        total_nast_score = 0
        for semester, the_nasts in self.nasts.items():
            score_nasts = 0
            for nast in the_nasts:
                nast_taken =  np.zeros((5,16), dtype=np.int32)
                for rasp in nast:
                    _, day, hour = timetable[rasp]
                    nast_taken[day, hour:(rasp.duration + hour)] += 1
                for rasp in nast:
                    _, day, hour = timetable[rasp]
                    cnt = sum(nast_taken[day, hour:(rasp.duration + hour)]>1)
                    score_nasts += cnt * self.students[rasp]
            if verbose and score_nasts:
                print(f"Nast collisions {semester}: {score_nasts}")
                print(nast_taken)
            total_nast_score -= score_nasts
            total_score -= score_nasts

        final_score = {
                "totalScore": total_score,
                "roomScore": total_room_score,
                "professorScore": total_professor_score,
                "capacityScore": total_capacity_score,
                "computerScore": total_computers_score,
                "nastScore": total_nast_score
        }

        return final_score

    def mutate(self, timetable):
        new_timetable = timetable.copy()
        nonassigned = self.rasps - set(self.fixed.keys())
        rasp0 = random.choice(list(nonassigned))
        new_timetable.pop(rasp0, 0)

        avs = self.free_terms.copy()
        for rasp, (room, day, hour) in new_timetable.items():
            terms = {(room, day, hour+i) for i in range(rasp.duration)}
            avs -= terms

        nonavs = set()
        for (room, day, hour) in avs:
            if any((room, day, hour+i) not in avs for i in range(1,rasp0.duration)):
                nonavs.add((room, day, hour))

        avs -= nonavs
        slot = random.choice(list(avs))
        new_timetable[rasp0] = slot
        return new_timetable


    def crossover(self, timetable1, timetable2):
        return {rasp:random.choice([timetable1[rasp],timetable2[rasp]])
                for rasp in timetable1}


    def cross_and_grade(self, two_timetables):
        one_timetable = self.crossover(two_timetables[0], two_timetables[1])
        return self.grade(one_timetable), one_timetable


    def mutate_and_grade(self, timetable):
        timetable = self.mutate(timetable)
        return self.grade(timetable), timetable


    def iterate(self, sample, generations=100, starting_generation=1, population_cap=512):
        BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
        print(starting_generation-1, BEST_SAMPLE[0])
        for generation in tqdm(range(starting_generation, starting_generation+generations)):

            with Pool(7) as p:
                the_samples = [s[1] for s in sample]

                mutations = p.map(self.mutate_and_grade, the_samples)

                size = len(the_samples) if 10 > len(the_samples) else 10
                cross1 = random.sample(the_samples, size)
                cross2 = random.sample(the_samples, size)
                crossover_pairs = [(t1, t2) for t1, t2 in product(cross1, cross2)]
                crossovers = p.map(self.cross_and_grade, crossover_pairs)

            sample += mutations+crossovers
            sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
            sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
            sample = sample[0:population_cap]
            if sample[0][0]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
                tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")
        return sample
