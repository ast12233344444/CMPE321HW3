from flask import Flask, request
import pandas as pd
import pymysql
import argparse
from datetime import datetime
from database_calls import hash_password_sha256

app = Flask(__name__)

# --- MySQL config ---
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'root'
DB_PASS = 'password' # Updated to match your provided password
DB_NAME = "HW3"


def get_mysql_connection():
    return pymysql.connect(host=DB_HOST,
                           user=DB_USER,
                           password=DB_PASS,
                           port=DB_PORT,
                           database=DB_NAME,
                           cursorclass=pymysql.cursors.DictCursor)

def create_table_dbmanagers(df: pd.DataFrame, db_connector):
    table_name = 'DBManagers'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username VARCHAR(255), password TEXT, PRIMARY KEY (username));")

        for _, row in df.iterrows():
            password = hash_password_sha256(str(row["password"])) # Ensure password is a string
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['username'], password))

def create_table_players(df: pd.DataFrame, db_connector):
    table_name = 'Players'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username VARCHAR(255), password TEXT, name TEXT, surname TEXT, nationality TEXT, date_of_birth DATE, fide_id VARCHAR(255), elo_rating INT, title_id INT, "
                       f"PRIMARY KEY (username), FOREIGN KEY (title_id) REFERENCES Titles(title_id), "
                       f"UNIQUE (fide_id), CHECK (elo_rating > 1000));")

        for _, row in df.iterrows():
            password = hash_password_sha256(str(row["password"])) # Ensure password is a string
            # Assuming row['date_of_birth'] is a datetime object or a string pandas can parse to datetime
            dob_formatted = pd.to_datetime(row['date_of_birth'], dayfirst=True).strftime("%Y-%m-%d")
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['username'], password, row['name'], row['surname'], row['nationality'],
                                 dob_formatted, row['fide_id'], row['elo_rating'], row['title_id']))

def create_table_titles(df: pd.DataFrame, db_connector):
    table_name = 'Titles'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (title_id INT, title_name TEXT, PRIMARY KEY (title_id));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['title_id'], row['title_name']))

def create_table_player_teams(df: pd.DataFrame, db_connector):
    table_name = 'PlayerTeams'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username VARCHAR(255), team_id INT, PRIMARY KEY (username, team_id), "
                       f"FOREIGN KEY (username) REFERENCES Players(username), FOREIGN KEY (team_id) REFERENCES Teams(team_id));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['username'], row['team_id']))

def create_table_coaches(df: pd.DataFrame, db_connector):
    table_name = 'Coaches'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username VARCHAR(255), password TEXT, name TEXT, surname TEXT, nationality TEXT, "
                       f"team_id INT, contract_start DATE, contract_end DATE, PRIMARY KEY (username), FOREIGN KEY (team_id) REFERENCES Teams(team_id));")

        for _, row in df.iterrows():
            password = hash_password_sha256(str(row["password"])) # Ensure password is a string
            contract_start_formatted = pd.to_datetime(row['contract_start'], dayfirst=True).strftime("%Y-%m-%d")
            contract_end_formatted = pd.to_datetime(row['contract_finish'], dayfirst=True).strftime("%Y-%m-%d") # Changed 'contract_end' to 'contract_finish'
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['username'], password, row['name'], row['surname'], row['nationality'], row['team_id'],
                                 contract_start_formatted, contract_end_formatted))

def create_table_coach_certifications(df: pd.DataFrame, db_connector):
    table_name = 'CoachCertifications'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username VARCHAR(255), certification VARCHAR(255), PRIMARY KEY (username, certification), " # Assuming certification can also be VARCHAR
                       f"FOREIGN KEY (username) REFERENCES Coaches(username));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['coach_username'], row['certification'])) # Changed 'username' to 'coach_username'

def create_table_teams(df: pd.DataFrame, db_connector):
    table_name = 'Teams'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (team_id INT, team_name TEXT, sponsor_id INT, "
                       f"PRIMARY KEY (team_id), FOREIGN KEY (sponsor_id) REFERENCES Sponsors(sponsor_id));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s)"
            cursor.execute(sql, (row['team_id'], row['team_name'], row['sponsor_id']))

def create_table_sponsors(df: pd.DataFrame, db_connector):
    table_name = 'Sponsors'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (sponsor_id INT, sponsor_name TEXT, PRIMARY KEY (sponsor_id));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['sponsor_id'], row['sponsor_name']))

def create_table_arbiters(df: pd.DataFrame, db_connector):
    table_name = 'Arbiters'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username VARCHAR(255), password TEXT, name TEXT, surname TEXT, nationality TEXT,"
                       f"experience_level VARCHAR(50), PRIMARY KEY (username));") # experience_level to VARCHAR

        for _, row in df.iterrows():
            password = hash_password_sha256(str(row["password"])) # Ensure password is a string
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['username'], password, row['name'], row['surname'], row['nationality'], row['experience_level']))

def create_table_arbiters_certifications(df: pd.DataFrame, db_connector):
    table_name = 'ArbiterCertifications'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username VARCHAR(255), certification VARCHAR(255), PRIMARY KEY (username, certification), " # Assuming certification can also be VARCHAR
                       f"FOREIGN KEY (username) REFERENCES Arbiters(username));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['username'], row['certification']))

def create_table_halls(df: pd.DataFrame, db_connector):
    table_name = 'Halls'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (hall_id INT, hall_name TEXT, country TEXT, capacity INT, PRIMARY KEY (hall_id));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (row['hall_id'], row['hall_name'], row['country'], row['capacity']))

def create_table_tables(df: pd.DataFrame, db_connector):
    table_name = 'Tables'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (table_id INT, hall_id INT, "
                       f"PRIMARY KEY (table_id, hall_id), FOREIGN KEY (hall_id) REFERENCES Halls(hall_id));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['table_id'], row['hall_id']))

def create_table_matches(df: pd.DataFrame, db_connector):
    table_name = 'Matches'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (match_id INT, date DATE, time_slot INT, hall_id INT, table_id INT, "
                           f"team1_id INT, team2_id INT, arbiter_username VARCHAR(255), ratings INT, Creator VARCHAR(255),  " # Changed REAL to INT
                           f"PRIMARY KEY (match_id), FOREIGN KEY (table_id, hall_id) REFERENCES Tables(table_id, hall_id), "
                           f"FOREIGN KEY (team1_id) REFERENCES Teams(team_id), FOREIGN KEY (team2_id) REFERENCES Teams(team_id), "
                           f"FOREIGN KEY (arbiter_username) REFERENCES Arbiters(username), FOREIGN KEY (creator) REFERENCES Coaches(username),"
                           f"CHECK (ratings >= 1 AND ratings <= 10));")

        for _, row in df.iterrows():
            match_date_formatted = pd.to_datetime(row['date'], dayfirst=True).strftime("%Y-%m-%d")
            # Ensure rating is int for insertion if it comes as float from Excel
            rating_value = int(row['ratings']) if pd.notna(row['ratings']) else None 
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['match_id'], match_date_formatted, row['time_slot'], row['hall_id'], row['table_id'],
                                 row['team1_id'], row['team2_id'], row['arbiter_username'], rating_value, None))

def create_table_match_assignments(df: pd.DataFrame, db_connector):
    table_name = "MatchAssignments"
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (match_id INT, white_player VARCHAR(255), black_player VARCHAR(255), result ENUM('draw', 'black wins', 'white wins'), " # Added comma, player usernames to VARCHAR
                       f"PRIMARY KEY (match_id), FOREIGN KEY (match_id) REFERENCES Matches(match_id), "
                       f"FOREIGN KEY (white_player) REFERENCES Players(username), FOREIGN KEY (black_player) REFERENCES Players(username));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (row['match_id'], row['white_player'], row['black_player'], row['result']))

# --- Utility to create table and insert data ---
def transfer_excel_to_mysql(filepath):
    xls = pd.ExcelFile(filepath)
    conn = get_mysql_connection()
    print(conn)

    with conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    tables_to_parse_in_order = [
        "DBManagers", "Titles", "Sponsors", "Halls", "Arbiters", 
        "Teams", "Players", "Coaches", 
        "PlayerTeams", "CoachCertifications", "ArbiterCertifications", 
        "Tables", "Matches", "MatchAssignments"
    ] # Revised order for foreign key dependencies
    for name in tables_to_parse_in_order:
        print(f"Processing sheet: {name}...") # Added print statement
        df = xls.parse(name)

        if name == 'DBManagers':
            create_table_dbmanagers(df, conn)
        elif name == 'Players':
            create_table_players(df, conn)
        elif name == 'Titles':
            create_table_titles(df, conn)
        elif name == 'PlayerTeams':
            create_table_player_teams(df, conn)
        elif name == 'Coaches':
            create_table_coaches(df, conn)
        elif name == 'CoachCertifications':
            create_table_coach_certifications(df, conn)
        elif name == 'Teams':
            create_table_teams(df, conn)
        elif name == 'Sponsors':
            create_table_sponsors(df, conn)
        elif name == 'Arbiters':
            create_table_arbiters(df, conn)
        elif name == 'ArbiterCertifications':
            create_table_arbiters_certifications(df, conn)
        elif name == 'Halls':
            create_table_halls(df, conn)
        elif name == 'Tables':
            create_table_tables(df, conn)
        elif name == 'Matches':
            create_table_matches(df, conn)
        elif name == 'MatchAssignments':
            create_table_match_assignments(df, conn)

    conn.commit()
    
    with conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Transfer Excel data to MySQL.")
    parser.add_argument('file', type=str, help="Path to the Excel file")
    args = parser.parse_args()

    filepath = args.file
    try:
        transfer_excel_to_mysql(filepath)
        print(f"Transfer of {filepath} complete.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()


"""
mysql> SHOW TABLES
    -> ;
+-----------------------+
| Tables_in_HW3         |
+-----------------------+
| ArbiterCertifications |
| Arbiters              |
| CoachCertifications   |
| Coaches               |
| DBManagers            |
| Halls                 |
| MatchAssignments      |
| Matches               |
| PlayerTeams           |
| Players               |
| Sponsors              |
| Tables                |
| Teams                 |
| Titles                |
+-----------------------+
14 rows in set (0.00 sec)

"""