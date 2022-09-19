import analysis.input.analyze_semesters              as semesters
import analysis.input.analyze_subjects               as subjects
import analysis.input.analyze_rasps                  as rasps
import analysis.input.analyze_classrooms             as classrooms
import analysis.input.analyze_professors             as professors
import analysis.input.analyze_year                   as year
import analysis.input.analyze_day_struct             as day_struct
import analysis.constraints.analyze_room_constraints as room_cons
import analysis.constraints.analyze_prof_constraints as prof_cons
import utilities.input_csv_to_json as input_csv_to_json

def input_csvs():
    year_success = year.analyze_year()
    day_struct_success = day_struct.analyze_day_struct()

    if not year_success or not day_struct_success:
        return False

    input_csv_to_json.just_time_to_json()

    semesters_success        = semesters.analyze_semesters()
    subjects_success         = subjects.analyze_subjects()
    rasps_success            = rasps.analyze_rasps()
    classrooms_success       = classrooms.analyze_classrooms()
    professors_success       = professors.analyze_professors()

    input_csv_to_json.just_input_to_json()

    room_cons_success = room_cons.analyze_room_available()
    prof_cons_success = prof_cons.analyze_professor_available()

    if semesters_success and subjects_success and rasps_success and classrooms_success \
       and professors_success and room_cons_success and prof_cons_success:
        return True
    else:
        return False

input_csvs()
