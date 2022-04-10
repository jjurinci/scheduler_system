# Scheduler system

System that solves academic timetables where each subject has its own [rrule](https://dateutil.readthedocs.io/en/stable/rrule.html).

## Dependencies
After cloning the repository, you will need to install the following Python dependencies: **numpy**, **pandas**, **python-dateutil**, **tqdm**, **tabulate**.

## Input

Structure of the input can be found in **/database** directory. User can modify .csv files to represent their university.

## Analyze .csvs

If you wish to check if .csv files are formated properly you can run the command (from /src directory):

```
python -m analysis.analyze_input
python -m analysis.analyze_constraints
```
If there are any errors, they will be printed.

## Convert .csvs to .jsons

Run the command:

```
python -m utilities.csv_to_json
```

This will fill up the **/database/input** and **/database/constraints** directories.

## Run the solver

Now you can run the solver with the following command:
```
python rrule_io.py
```

This will output the **one_state.pickle** file in the **/saved_timetables** directory (can be changed in settings.json).

## Visualize the timetable

To visualize the timetable run the following command:
```
python print_timetable.py > my_timetable.txt
```
Open **my_timetable.txt** with the text editor of your choice.

## Movement of rasps

If you wish to check to which slots a rasp can be moved without any collisions, run the following command:
```
python -m movement.movement
```

If you wish to check to which rooms a rasp can be moved without any collisions, run the following command:
```
python -m movement.room_change
```

## Testing the solution
If you wish to test whether the solver calculated correctly, run the following command:
```
python -m tests.tests
```
If there are any errors, they will be printed.

## Generating random input dataset
If you wish to generate a random input dataset, run the following command:
```
python -m generate_input.generate
```

You can control the distribution via the **/generate_input/generate_config.json** file.<br/>
Keep in mind that you have to modify the **settings.json** paths if you wish to use this dataset as an input to the solver.
