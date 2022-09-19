# Sustav za optimiranje akademskih rasporeda temeljenih na ponavljajućim pravilima norme iCalendar

### Diplomski rad

Autor: Jurica Jurinčić

Mentor: doc. dr. sc. Nikola Tanković

Komentor: doc. dr. sc. Siniša Miličić

Sveučilište Jurja Dobrile u Puli, Fakultet informatike

### Sažetak

Optimizacija akademskog rasporeda je NP-težak problem koji se često pojavljuje u
praksi. Zbog nepostojanja boljih algoritama, obično se koriste heuristički algoritmi koji
daju zadovoljavajuća rješenja za praktične potrebe. Različiti autori problem različito
definiraju zbog proizvoljnosti ograničenja koja njihova sveučilišta imaju. U ovom radu je
dana jedna moguća definicija koja omogućuje da svaka grupa predmeta ima
ponavljajuće pravilo po kojemu će se vremenski održavati uz optimizaciju kršenja
ograničenja kao što su kolizije vremena dvorana, profesora, semestara, kapaciteta,
računalnosti, i sl. Za ponavljajuća pravila se koristi [RRULE](https://dateutil.readthedocs.io/en/stable/rrule.html) iz iCalendar RFC 5545
specifikacije. U praktičnom dijelu je ulaz analiziran, rastavljen na dijelove i pretvoren u
rješenje uz pomoć optimizacijskih algoritama. Specifično, implementirani su sljedeći
algoritmi: ponavljano lokalno traženje, iterirano lokalno traženje, pretraživanje
promjenjivim susjedstvom, simulirano kaljenje, i pohlepno randomizirano adaptivno
pretraživanje.

# System for optimizing academic timetables based on iCalendar recurring rules

### Master's thesis
Author: Jurica Jurinčić

Mentor: doc. dr. sc. Nikola Tanković

Co-mentor: doc. dr. sc. Siniša Miličić

Juraj Dobrila University of Pula, Faculty of Informatics

### Abstract

Academic timetable optimization is an NP-hard problem that often appears in practice.
In the absence of better algorithms, heuristic algorithms are usually used, which provide
satisfactory solutions for practical needs. Different authors define the problem differently
due to the arbitrariness of the restrictions that their universities have. In this thesis, one
possible definition is given that allows each group of subjects to have a recurring rule
according to which it will be maintained in time while optimizing the violation of
restrictions such as collisions of the time of rooms, professors, semesters, capacity,
computers, etc. For recurring rules, [RRULE](https://dateutil.readthedocs.io/en/stable/rrule.html) from the iCalendar RFC 5545 specification
is used. In the practical part, the input is analyzed, divided into parts, and turned into a
solution with the help of optimization algorithms. Specifically, the following algorithms
are presented: repeated local search, iterated local search, variable neighborhood
search, simulated annealing, and greedy randomized adaptive search procedure.
Algorithms were finally tested on different datasets where their performance was
compared.

![GIF](https://github.com/jjurinci/scheduler_system/blob/main/readme_static/cli.gif)

# How to use

## Dependencies
Clone the repository and install the Python dependencies: **numpy**, **pandas**, **python-dateutil**, **tqdm**, **tabulate**, **recordclass**.
```
git clone https://github.com/jjurinci/scheduler_system.git
cd scheduler_system
pip install -r requirements.txt
```

## Input

Represent your university in the **database** directory. You can do this by changing the .csv files there.

In the **database/input** directory, the following can be changed:
- faculties.csv
- study_programmes.csv
- semesters.csv
- subjects.csv
- rasps.csv (Rasp is a group of subject. If subject is Mathematics, then rasp can be Mathematics Exercise Group 1 or Mathematics Lecture Group 4, ...)
- classrooms.csv
- professors.csv
- start_end_year.csv (Starting and ending date of the academic year)
- day_structure.csv  (Academic timeblocks of a workday)

In the **database/constraints** directory, the following can be changed:
- classroom_available.csv
- professor_available.csv

**database/constraints** is concerned with limiting the available time of classrooms and professors. "T" means available entire day, "F" means not available that day, and a comma separated list of numbers describes which academic timeblocks are available for that day (for example: "1,5,8,15" means "available only from 1st to 5th academic hour inclusive and from 8th to 15th academic hour inclusive").

## Analyze .csvs

Check if .csv files are properly formatted by running the following commands:

```
python -m analysis.analyze_input
python -m analysis.analyze_constraints
```
If there are any errors, they will be printed out.

## Run the command line interface

Once the .csv files are properly formatted, run the CLI:
```
python cli.py
```

You can choose between the Python and C++ (uses make) optimizers which both implement 5 optimization algorithms:
- Variable Neighborhood Search
- Simulated Annealing
- Repeated Local Search
- Iterated Local Search
- Greedy Randomized Adaptive Search Procedure

If everything went as planned, the resulting timetable will be saved in the **saved_timetables/state.pickle** file. Visual representation will be saved in the **timetable.txt** file.

Once **saved_timetables/state.pickle** is generated, you can perform the operations described below.

## Timetable collisions

Check which collisions the generated timetables has:
```
python -m movement.timetable_problems
```

## Movement of rasps

Check to which slots a rasp can be moved to without any collisions:
```
python -m movement.movement
```

Check to which rooms (and at which slots) a rasp can be moved to without any collisions:
```
python -m movement.room_change
```

## Generating random input dataset
If you wish to generate a random input dataset:
```
python -m generate_input.generate
```

.csvs will be saved in **generate_input/csvs** directory.
.jsons will be saved in **generate_input/jsons** directory.

To control the distribution, change the **/generate_input/generate_config.json** file.

To use this dataset as an input, modify the **settings.json** paths.
