from collections import namedtuple
from recordclass import recordclass

# Structure of university
University = namedtuple('University', ['id', 'name'])
Faculty = namedtuple('Faculty', ['id', 'name'])
StudyProgramme = namedtuple('StudyProgramme', ['id', 'name', 'faculty_id'])
Semester = namedtuple('Semester', ['id', 'season', 'num_semester', 'num_students', 'study_programme_id'])
Subject = namedtuple('Subject', ['id', 'name', 'mandatory_in_semester_ids', 'optional_in_semester_ids', 'rasps'])
Rasp = namedtuple('Rasp', ['id', 'subject_id', 'professor_id','type', 'group', 'duration', 'mandatory_in_semester_ids',  'optional_in_semester_ids', 'needs_computers', 'total_groups', 'fix_at_room_id','random_dtstart_weekday','fixed_hour','rrule'])

# Sources of constraints
Classroom = namedtuple('Classroom', ['id', 'name', 'capacity', 'has_computers'])
Professor = namedtuple('Professor', ['id', 'name'])

# Timeblock and slot structure
Timeblock = namedtuple('Timeblock', ['index', 'timeblock'])
Slot = namedtuple('Slot', ['room_id', 'week', 'day', 'hour'])

# STATE parts
TimeStructure = namedtuple('TimeStructure', ['START_SEMESTER_DATE', 'END_SEMESTER_DATE',
                                             'NUM_WEEKS', 'NUM_DAYS', 'NUM_HOURS',
                                             'timeblocks', 'hour_to_index', 'index_to_hour'])

InitialConstraints = namedtuple('InitialConstraints', ['rooms_occupied', 'profs_occupied',
                                                       'sems_occupied', 'optionals_occupied', 'sems_collisions'])
MutableConstraints = namedtuple('MutableConstraints', ['rooms_occupied', 'profs_occupied',
                                                       'sems_occupied', 'optionals_occupied', 'sems_collisions'])

RaspRRULES = namedtuple('RaspRRULES', ["DTSTART", "UNTIL", "FREQ",
                                       "all_dates", "dtstart_weekdays",
                                       "rrule_table_index"])

# STATE
State = recordclass('State',  ['is_winter','semesters',
                              'time_structure', 'rasps',
                              'rooms','students_per_rasp',
                              'initial_constraints',
                              'groups', 'subject_types',
                              'mutable_constraints',
                              'timetable', 'grade',
                              'rasp_rrules', 'rrule_table'])
