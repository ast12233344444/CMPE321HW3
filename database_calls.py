import hashlib
from datetime import datetime


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
                sql = "INSERT INTO Arbiter (username, password, name, surname, nationality, experience_level) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (username, password, name, surname, nationality, experience_level))
        except Exception as e:
            return {"status": 400, "message": f"error occured: {str(e)}"}
        return {"status": 200, "message": "Arbiter Added Into Database."}
    else:
        return {"status": 400, "message": "Password is not valid, check password constraints."}


