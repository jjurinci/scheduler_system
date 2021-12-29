from collections import namedtuple

# Structure of university
University = namedtuple('University', ['id', 'name', 'user_id'])
Faculty = namedtuple('Faculty', ['id', 'name', 'university_id', 'user_id'])
Study_Programme = namedtuple('Study_Programme', ['id', 'name', 'faculty_id', 'user_id'])
Study_Programme_Module = namedtuple('Study_Programme_Module', ['id', 'name', 'study_programme_id', 'user_id'])
Semester = namedtuple('Semester', ['id', 'season', 'num_semester', 'has_optional_subjects', 'num_students', 'study_programme_module_id', 'user_id'])
Subject = namedtuple('Subject', ['id', 'name', 'mandatory_in_semester_ids', 'optional_in_semester_ids','user_id', 'rasps'])
Rasp = namedtuple('Rasp', ['id', 'subject_id', 'professor_id','type', 'group', 'duration', 'mandatory_in_semester_ids',  'optional_in_semester_ids', 'needs_computers', 'total_groups', 'fix_at_room_id','random_dtstart_weekday','fixed_hour','rrule'])

# Sources of constraints
Classroom = namedtuple('Classroom', ['id', 'name', 'capacity', 'has_computers', 'used_in_faculty_ids','user_id'])
Professor = namedtuple('Professor', ['id', 'first_name', 'last_name', 'user_id'])

# Time structure
Timeblock = namedtuple('Timeblock', ['index', 'timeblock'])
Slot = namedtuple('Slot', ['room_id', 'week', 'day', 'hour'])
