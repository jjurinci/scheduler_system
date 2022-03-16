import analysis.input.analyze_faculties        as faculties
import analysis.input.analyze_study_programmes as study_programmes
import analysis.input.analyze_semesters        as semesters
import analysis.input.analyze_subjects         as subjects
import analysis.input.analyze_rasps            as rasps
import analysis.input.analyze_classrooms       as classrooms
import analysis.input.analyze_professors       as professors

def input_csvs():
    #faculties_success        = faculties.analyze_faculties()
    #study_programmes_success = study_programmes.analyze_study_programmes()
    faculties_success, study_programmes_success = True, True
    semesters_success        = semesters.analyze_semesters()
    subjects_success         = subjects.analyze_subjects()
    rasps_success            = rasps.analyze_rasps()
    classrooms_success       = classrooms.analyze_classrooms()
    professors_success       = professors.analyze_professors()

    if faculties_success and study_programmes_success and semesters_success and \
       subjects_success and rasps_success and classrooms_success and professors_success:
           return True
    else:
        return False

input_csvs()
