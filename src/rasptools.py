import random
import signal
import numpy as np
from tqdm import tqdm
from collections import defaultdict
from multiprocessing import Pool

class Optimizer:
    def __init__(self, data):
        self.rasps = data["rasps"]
        self.nasts = data["nasts"]
        self.fixed = data["fixed"]
        self.free_terms = data["free_terms"]
        self.classroom_occupied = dict(**data["classroom_occupied"])
        self.professor_occupied = dict(**data["professor_occupied"])
        self.computer_rooms = data["computer_rooms"]
        self.room_capacity = data["room_capacity"]
        self.students = data["students_estimate"]
        self.season = data["season"]


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
                avs.remove(slot) #Primitive remove, not taking into account rasp.duration slots, future rasp could take these slots
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


    def grade(self, timetable):
        room_taken = {k:v.copy() for k,v in self.classroom_occupied.items()}
        prof_taken = {k:v.copy() for k,v in self.professor_occupied.items()}

        for rasp, (room, day, hour) in timetable.items():
            room_taken[room][day, hour:(hour + rasp.duration)] += 1
            prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)] += 1

        total_score = 0
        total_room_score, total_professor_score = 0, 0
        total_capacity_score, total_computers_score = 0, 0
        for rasp, (room, day, hour) in timetable.items():

            # Room collisions
            cnt = sum(room_taken[room][day, hour:(hour + rasp.duration)]>1)
            score_rooms = cnt * self.students[rasp]
            total_room_score -= score_rooms
            total_score -= score_rooms

            # Professor collisions
            cnt = sum(prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)]>1)
            score_professors = cnt * self.students[rasp]
            total_professor_score -= score_professors
            total_score -= score_professors

            # Insufficient room capacity
            capacity = bool(self.students[rasp] - self.room_capacity[room]>=0)
            score_capacity = capacity * rasp.duration * self.students[rasp]
            total_capacity_score -= score_capacity
            total_score -= score_capacity

            # Computer room & computer rasp collisions
            if not room in self.computer_rooms and rasp.needsComputers:
                score_computers = self.students[rasp]
                total_computers_score -= score_computers
                total_score -= score_computers

            if room in self.computer_rooms and not rasp.needsComputers:
                score_computers = self.students[rasp] * 0.1
                total_computers_score -= score_computers
                total_score -= score_computers

        # Nast collisions
        total_nast_score = 0
        for semester, the_nasts in self.nasts.items():
            score_nasts = 0
            for nast in the_nasts:
                nast_occupied =  np.zeros((5,16), dtype=np.uint8)
                for rasp in nast:
                    _, day, hour = timetable[rasp]
                    nast_occupied[day, hour:(rasp.duration + hour)] += 1
                for rasp in nast:
                    _, day, hour = timetable[rasp]
                    cnt = sum(nast_occupied[day, hour:(rasp.duration + hour)]>1)
                    score_nasts += cnt * self.students[rasp]
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
            avs -= terms #smart remove slots, takes into account entire rasp.duration

        nonavs = set()
        for (room, day, hour) in avs:
            if any((room, day, hour+i) not in avs for i in range(1,rasp0.duration)):
                nonavs.add((room, day, hour))

        avs -= nonavs #smart remove slots, removes starting slots with insufficient duration to hold rasp0
        slot = random.choice(list(avs)) #there is no way that we create a room collision here, prof collision yes coz prof might be occupied at this time
        new_timetable[rasp0] = slot
        return new_timetable


    def crossover(self, timetable1, timetable2):
        return {rasp:random.choice([timetable1[rasp],timetable2[rasp]])
                for rasp in timetable1}


    def swap(self, timetable):
        new_timetable = timetable.copy()
        nonassigned = self.rasps - set(self.fixed.keys())
        rasp1 = random.choice(list(nonassigned))
        rasp2 = random.choice(list(nonassigned))

        temp = new_timetable[rasp1]
        new_timetable[rasp1] = new_timetable[rasp2]
        new_timetable[rasp2] = temp
        return new_timetable


    def fix_problematic(self, timetable):
        problematic_rasps = []
        prof_taken = {k:v.copy() for k,v in self.professor_occupied.items()}
        room_taken = {k:v.copy() for k,v in self.classroom_occupied.items()}

        for rasp, (room, day, hour) in timetable.items():
            room_taken[room][day, hour:(hour + rasp.duration)] += 1
            prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)] += 1

        # Find problematic rasps
        for rasp, (room, day, hour) in timetable.items():
            room_problem = sum(room_taken[room][day, hour:(hour + rasp.duration)]>1)
            prof_problem = sum(prof_taken[rasp.professorId][day, hour:(hour + rasp.duration)]>1)
            capacity_problem = bool(self.students[rasp] - self.room_capacity[room]>=0)
            computer_problem1 = not room in self.computer_rooms and rasp.needsComputers
            computer_problem2 = room in self.computer_rooms and not rasp.needsComputers

            if room_problem or prof_problem or capacity_problem or computer_problem1 or computer_problem2:
                problematic_rasps.append(rasp)

        new_timetable = timetable.copy()
        if not problematic_rasps:
            return new_timetable

        # Choose a random problematic rasp
        rasp0 = random.choice(problematic_rasps)

        # Check if there is a new free term for it
        avs = self.free_terms.copy()
        for rasp, (room, day, hour) in new_timetable.items():
            terms = {(room, day, hour+i) for i in range(rasp.duration)}
            avs -= terms

        nonavs = set()
        for (room, day, hour) in avs:
            if any((room, day, hour+i) not in avs for i in range(1,rasp0.duration)):
                nonavs.add((room, day, hour))

        avs -= nonavs

        # If there is a new free term, try it
        if avs:
            slot = random.choice(list(avs))
            new_timetable[rasp0] = slot
            return new_timetable


        # Otherwise, find with which other rasps it could potentially swap terms
        potential_swaps = []
        for rasp, (room, day, hour) in new_timetable.items():
            if all((room, day, hour+i) in self.free_terms for i in range(rasp0.duration)):
                potential_swaps.append(rasp)

        if not potential_swaps:
            return new_timetable

        # If there are potential swaps, try a random one
        rasp1 = random.choice(potential_swaps)
        temp = new_timetable[rasp0]
        new_timetable[rasp0] = new_timetable[rasp1]
        new_timetable[rasp1] = temp

        return new_timetable


    def cross_and_grade(self, two_timetables):
        one_timetable = self.crossover(two_timetables[0], two_timetables[1])
        return self.grade(one_timetable), one_timetable


    def mutate_and_grade(self, timetable):
        timetable = self.mutate(timetable)
        return self.grade(timetable), timetable


    def swap_and_grade(self, timetable):
        timetable = self.swap(timetable)
        return self.grade(timetable), timetable


    def prob_and_grade(self, timetable):
        timetable =self.fix_problematic(timetable)
        return self.grade(timetable), timetable


    def iterate(self, sample, generations=100, starting_generation=1, population_cap=512):
        BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
        print(starting_generation-1, BEST_SAMPLE[0])

        for generation in tqdm(range(starting_generation, starting_generation+generations)):
            try:
                original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
                with Pool(7) as p:
                    signal.signal(signal.SIGINT, original_sigint_handler)

                    the_samples = [s[1] for s in sample]

                    mutations = p.map_async(self.mutate_and_grade, the_samples)
                    swaps = p.map_async(self.swap_and_grade, the_samples)
                    probs = p.map_async(self.prob_and_grade, the_samples)

                    #size = len(the_samples) if 11 > len(the_samples) else 10
                    #cross1 = random.sample(the_samples, size)
                    #cross2 = random.sample(the_samples, size)
                    #crossover_pairs = [(t1, t2) for t1, t2 in product(cross1, cross2)]
                    #crossovers = p.map(self.cross_and_grade, crossover_pairs)
                    mutations.wait()
                    swaps.wait()
                    probs.wait()

                sample += probs.get() + mutations.get() + swaps.get() #+crossovers
                sample = [x for i, x in enumerate(sample) if i == sample.index(x)]
                sample.sort(key=lambda x: x[0]["totalScore"], reverse=True)
                sample = sample[0:population_cap]
                if sample[0][0]["totalScore"] > BEST_SAMPLE[0]["totalScore"]:
                    BEST_SAMPLE = (sample[0][0], sample[0][1].copy())
                    tqdm.write(f"{generation}, {BEST_SAMPLE[0]}")

            except KeyboardInterrupt:
                return self.finalize_output(sample)

        return self.finalize_output(sample)


    def finalize_output(self, sample):
        output = []
        for grade, timetable in sample:
            rooms_occupied = {k:v.copy() for k,v in self.classroom_occupied.items()}
            professors_occupied = {k:v.copy() for k,v in self.professor_occupied.items()}
            for rasp, (room, day, hour) in timetable.items():
                rooms_occupied[room][day, hour:(hour + rasp.duration)] += 1
                professors_occupied[rasp.professorId][day, hour:(hour + rasp.duration)] += 1

            nasts_occupied = defaultdict(lambda: np.ones(shape=(5,16), dtype=np.uint8))
            for semester, the_nasts in self.nasts.items():
                sem_id, _, _, _ = semester

                # If student can choose exactly N=1 optional subjects then and
                # only then are apriori parallel optional subjects allowed.
                # There's no upper limit to parallelism, the algorithm could
                # theoretically put all optionals into the same (day, hour) slot.
                # Of course, then it would need a new room for each slot.
                #
                # If student can choose N>=2 optionals then there can be no
                # apriori parallel optional subjects because student could choose
                # any combination of N subjects and therefore they couldn't
                # be in parallel.

                #TODO: Tidy up the variable naming and fetch them from proper places
                NUM_OPTIONALS_ALLOWED = 1
                PARALLEL_OPTIONALS_ALLOWED = True if NUM_OPTIONALS_ALLOWED == 1 else False

                seen_rasps = set()
                nast_occupied = np.zeros((5,16), dtype=np.uint8)
                optionals_occupied = np.zeros((5,16), dtype=np.uint8)
                for nast in the_nasts:
                    for rasp in nast:
                        if rasp.id in seen_rasps:
                            continue

                        seen_rasps.add(rasp.id)
                        _, day, hour = timetable[rasp]

                        # If no parallel rasps then every rasp presence at day,hour is taxed.
                        if rasp.mandatory or not PARALLEL_OPTIONALS_ALLOWED:
                            nast_occupied[day, hour:(rasp.duration + hour)] += 1
                        else:
                            # Only tax optional rasp's presence at day,hour
                            # if it is the first optional rasp at that day,hour.
                            for hr in range(hour, hour + rasp.duration):
                                if optionals_occupied[day, hr] == 0.0:
                                    nast_occupied[day, hr] += 1
                            optionals_occupied[day, hour:(rasp.duration + hour)] += 1

                nasts_occupied[sem_id] = nast_occupied

            data = {"grade": grade,
                    "timetable": timetable,
                    "season": self.season,
                    "rooms_occupied": rooms_occupied,
                    "professors_occupied": professors_occupied,
                    "nasts_occupied": dict(**nasts_occupied),
                    "students_estimate": self.students}
            output.append(data)

        return output
