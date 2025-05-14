import hashlib
from datetime import datetime


## FINISHED : REGISTRATION, LOGIN, CALLS THAT ARE ONLY GETTING FROM DATABASE
## TO DO : CALLS THAT CHANGE DATABASE, TESTING OF FUNCTIONALITIES

def check_password_validity(password: str) -> bool:
    if len(password) < 8:
        return False

    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False
    special_characters = "!@#$%^&*(),.?\":{}|<>"

    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        elif char in special_characters:
            has_special = True

    return has_upper and has_lower and has_digit and has_special

def hash_password_sha256(password: str) -> str:
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    return sha.hexdigest()

def register_player(parameters: dict, db_connector):
    username: str = parameters['username']
    password: str = parameters['password']
    name: str = parameters['name']
    surname: str = parameters['surname']
    nationality: str = parameters['nationality']
    date_of_birth: datetime = datetime.strptime(parameters['date_of_birth'], "%m/%d/%y") # Corrected format to match main.py
    fide_id: str = parameters['fide_id']
    elo_rating: int = parameters['elo_rating']
    title_id: int = parameters['title_id']

    password_valid = check_password_validity(password)
    if password_valid:
        password = hash_password_sha256(password)
        try:
            with db_connector.cursor() as cursor:
                sql = "INSERT INTO Players (username, password, name, surname, nationality, date_of_birth, fide_id, elo_rating, title_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (username, password, name, surname, nationality, date_of_birth, fide_id, elo_rating, title_id))
        except Exception as e:
            return {"status": 400, "message": f"error occured: {str(e)}"}
        return {"status": 200, "message": "Player Added Into Database."}
    else:
        return {"status": 400, "message": "Password is not valid, check password constraints."}

def register_coach(parameters: dict, db_connector):
    username: str = parameters['username']
    password: str = parameters['password']
    name: str = parameters['name']
    surname: str = parameters['surname']
    nationality: str = parameters['nationality']
    team_id: int = parameters['team_id']
    contract_start: datetime = datetime.strptime(parameters['contract_start'], "%m/%d/%y") # Corrected format to match main.py
    contract_end: datetime = datetime.strptime(parameters['contract_end'], "%m/%d/%y") # Corrected format to match main.py

    password_valid = check_password_validity(password)
    if password_valid:
        password = hash_password_sha256(password)
        try:
            with db_connector.cursor() as cursor:
                sql = "INSERT INTO Coaches (username, password, name, surname, nationality, team_id, contract_start, contract_end) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (username, password, name, surname, nationality, team_id, contract_start, contract_end))
        except Exception as e:
            return {"status": 400, "message": f"error occured: {str(e)}"}
        return {"status": 200, "message": "Coach Added Into Database."}
    else:
        return {"status": 400, "message": "Password is not valid, check password constraints."}

def register_arbiter(params: dict, db_connector):
    username: str = params['username']
    password: str = params['password']
    name: str = params['name']
    surname: str = params['surname']
    nationality: str = params['nationality']
    experience_level: str = params['experience_level']

    password_valid = check_password_validity(password)
    if password_valid:
        password = hash_password_sha256(password)
        try:
            with db_connector.cursor() as cursor:
                sql = "INSERT INTO Arbiters (username, password, name, surname, nationality, experience_level) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (username, password, name, surname, nationality, experience_level))
        except Exception as e:
            return {"status": 400, "message": f"error occured: {str(e)}"}
        return {"status": 200, "message": "Arbiter Added Into Database."}
    else:
        return {"status": 400, "message": "Password is not valid, check password constraints."}

def log_in_general(username, password, table, db_connector):
    with db_connector.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table} WHERE username = %s", (username))
        user_data = cursor.fetchone()
        if user_data:
            password_user = user_data["password"]
            password_given = hash_password_sha256(password)
            if password_user == password_given:
                return {"status": 200, "user_data": user_data}
            else:
                return {"status": 400, "message": "Password does not match."}
        else:
            return {"status": 400, "message": "Username not found."}

def log_in_player(username, password, db_connector):
    return log_in_general(username, password, table="Players", db_connector=db_connector)

def log_in_coach(username, password, db_connector):
    # First, authenticate using the general login function
    auth_result = log_in_general(username, password, table="Coaches", db_connector=db_connector)
    if auth_result.get("status") == 200 and auth_result.get("user_data"):
        coach_data = auth_result["user_data"]
        team_id = coach_data.get("team_id")
        if team_id:
            try:
                with db_connector.cursor() as cursor:
                    cursor.execute("SELECT team_name FROM Teams WHERE team_id = %s", (team_id,))
                    team_data = cursor.fetchone()
                    if team_data:
                        coach_data["team_name"] = team_data["team_name"]
                    else:
                        coach_data["team_name"] = "N/A (Team not found)"
            except Exception as e:
                print(f"Error fetching team name for coach {username}: {str(e)}")
                coach_data["team_name"] = "N/A (Error)"
        else:
            coach_data["team_name"] = "N/A (No team assigned)"
        # Return the augmented coach_data
        return {"status": 200, "user_data": coach_data}
    return auth_result # Return original result if auth failed or no user_data

def log_in_arbiter(username, password, db_connector):
    return log_in_general(username, password, table="Arbiters", db_connector=db_connector)

def log_in_dbmanager(username, password, db_connector):
    return log_in_general(username, password, table="DBManagers", db_connector=db_connector)

            #####PLAYER CALLS#####
def get_player_past_matched_players(username, db_connector):
    with db_connector.cursor() as cursor:
        query_userblack = f"SELECT P.username FROM Players P, MatchAssignments M WHERE (M.black_player = %s AND M.white_player = P.username)"
        query_userwhite = f"SELECT P.username FROM Players P, MatchAssignments M WHERE (M.black_player = P.username AND M.white_player = %s)"

        cursor.execute(query_userblack, (username,))
        white_opponents = [row['username'] for row in cursor.fetchall()]

        cursor.execute(query_userwhite, (username,))
        black_opponents = [row['username'] for row in cursor.fetchall()]

        all_opponent_names = white_opponents + black_opponents

        return all_opponent_names

def get_drwed_users_with_player(username, db_connector):
    with db_connector.cursor() as cursor:
        query_draweduserblack = f"SELECT P.username FROM Players P, MatchAssignments M WHERE (M.black_player = %s AND M.white_player = P.username AND M.result = 'draw')"
        query_draweduserwhite =  f"SELECT P.username FROM Players P, MatchAssignments M WHERE (M.black_player = P.username AND M.white_player = %s AND M.result = 'draw')"

        cursor.execute(query_draweduserblack, (username,))
        white_drawed_opponents = [row["username"] for row in cursor.fetchall()]

        cursor.execute(query_draweduserwhite, (username,))
        black_drawed_opponents = [row["username"] for row in cursor.fetchall()]

        all_drawed_opponents = white_drawed_opponents + black_drawed_opponents

        return all_drawed_opponents

def get_most_played_players_w_elo(username, db_connector):
    with (db_connector.cursor() as cursor):
        all_matches_played_against = get_player_past_matched_players(username, db_connector=db_connector)
        name_occurrences = {}
        max_occurrence = 0
        for name in all_matches_played_against:
            if name in name_occurrences.keys():
                name_occurrences[name] += 1
            else:
                name_occurrences[name] = 1
            max_occurrence = max(max_occurrence, name_occurrences[name])
        most_occurring_names = []
        for name in name_occurrences.keys():
            if name_occurrences[name] == max_occurrence:
                most_occurring_names.append(name)

        placeholders = ','.join(['%s'] * len(most_occurring_names))
        query = f"SELECT P.username, P.name, P.surname, P.elo_rating FROM Players P WHERE P.username IN ({placeholders})"
        cursor.execute(query, most_occurring_names)
        # Return a list of dictionaries for easier access in main.py
        return [{"username": row["username"], "name": row["name"], "surname": row["surname"], "elo_rating": row["elo_rating"]} for row in cursor.fetchall()]


            #### ARBITER CALLS #####
def get_matches_assigned_to_arbiter(username, db_connector):
    with db_connector.cursor() as cursor:
        query = f"SELECT M.match_id FROM Matches M WHERE M.arbiter_username = %s"
        cursor.execute(query, (username))

        return [row["match_id"] for row in cursor.fetchall()]

def get_avg_n_count_ratings_arbiters(username, db_connector):
    with db_connector.cursor() as cursor:
        query = f"SELECT AVG(M.ratings) as avgrating, COUNT(M.ratings) as numrating FROM Matches M WHERE M.arbiter_username = %s"
        cursor.execute(query, (username))
        res = cursor.fetchone()
        return res["avgrating"], res["numrating"]

            ####COACH CALLS####

def get_all_halls(username, db_connector): # username param seems unused if fetching ALL halls
    try:
        with db_connector.cursor() as cursor:
            query = "SELECT hall_id, hall_name, country, capacity FROM Halls ORDER BY hall_name" # Be more specific
            cursor.execute(query)
            return {"status": 200, "halls": cursor.fetchall()}
    except Exception as e:
        return {"status": 500, "message": f"Error fetching halls: {str(e)}", "halls": []}

def get_coach_current_team(coach_username: str, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # Assuming current date logic for active contract.
            # For simplicity, if multiple "current" contracts, picks one.
            # A more robust solution would handle cases with no current team or multiple.
            # Project 1-2: "Being in an agreement with more than one team at the same time is not possible for coaches."
            # Project 1-2: "Each team must be directed by a unique coach."
            # The Coaches table has team_id, contract_start, contract_end.
            # We need the team_id for the coach's current active team.
            # For this version, let's assume the team_id in Coaches table is the current one.
            # A proper check would be: WHERE username = %s AND contract_start <= CURDATE() AND (contract_end >= CURDATE() OR contract_end IS NULL)
            # For now, simplifying to just get the team_id associated with the coach.
            query = """
                SELECT T.team_id, T.team_name
                FROM Coaches C
                JOIN Teams T ON C.team_id = T.team_id
                WHERE C.username = %s 
                -- AND C.contract_start <= CURDATE() AND (C.contract_end >= CURDATE() OR C.contract_end IS NULL) 
                -- The above date check is more robust but adds complexity for now.
                -- Let's assume the Coaches.team_id reflects the current primary assignment for simplicity in P3.
            """
            # Simpler query based on current schema structure:
            query_simple = "SELECT team_id FROM Coaches WHERE username = %s"
            cursor.execute(query_simple, (coach_username,))
            coach_data = cursor.fetchone()
            if coach_data and coach_data.get('team_id'):
                # Now fetch team_name for that team_id
                query_team = "SELECT team_id, team_name FROM Teams WHERE team_id = %s"
                cursor.execute(query_team, (coach_data['team_id'],))
                team_data = cursor.fetchone()
                if team_data:
                    return {"status": 200, "team": team_data}
                else:
                    return {"status": 404, "message": "Coach's team details not found."}
            else:
                return {"status": 404, "message": "Coach not found or not assigned to a team."}
    except Exception as e:
        return {"status": 500, "message": f"Error fetching coach's current team: {str(e)}"}


            #### DB MANAGER CALLS ####
def rename_hall_by_id(hall_id: int, new_hall_name: str, db_connector):
    try:
        with db_connector.cursor() as cursor:
            sql = "UPDATE Halls SET hall_name = %s WHERE hall_id = %s"
            affected_rows = cursor.execute(sql, (new_hall_name, hall_id))
            if affected_rows > 0:
                return {"status": 200, "message": f"Hall ID {hall_id} renamed to '{new_hall_name}'."}
            else:
                return {"status": 404, "message": f"Hall ID {hall_id} not found or name unchanged."}
    except Exception as e:
        return {"status": 500, "message": f"Error renaming hall: {str(e)}"}

def get_all_titles(db_connector):
    try:
        with db_connector.cursor() as cursor:
            query = "SELECT title_id, title_name FROM Titles ORDER BY title_name"
            cursor.execute(query)
            return {"status": 200, "titles": cursor.fetchall()}
    except Exception as e:
        return {"status": 500, "message": f"Error fetching titles: {str(e)}", "titles": []}

def get_all_teams(db_connector):
    try:
        with db_connector.cursor() as cursor:
            query = "SELECT team_id, team_name FROM Teams"
            cursor.execute(query)
            return {"status": 200, "teams": cursor.fetchall()}
    except Exception as e:
        return {"status": 500, "message": f"Error fetching teams: {str(e)}", "teams": []}

def get_all_tables_with_hall_info(db_connector):
    try:
        with db_connector.cursor() as cursor:
            # Joining Tables with Halls to get hall_name and hall_id along with table_id
            query = """
                SELECT T.table_id, T.hall_id, H.hall_name 
                FROM Tables T
                JOIN Halls H ON T.hall_id = H.hall_id
                ORDER BY H.hall_name, T.table_id
            """
            cursor.execute(query)
            return {"status": 200, "tables_with_hall_info": cursor.fetchall()}
    except Exception as e:
        return {"status": 500, "message": f"Error fetching tables with hall info: {str(e)}", "tables_with_hall_info": []}

def get_all_certified_arbiters(db_connector):
    try:
        with db_connector.cursor() as cursor:
            # Select arbiters who have at least one certification
            # We also need their names for the dropdown
            query = """
                SELECT DISTINCT A.username, A.name, A.surname
                FROM Arbiters A
                JOIN ArbiterCertifications AC ON A.username = AC.username
                ORDER BY A.surname, A.name
            """
            cursor.execute(query)
            return {"status": 200, "arbiters": cursor.fetchall()}
    except Exception as e:
        return {"status": 500, "message": f"Error fetching certified arbiters: {str(e)}", "arbiters": []}

def create_new_match(match_details: dict, db_connector):
    try:
        with db_connector.cursor() as cursor:
            hall_id = match_details['hall_id']
            table_id = match_details['table_id']
            match_date = match_details['date'] # Expected in YYYY-MM-DD
            time_slot = int(match_details['time_slot'])
            arbiter_username = match_details['arbiter_username']
            team1_id = match_details['team1_id'] # Coach's team
            team2_id = match_details['team2_id'] # Opponent team

            # Constraint C1, C3, C4: Check for location/time conflict
            # A match occupies time_slot and time_slot + 1
            occupied_slots = [time_slot, time_slot + 1]
            # Ensure time_slot+1 is valid (e.g., not > 4 if that's a hard rule, though PDF implies 4 slots total)
            # For simplicity, this check assumes time_slot+1 is a conceptual next slot.
            # If time_slot is 4, then occupied_slots would be [4, 5]. This needs clarification if slots are strictly 1-4.
            # Project 1-2 PDF: "There are four time slots (e.g., 1,2,3,4) for each day."
            # "A match has a fixed duration of 2 time slots."
            # "if a match starts at time slot 2 ... reserved ... during ... [2,3]"
            # So if a match starts at slot 3, it occupies [3,4]. If it starts at 4, it occupies [4, and conceptually 5, or this is invalid].
            # Let's assume a match cannot start at slot 4 if it needs 2 slots and slots are 1-4.
            # Or, the system allows matches starting at slot 4 to run into the "next day's slot 1 equivalent" - unlikely.
            # Safest assumption: if time_slot is 4, it cannot be scheduled if duration is 2.
            # Project 3 PDF: "Each match lasts 2 consecutive time slots."
            if time_slot == 4: # Max slot given 1-4 range and 2 slot duration
                 return {"status": 400, "message": "Match cannot start at the last time slot (4) as it requires 2 consecutive slots."}
            
            # Check if the location (hall, table) is occupied at the proposed time slots
            sql_loc_conflict = """
                SELECT COUNT(*) as conflict_count 
                FROM Matches 
                WHERE hall_id = %s AND table_id = %s AND date = %s AND time_slot IN (%s, %s)
            """
            cursor.execute(sql_loc_conflict, (hall_id, table_id, match_date, time_slot, time_slot + 1))
            loc_conflict = cursor.fetchone()
            if loc_conflict['conflict_count'] > 0:
                return {"status": 400, "message": f"Location (Hall {hall_id}, Table {table_id}) is already booked for date {match_date} at time slot {time_slot} or {time_slot + 1}."}

            # Constraint C9: Check for arbiter availability
            sql_arb_conflict = """
                SELECT COUNT(*) as conflict_count
                FROM Matches
                WHERE arbiter_username = %s AND date = %s AND time_slot IN (%s, %s)
            """
            cursor.execute(sql_arb_conflict, (arbiter_username, match_date, time_slot, time_slot + 1))
            arb_conflict = cursor.fetchone()
            if arb_conflict['conflict_count'] > 0:
                return {"status": 400, "message": f"Arbiter {arbiter_username} is already assigned to another match on {match_date} at time slot {time_slot} or {time_slot + 1}."}

            # Generate new match_id
            cursor.execute("SELECT COALESCE(MAX(match_id), 0) + 1 as next_match_id FROM Matches")
            next_match_id = cursor.fetchone()['next_match_id']

            # Insert the new match
            sql_insert_match = """
                INSERT INTO Matches (match_id, date, time_slot, hall_id, table_id, team1_id, team2_id, arbiter_username, ratings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL) 
            """
            # Ratings is NULL initially
            cursor.execute(sql_insert_match, (next_match_id, match_date, time_slot, hall_id, table_id, team1_id, team2_id, arbiter_username))
            
            # db_connector.commit() # autocommit is True in db_config
            return {"status": 200, "message": f"Match ID {next_match_id} created successfully.", "match_id": next_match_id}

    except ValueError as ve: # For int(time_slot)
        return {"status": 400, "message": f"Invalid input: {str(ve)}"}
    except Exception as e:
        # Log the full error e for debugging
        print(f"Error in create_new_match: {str(e)}")
        return {"status": 500, "message": f"An unexpected error occurred while creating the match: {str(e)}"}

def get_players_for_team(team_id: int, db_connector):
    try:
        with db_connector.cursor() as cursor:
            query = """
                SELECT P.username, P.name, P.surname, P.elo_rating
                FROM Players P
                JOIN PlayerTeams PT ON P.username = PT.username
                WHERE PT.team_id = %s
                ORDER BY P.surname, P.name
            """
            cursor.execute(query, (team_id,))
            return {"status": 200, "players": cursor.fetchall()}
    except Exception as e:
        return {"status": 500, "message": f"Error fetching players for team {team_id}: {str(e)}", "players": []}

def get_coach_matches_needing_assignment(coach_team_id: int, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # Find matches where the coach's team is team1 and white_player is not assigned,
            # OR coach's team is team2 and black_player is not assigned.
            # This query also fetches opponent team name for display purposes.
            query = """
                SELECT 
                    M.match_id, 
                    M.date, 
                    M.time_slot,
                    H.hall_name,
                    Tbl.table_id,
                    CASE 
                        WHEN M.team1_id = %s THEN T2.team_name 
                        ELSE T1.team_name 
                    END as opponent_team_name,
                    CASE
                        WHEN M.team1_id = %s THEN 'White'
                        ELSE 'Black'
                    END as player_color_to_assign
                FROM Matches M
                LEFT JOIN MatchAssignments MA ON M.match_id = MA.match_id
                JOIN Halls H ON M.hall_id = H.hall_id
                JOIN Tables Tbl ON M.table_id = Tbl.table_id AND M.hall_id = Tbl.hall_id
                JOIN Teams T1 ON M.team1_id = T1.team_id
                JOIN Teams T2 ON M.team2_id = T2.team_id
                WHERE 
                (M.team1_id = %s AND (MA.white_player IS NULL OR MA.white_player = '')) OR
                (M.team2_id = %s AND (MA.black_player IS NULL OR MA.black_player = ''))
                ORDER BY M.date, M.time_slot
            """
            # Parameters for query: coach_team_id (for opponent name), coach_team_id (for player_color),
            # coach_team_id (for team1 check), coach_team_id (for team2 check)
            cursor.execute(query, (coach_team_id, coach_team_id, coach_team_id, coach_team_id))
            matches_to_assign = cursor.fetchall()
            return {"status": 200, "matches_needing_assignment": matches_to_assign}
    except Exception as e:
        print(f"Error in get_coach_matches_needing_assignment: {str(e)}")
        return {"status": 500, "message": f"Error fetching matches needing assignment: {str(e)}", "matches_needing_assignment": []}

def assign_player_to_match_db(match_id: int, player_username: str, assigning_coach_team_id: int, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # 1. Fetch match details to determine player color and check player availability
            cursor.execute("SELECT date, time_slot, team1_id, team2_id FROM Matches WHERE match_id = %s", (match_id,))
            match_info = cursor.fetchone()
            if not match_info:
                return {"status": 404, "message": "Match not found."}

            match_date = match_info['date']
            time_slot = match_info['time_slot']
            team1_id = match_info['team1_id']
            team2_id = match_info['team2_id']

            # 2. Check if player is part of the assigning coach's team
            cursor.execute("SELECT COUNT(*) as count FROM PlayerTeams WHERE username = %s AND team_id = %s", (player_username, assigning_coach_team_id))
            if cursor.fetchone()['count'] == 0:
                return {"status": 400, "message": f"Player {player_username} is not part of your team (ID: {assigning_coach_team_id})."}

            # 3. Constraint C15: Check player availability (not in another match at the same time)
            # A match occupies time_slot and time_slot + 1
            if time_slot == 4: # Should have been caught at match creation, but double check
                 return {"status": 400, "message": "Cannot assign player; match is at an invalid final time slot for 2-slot duration."}

            sql_player_conflict = """
                SELECT COUNT(*) as conflict_count
                FROM MatchAssignments MA
                JOIN Matches M ON MA.match_id = M.match_id
                WHERE (MA.white_player = %s OR MA.black_player = %s)
                  AND M.date = %s 
                  AND M.time_slot IN (%s, %s)
                  AND M.match_id != %s 
            """
            # We check against other matches. If re-assigning for the same match, it's fine.
            cursor.execute(sql_player_conflict, (player_username, player_username, match_date, time_slot, time_slot + 1, match_id))
            player_conflict = cursor.fetchone()
            if player_conflict['conflict_count'] > 0:
                return {"status": 400, "message": f"Player {player_username} is already scheduled for another match at this time."}

            # 4. Determine if assigning white_player or black_player
            player_column_to_assign = None
            if assigning_coach_team_id == team1_id:
                player_column_to_assign = "white_player"
            elif assigning_coach_team_id == team2_id:
                player_column_to_assign = "black_player"
            else:
                return {"status": 400, "message": "Your team is not participating in this match as team1 or team2."}

            # 5. Constraint C16: Check if players from the same team would compete (if other player is already assigned)
            cursor.execute("SELECT white_player, black_player FROM MatchAssignments WHERE match_id = %s", (match_id,))
            current_assignment = cursor.fetchone()
            
            other_player_username = None
            if current_assignment:
                if player_column_to_assign == "white_player" and current_assignment.get('black_player'):
                    other_player_username = current_assignment['black_player']
                elif player_column_to_assign == "black_player" and current_assignment.get('white_player'):
                    other_player_username = current_assignment['white_player']
            
            if other_player_username:
                # Get team of other_player_username
                cursor.execute("SELECT team_id FROM PlayerTeams WHERE username = %s", (other_player_username,))
                # This assumes a player is in only one team for the context of a match, or we take the first.
                # A more robust check might need to consider the specific team they are representing in *that* match if complex.
                # For now, any team membership is checked.
                other_player_teams = cursor.fetchall()
                other_player_team_ids = [t['team_id'] for t in other_player_teams]
                if assigning_coach_team_id in other_player_team_ids:
                     return {"status": 400, "message": f"Cannot assign player. Player {player_username} and opponent player {other_player_username} are from the same team."}


            # 6. Perform INSERT or UPDATE into MatchAssignments
            if current_assignment: # Row exists, so UPDATE
                sql_update_assignment = f"UPDATE MatchAssignments SET {player_column_to_assign} = %s WHERE match_id = %s"
                cursor.execute(sql_update_assignment, (player_username, match_id))
            else: # No row exists, so INSERT
                if player_column_to_assign == "white_player":
                    sql_insert_assignment = "INSERT INTO MatchAssignments (match_id, white_player, black_player, result) VALUES (%s, %s, NULL, NULL)"
                else: # black_player
                    sql_insert_assignment = "INSERT INTO MatchAssignments (match_id, white_player, black_player, result) VALUES (%s, NULL, %s, NULL)"
                cursor.execute(sql_insert_assignment, (match_id, player_username))
            
            return {"status": 200, "message": f"Player {player_username} assigned to match {match_id} as {player_column_to_assign.replace('_', ' ')}."}

    except ValueError as ve:
        return {"status": 400, "message": f"Invalid data for assignment: {str(ve)}."}
    except Exception as e:
        print(f"Error in assign_player_to_match_db: {str(e)}")
        return {"status": 500, "message": f"An unexpected error occurred during player assignment: {str(e)}."}

def get_matches_involving_coach_team(coach_team_id: int, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # Fetches matches where the coach's team is either team1 or team2
            # Also fetches opponent team name for better display
            query = """
                SELECT 
                    M.match_id, 
                    M.date, 
                    M.time_slot,
                    H.hall_name,
                    Tbl.table_id,
                    T1.team_name as team1_name,
                    T2.team_name as team2_name,
                    M.arbiter_username,
                    ARB.name as arbiter_name, ARB.surname as arbiter_surname,
                    MA.white_player,
                    PW.name as white_player_name, PW.surname as white_player_surname,
                    MA.black_player,
                    PB.name as black_player_name, PB.surname as black_player_surname,
                    MA.result,
                    M.ratings
                FROM Matches M
                JOIN Halls H ON M.hall_id = H.hall_id
                JOIN Tables Tbl ON M.table_id = Tbl.table_id AND M.hall_id = Tbl.hall_id
                JOIN Teams T1 ON M.team1_id = T1.team_id
                JOIN Teams T2 ON M.team2_id = T2.team_id
                LEFT JOIN Arbiters ARB ON M.arbiter_username = ARB.username
                LEFT JOIN MatchAssignments MA ON M.match_id = MA.match_id
                LEFT JOIN Players PW ON MA.white_player = PW.username
                LEFT JOIN Players PB ON MA.black_player = PB.username
                WHERE M.team1_id = %s OR M.team2_id = %s
                ORDER BY M.date DESC, M.time_slot DESC
            """
            cursor.execute(query, (coach_team_id, coach_team_id))
            matches = cursor.fetchall()
            return {"status": 200, "matches": matches}
    except Exception as e:
        print(f"Error in get_matches_involving_coach_team: {str(e)}")
        return {"status": 500, "message": f"Error fetching matches for coach's team: {str(e)}", "matches": []}

def delete_match_by_id_for_coach(match_id: int, coach_team_id: int, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # 1. Authorization: Check if the coach's team is part of the match
            cursor.execute("SELECT team1_id, team2_id FROM Matches WHERE match_id = %s", (match_id,))
            match_info = cursor.fetchone()
            if not match_info:
                return {"status": 404, "message": "Match not found."}
            
            if coach_team_id != match_info['team1_id'] and coach_team_id != match_info['team2_id']:
                # Project 3 PDF: "A coach can delete any match they created."
                # This is interpreted as: if their team was team1 (usually the creator's team).
                # A stricter check could be: if coach_team_id != match_info['team1_id']:
                # For now, allowing deletion if their team is involved, as "creator" isn't stored.
                # Let's refine to: only if coach's team is team1, assuming team1 is the creator.
                if coach_team_id != match_info['team1_id']:
                    return {"status": 403, "message": "Unauthorized: You can only delete matches created by your team (as Team 1)."}

            # 2. Deletion (Order matters due to foreign keys if they were set with ON DELETE RESTRICT)
            # First, delete from MatchAssignments
            sql_delete_assignments = "DELETE FROM MatchAssignments WHERE match_id = %s"
            cursor.execute(sql_delete_assignments, (match_id,))
            
            # Then, delete from Matches
            sql_delete_match = "DELETE FROM Matches WHERE match_id = %s"
            deleted_match_rows = cursor.execute(sql_delete_match, (match_id,))
            
            if deleted_match_rows > 0:
                # db_connector.commit() # autocommit is True
                return {"status": 200, "message": f"Match ID {match_id} and its assignments deleted successfully."}
            else:
                # This case should ideally not be reached if match_info was found,
                # unless something went wrong between fetch and delete.
                return {"status": 404, "message": "Match found but could not be deleted from Matches table."}
                
    except Exception as e:
        print(f"Error in delete_match_by_id_for_coach: {str(e)}")
        # db_connector.rollback() # If autocommit was false
        return {"status": 500, "message": f"An unexpected error occurred while deleting the match: {str(e)}."}

def get_detailed_matches_for_arbiter(arbiter_username: str, db_connector):
    try:
        with db_connector.cursor() as cursor:
            query = """
                SELECT 
                    M.match_id, 
                    M.date, 
                    M.time_slot,
                    H.hall_name,
                    Tbl.table_id,
                    T1.team_name as team1_name,
                    T2.team_name as team2_name,
                    MA.white_player,
                    P_W.name as white_player_name, P_W.surname as white_player_surname,
                    MA.black_player,
                    P_B.name as black_player_name, P_B.surname as black_player_surname,
                    M.ratings,
                    MA.result
                FROM Matches M
                JOIN Halls H ON M.hall_id = H.hall_id
                JOIN Tables Tbl ON M.table_id = Tbl.table_id AND M.hall_id = Tbl.hall_id
                JOIN Teams T1 ON M.team1_id = T1.team_id
                JOIN Teams T2 ON M.team2_id = T2.team_id
                LEFT JOIN MatchAssignments MA ON M.match_id = MA.match_id
                LEFT JOIN Players P_W ON MA.white_player = P_W.username
                LEFT JOIN Players P_B ON MA.black_player = P_B.username
                WHERE M.arbiter_username = %s
                ORDER BY M.date DESC, M.time_slot DESC
            """
            cursor.execute(query, (arbiter_username,))
            detailed_matches = cursor.fetchall()
            return {"status": 200, "detailed_matches": detailed_matches}
    except Exception as e:
        print(f"Error in get_detailed_matches_for_arbiter: {str(e)}")
        return {"status": 500, "message": f"Error fetching detailed matches for arbiter: {str(e)}", "detailed_matches": []}

def get_unrated_past_matches_for_arbiter(arbiter_username: str, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # CURDATE() gets the current date in YYYY-MM-DD format in MySQL
            query = """
                SELECT 
                    M.match_id, 
                    M.date, 
                    M.time_slot,
                    H.hall_name,
                    Tbl.table_id,
                    T1.team_name as team1_name,
                    T2.team_name as team2_name
                FROM Matches M
                JOIN Halls H ON M.hall_id = H.hall_id
                JOIN Tables Tbl ON M.table_id = Tbl.table_id AND M.hall_id = Tbl.hall_id
                JOIN Teams T1 ON M.team1_id = T1.team_id
                JOIN Teams T2 ON M.team2_id = T2.team_id
                WHERE M.arbiter_username = %s
                  AND M.date < CURDATE() 
                  AND M.ratings IS NULL
                ORDER BY M.date DESC, M.time_slot DESC
            """
            cursor.execute(query, (arbiter_username,))
            matches = cursor.fetchall()
            return {"status": 200, "unrated_matches": matches}
    except Exception as e:
        print(f"Error in get_unrated_past_matches_for_arbiter: {str(e)}")
        return {"status": 500, "message": f"Error fetching unrated past matches: {str(e)}", "unrated_matches": []}

def submit_match_rating_db(match_id: int, arbiter_username_session: str, rating_value: int, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # 1. Fetch match details
            cursor.execute("SELECT date, arbiter_username, ratings FROM Matches WHERE match_id = %s", (match_id,))
            match_info = cursor.fetchone()

            if not match_info:
                return {"status": 404, "message": "Match not found."}

            # 2. Constraint Checks
            if match_info['arbiter_username'] != arbiter_username_session:
                return {"status": 403, "message": "Unauthorized: You are not the assigned arbiter for this match."}
            
            # Check if date is in the past. match_info['date'] is a datetime.date object from DB.
            # datetime.now().date() gives current date as datetime.date object.
            current_date = datetime.now().date()
            if match_info['date'] >= current_date:
                return {"status": 400, "message": "Cannot rate a match that has not yet occurred or is today."}

            if match_info['ratings'] is not None:
                return {"status": 400, "message": "This match has already been rated."}

            if not (1 <= rating_value <= 10):
                return {"status": 400, "message": "Rating must be an integer between 1 and 10."}

            # 3. Update rating
            # The CHECK constraint in DB also validates 1-10, but app check is good.
            # Adding arbiter_username and ratings IS NULL to WHERE for extra safety.
            sql_update_rating = """
                UPDATE Matches 
                SET ratings = %s 
                WHERE match_id = %s 
                  AND arbiter_username = %s 
                  AND ratings IS NULL 
            """
            affected_rows = cursor.execute(sql_update_rating, (rating_value, match_id, arbiter_username_session))

            if affected_rows > 0:
                return {"status": 200, "message": f"Rating {rating_value} submitted successfully for match ID {match_id}."}
            else:
                # This could happen if another concurrent request rated it, or if initial checks were somehow bypassed.
                return {"status": 409, "message": "Failed to submit rating. Match might have been rated by another process or conditions changed."}

    except ValueError: # For int(rating_value) if it wasn't pre-validated
        return {"status": 400, "message": "Invalid rating value provided."}
    except Exception as e:
        print(f"Error in submit_match_rating_db: {str(e)}")
        return {"status": 500, "message": f"An unexpected error occurred while submitting the rating: {str(e)}."}

def get_detailed_opponent_history(player_username: str, db_connector):
    try:
        with db_connector.cursor() as cursor:
            # Get distinct opponent usernames first
            opponent_usernames = set()
            
            query_white_opponents = """
                SELECT DISTINCT MA.black_player as opponent_username
                FROM MatchAssignments MA
                WHERE MA.white_player = %s AND MA.black_player IS NOT NULL
            """
            cursor.execute(query_white_opponents, (player_username,))
            for row in cursor.fetchall():
                opponent_usernames.add(row['opponent_username'])

            query_black_opponents = """
                SELECT DISTINCT MA.white_player as opponent_username
                FROM MatchAssignments MA
                WHERE MA.black_player = %s AND MA.white_player IS NOT NULL
            """
            cursor.execute(query_black_opponents, (player_username,))
            for row in cursor.fetchall():
                opponent_usernames.add(row['opponent_username'])
            
            if not opponent_usernames:
                return {"status": 200, "opponents": []}

            # Fetch details for these opponent usernames
            placeholders = ', '.join(['%s'] * len(opponent_usernames))
            sql_opponent_details = f"""
                SELECT username, name, surname, elo_rating 
                FROM Players 
                WHERE username IN ({placeholders})
                ORDER BY surname, name
            """
            cursor.execute(sql_opponent_details, tuple(opponent_usernames))
            opponents_details = cursor.fetchall()
            return {"status": 200, "opponents": opponents_details}
            
    except Exception as e:
        print(f"Error in get_detailed_opponent_history: {str(e)}")
        return {"status": 500, "message": f"Error fetching detailed opponent history: {str(e)}", "opponents": []}

def get_player_match_history_detailed(player_username: str, db_connector):
    try:
        with db_connector.cursor() as cursor:
            query = """
                SELECT 
                    M.match_id,
                    M.date,
                    M.time_slot,
                    H.hall_name,
                    Tbl.table_id,
                    T1.team_name AS team1_name,
                    T2.team_name AS team2_name,
                    MA.white_player,
                    P_W.name as white_player_name, P_W.surname as white_player_surname,
                    MA.black_player,
                    P_B.name as black_player_name, P_B.surname as black_player_surname,
                    MA.result,
                    M.ratings AS match_rating_by_arbiter
                FROM Matches M
                JOIN MatchAssignments MA ON M.match_id = MA.match_id
                JOIN Halls H ON M.hall_id = H.hall_id
                JOIN Tables Tbl ON M.table_id = Tbl.table_id AND M.hall_id = Tbl.hall_id
                JOIN Teams T1 ON M.team1_id = T1.team_id
                JOIN Teams T2 ON M.team2_id = T2.team_id
                LEFT JOIN Players P_W ON MA.white_player = P_W.username
                LEFT JOIN Players P_B ON MA.black_player = P_B.username
                WHERE MA.white_player = %s OR MA.black_player = %s
                ORDER BY M.date DESC, M.time_slot DESC
            """
            cursor.execute(query, (player_username, player_username))
            match_history = cursor.fetchall()
            return {"status": 200, "match_history": match_history}
    except Exception as e:
        print(f"Error in get_player_match_history_detailed: {str(e)}")
        return {"status": 500, "message": f"Error fetching player match history: {str(e)}", "match_history": []}
