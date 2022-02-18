from collections import namedtuple

# Structure of university
University = namedtuple('University', ['id', 'name', 'user_id'])
Faculty = namedtuple('Faculty', ['id', 'name', 'university_id', 'user_id'])
StudyProgramme = namedtuple('StudyProgramme', ['id', 'name', 'faculty_id', 'user_id'])
Semester = namedtuple('Semester', ['id', 'season', 'num_semester', 'has_optional_subjects', 'num_students', 'study_programme_id', 'user_id'])
Subject = namedtuple('Subject', ['id', 'name', 'mandatory_in_semester_ids', 'optional_in_semester_ids','user_id', 'rasps'])
Rasp = namedtuple('Rasp', ['id', 'subject_id', 'professor_id','type', 'group', 'duration', 'mandatory_in_semester_ids',  'optional_in_semester_ids', 'needs_computers', 'total_groups', 'fix_at_room_id','random_dtstart_weekday','fixed_hour','rrule'])

# Sources of constraints
Classroom = namedtuple('Classroom', ['id', 'name', 'capacity', 'has_computers', 'used_in_faculty_ids','user_id'])
Professor = namedtuple('Professor', ['id', 'first_name', 'last_name', 'user_id'])

# Timeblock and slot structure
Timeblock = namedtuple('Timeblock', ['index', 'timeblock'])
Slot = namedtuple('Slot', ['room_id', 'week', 'day', 'hour'])

# STATE parts
TimeStructure = namedtuple('TimeStructure', ['START_SEMESTER_DATE', 'END_SEMESTER_DATE',
                                             'NUM_WEEKS', 'NUM_DAYS', 'NUM_HOURS',
                                             'timeblocks', 'hour_to_index', 'index_to_hour'])

InitialConstraints = namedtuple('InitialConstraints', ['rooms_occupied', 'profs_occupied',
                                                       'nasts_occupied', 'optionals_occupied'])
MutableConstraints = namedtuple('MutableConstraints', ['rooms_occupied', 'profs_occupied',
                                                       'nasts_occupied', 'optionals_occupied'])

RaspRRULES = namedtuple('RaspRRULES', ["DTSTART", "UNTIL", "FREQ",
                                       "all_dates", "dtstart_weekdays",
                                       "possible_all_dates_idx"])

# STATE
State = namedtuple('State',  ['is_winter','semesters',
                              'time_structure',
                              'rooms','students_per_rasp',
                              'initial_constraints',
                              'mutable_constraints',
                              'timetable', 'grades',
                              'rasp_rrules', 'rrule_space',
                              'groups', 'subject_types'])
