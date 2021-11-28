from collections import namedtuple

Rasp = namedtuple('Rasp', ['id', 'subjectId', 'professorId','type', 'group', 'duration', 'mandatory', 'needsComputers', 'totalGroups', 'color', 'fixedAt', 'userId'])
Subject = namedtuple('Subject', ['id', 'name', 'mandatory', 'semesterIds','userId', 'rasps'])
Faculty = namedtuple('Faculty', ['id', 'name', 'userId'])
Semester = namedtuple('Semester', ['id', 'name', 'season', 'numSemester', 'hasOptionalSubjects', 'numStudents', 'facultyId', 'userId'])
Professor = namedtuple('Professor', ['id', 'firstName', 'lastName', 'userId'])
Classroom = namedtuple('Classroom', ['id', 'name', 'capacity', 'hasComputers', 'userId'])