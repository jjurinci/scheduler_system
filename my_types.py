from collections import namedtuple

Rasp = namedtuple('Rasp', ['id', 'subjectId', 'professorId','type', 'group', 'duration', 'mandatory', 'needsComputers', 'totalGroups', 'color', 'fixed', 'fixedAt', 'userId'])
Subject = namedtuple('Subject', ['id', 'name', 'mandatory', 'semesterIds','userId', 'rasps'])

Faculty = namedtuple('Faculty', ['id', 'name', 'userId'])
Semester = namedtuple('Semester', ['id', 'name', 'season', 'numSemester', 'hasOptionalSubjects', 'numStudents', 'facultyId', 'userId'])
Professor = namedtuple('Professor', ['id', 'firstName', 'lastName', 'userId'])
Classroom = namedtuple('Classroom', ['id', 'name', 'capacity', 'hasComputers', 'userId'])

#def raspstr(rasp):
#    return f"R({rasp.type}, {rasp.group}/{rasp.totalGroups}{', R' if rasp.needsComputers else ', .'}{', N' if rasp.color=='n' else ', .'}, {rasp.id})"
#
#setattr(Rasp, "__str__", raspstr)
