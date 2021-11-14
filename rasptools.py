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
        sample.sort(key=itemgetter(0), reverse=True)
        sample = sample[:N]
        return sample

    def initialize_from_single_timetable(self, sample0, N):
        sample = [(self.grade(sample0), sample0)]
        for _ in tqdm(range(10*N)):
            s = self.mutate(sample0)
            sample.append((self.grade(s), s))
        sample.sort(key=lambda x: x[0], reverse=True)
        sample = sample[:N]
        return sample


    def grade(self, timetable, verbose=False):
        score = 0
        dz = {k:v.copy() for k,v in self.occupied.items()}
        if verbose:
            dz0 = {k:v.copy() for k,v in self.occupied.items()}

        ns = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.int32))
        ns.update({k:v.copy() for k,v in self.professor_available.items()})

        for rasp, (room, day, hour) in timetable.items():
            dz[room][day,hour:(hour+rasp.duration)] += 1
            ns[rasp.professorId][day,hour:(hour+rasp.duration)] -= 1

        for rasp, (room, day, hour) in timetable.items():
            cnt = sum(dz[room][day,hour:(hour+rasp.duration)]>1)

            # broj kolizija dvorana i nastavnika
            score_rooms = cnt*self.students[rasp]
            if verbose and score_rooms:
                print(f"Kolizije dvorane ({room}): {score_rooms}")
                print(dz0[room])
                print(dz[room])
                print(repr(rasp))
            score -= score_rooms

            cnt = sum(ns[rasp.professorId][day,hour:(hour+rasp.duration)]<0)

            score_professors = cnt*self.students[rasp]
            if verbose and score_professors:
                print(f"Kolizije nastavnika ({rasp.professorId}): {score_professors}")
                print(ns[rasp.professorId])
                print(repr(rasp))
            score -= score_professors

            # nedostatan kapacitet
            capacity = bool(self.students[rasp]-self.room_capacity[room]>=0)
            score_capacity = capacity * rasp.duration * self.students[rasp]
            if verbose and capacity:
                print(f"Kapacitet ({room},{rasp.subjectId},{self.students[rasp]}): {score_capacity}")
            score -= score_capacity

            # zabranjene dvorane
            if not room in self.computer_rooms and rasp.needsComputers:
                score_computers = self.students[rasp]
                if verbose and score_computers:
                    print(f"Računalnu predmet u ne-računalnoj {rasp.subjectId}/{room}: {score_computers}")
                score -= score_computers

            if room in self.computer_rooms and not rasp.needsComputers:
                score_computers = self.students[rasp]*0.1
                if verbose and score_computers:
                    print(f"Neračunalni predmet u računalnoj {rasp.subjectId}/{room}: {score_computers}")
                score -= score_computers

        # kolizije po nastovima
        for semester, the_nasts in self.nasts.items():
            score_nasts = 0
            for nast in the_nasts:
                z =  np.zeros((5,16), dtype=np.int32)
                for rasp in nast:
                    _, day, hour = timetable[rasp]
                    z[day,hour:(rasp.duration+hour)] += 1
                for rasp in nast:
                    _, day, hour = timetable[rasp]
                    cnt = sum(z[day,hour:(rasp.duration+hour)]>1)
                    score_nasts += cnt*self.students[rasp]
            if verbose and score_nasts:
                print(f"Kolizije na studiju {semester}: {score_nasts}")
                print(z)
            score -= score_nasts
        return score

    def mutate(self, timetable):
        new_timetable = timetable.copy()
        nonassigned = self.rasps - set(self.fixed.keys())
        rasp0 = random.choice(list(nonassigned))
        new_timetable.pop(rasp0, 0)

        avs = self.free_terms.copy()
        for rasp, (dvorana, dan, sat) in new_timetable.items():
            terms = {(dvorana, dan, sat+i) for i in range(rasp.duration)}
            avs -= terms

        nonavs = set()
        for (dvorana, dan, sat) in avs:
            if any((dvorana, dan, sat+i) not in avs for i in range(1,rasp0.duration)):
                nonavs.add((dvorana, dan, sat))

        avs -= nonavs
        slot = random.choice(list(avs))
        new_timetable[rasp0] = slot
        return new_timetable


    def crossover(self, t1, t2):
        return {k:random.choice([t1[k],t2[k]]) for k in t1}


    def cross_and_grade(self, x):
        x1 = self.crossover(x[0], x[1])
        return self.grade(x1), x1


    def mutate_and_grade(self, x):
        x1 = self.mutate(x)
        return self.grade(x1),x1

    def iterate(self, sample, generations=100, starting_generation=1, population_cap=512):
        BEST = (sample[0][0], sample[0][1].copy())
        print(starting_generation-1, BEST[0])
        for generation in tqdm(range(starting_generation, starting_generation+generations)):

            with Pool(7) as p:
                the_samples = [s[1] for s in sample]

                mutations = p.map(self.mutate_and_grade, the_samples)

                cross1 = random.sample(the_samples, 10)
                cross2 = random.sample(the_samples, 10)
                crossover_pairs = [(t1, t2) for t1, t2 in product(cross1, cross2)]
                crossovers = p.map(self.cross_and_grade, crossover_pairs)


            sample += mutations+crossovers
            sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
            sample.sort(key=itemgetter(0), reverse=True)
            sample = sample[0:population_cap]
            if sample[0][0] > BEST[0]:
                BEST = (sample[0][0], sample[0][1].copy())
                tqdm.write(f"{generation}, {BEST[0]}")
        return sample
