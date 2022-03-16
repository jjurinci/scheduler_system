import analysis.constraints.analyze_room_constraints as room_cons
import analysis.constraints.analyze_prof_constraints as prof_cons

def constraint_csvs():
    room_cons_success = room_cons.analyze_room_available()
    prof_cons_success = prof_cons.analyze_professor_available()

    if room_cons_success and prof_cons_success:
           return True
    else:
        return False

constraint_csvs()
