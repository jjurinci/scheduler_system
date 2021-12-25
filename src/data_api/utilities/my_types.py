from collections import namedtuple

Rasp = namedtuple('Rasp', ['id', 'subjectId', 'professorId','type', 'group', 'duration', 'mandatory_in_semesterIds',  'optional_in_semesterIds', 'needsComputers', 'totalGroups', 'fix_at_room_id','random_dtstart_weekday','fixed_hour','rrule'])
Subject = namedtuple('Subject', ['id', 'name', 'mandatory_in_semesterIds', 'optional_in_semesterIds','userId', 'rasps'])
Faculty = namedtuple('Faculty', ['id', 'name', 'userId'])
Semester = namedtuple('Semester', ['id', 'name', 'season', 'numSemester', 'hasOptionalSubjects', 'numStudents', 'facultyId', 'userId'])
Professor = namedtuple('Professor', ['id', 'firstName', 'lastName', 'userId'])
Classroom = namedtuple('Classroom', ['id', 'name', 'capacity', 'hasComputers', 'userId'])
Timeblock = namedtuple('Timeblock', ['index', 'timeblock'])
Slot = namedtuple('Slot', ['room_id', 'week', 'day', 'hour'])
