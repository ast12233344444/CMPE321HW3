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
    date_of_birth: datetime = datetime.strptime(parameters['date_of_birth'], "%D-%M-%Y")
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
    contract_start: datetime = datetime.strptime(parameters['contract_start'], "%D-%M-%Y")
    contract_end: datetime = datetime.strptime(parameters['contract_end'], "%D-%M-%Y")

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
    return log_in_general(username, password, table="Coaches", db_connector=db_connector)

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
        query = f"SELECT P.username, P.elo_rating FROM Players P WHERE P.username IN ({placeholders})"
        cursor.execute(query, most_occurring_names)
        return [(row["username"], row["elo_rating"]) for row in cursor.fetchall()]


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

def get_all_halls(username, db_connector):
    with db_connector.cursor() as cursor:
        query = f"SELECT * from Halls"
        cursor.execute(query)
        return cursor.fetchall()



