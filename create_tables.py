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
DB_PASS = 'password'
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
        cursor.execute(f"CREATE TABLE `{table_name}` (username TEXT, password TEXT, PRIMARY KEY (username));")

        for _, row in df.iterrows():
            password = hash_password_sha256(row["password"])
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['username'], password))

def create_table_players(df: pd.DataFrame, db_connector):
    table_name = 'Players'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username TEXT, password TEXT, name TEXT, surname TEXT, nationality TEXT, date_of_birth DATE, fide_id TEXT, elo_rating INT, title_id INT, "
                       f"PRIMARY KEY (username), FOREIGN KEY (title_id) REFERENCES Titles(title_id));")

        for _, row in df.iterrows():
            password = hash_password_sha256(row["password"])
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['username'], password, row['name'], row['surname'], row['nationality'],
                                 datetime.strftime(row['date_of_birth'], "%D-%M-%Y"), row['fide_id'], row['elo_rating'], row['title_id']))

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
        cursor.execute(f"CREATE TABLE `{table_name}` (username TEXT, team_id INT, PRIMARY KEY (username, team_id), "
                       f"FOREIGN KEY (username) REFERENCES Players(username), FOREIGN KEY (team_id) REFERENCES Teams(team_id));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['username'], row['team_id']))

def create_table_coaches(df: pd.DataFrame, db_connector):
    table_name = 'Coaches'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username TEXT, password TEXT, name TEXT, surname TEXT, nationality TEXT, "
                       f"team_id INT, contract_start DATE, contract_end DATE, PRIMARY KEY (username), FOREIGN KEY (team_id) REFERENCES Teams(team_id));")

        for _, row in df.iterrows():
            password = hash_password_sha256(row["password"])
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['username'], password, row['name'], row['surname'], row['nationality'], row['team_id'],
                                 datetime.strftime(row['contract_start'], "%D-%M-%Y"), datetime.strftime(row['contract_end'], "%D-%M-%Y")))

def create_table_coach_certifications(df: pd.DataFrame, db_connector):
    table_name = 'CoachCertifications'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username TEXT, certification TEXT, PRIMARY KEY (username, certification), "
                       f"FOREIGN KEY (username) REFERENCES Coaches(username);")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s)"
            cursor.execute(sql, (row['username'], row['certification']))

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
        cursor.execute(f"CREATE TABLE `{table_name}` (username TEXT, password TEXT, name TEXT, surname TEXT, nationality TEXT,"
                       f"experience_level TEXT, PRIMARY KEY (username));")

        for _, row in df.iterrows():
            password = hash_password_sha256(row["password"])
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['username'], password, row['name'], row['surname'], row['nationality'], row['experience_level']))

def create_table_arbiters_certifications(df: pd.DataFrame, db_connector):
    table_name = 'ArbiterCertifications'
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (username TEXT, certification TEXT, PRIMARY KEY (username, certification), "
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
                       f"team1_id INT, team2_id INT, arbiter_username TEXT, ratings REAL,"
                       f"PRIMARY KEY (match_id), FOREIGN KEY (table_id, hall_id) REFERENCES Tables(table_id, hall_id), "
                       f"FOREIGN KEY (team1_id) REFERENCES Teams(team_id), FOREIGN KEY (team2_id) REFERENCES Teams(team_id), "
                       f"FOREIGN KEY (arbiter_username) REFERENCES Arbiters(username));")

        for _, row in df.iterrows():
            sql = f"INSERT INTO `{table_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['match_id'], datetime.strftime(row['date'], "%D-%M-%Y"), row['time_slot'], row['hall_id'], row['table_id'],
                                 row['team1_id'], row['team2_id'], row['arbiter_username'], row['ratings']))

def create_table_match_assignments(df: pd.DataFrame, db_connector):
    table_name = "MatchAssignments"
    with db_connector.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` (match_id INT, white_player TEXT, black_player TEXT, result ENUM('draw', 'black wins', 'white wins') "
                       f"PRIMARY KEY (match_id), FOREIGN KEY (match_id) REFERENCES Matches(match_id), "
                       f"FOREIGN KEY (white_player) REFERENCES Players(username), FOREIGN KEY (black_player) REFERENCES Players(username));")

# --- Utility to create table and insert data ---
def transfer_excel_to_mysql(filepath):
    xls = pd.ExcelFile(filepath)
    conn = get_mysql_connection()
    print(conn)
    cursor = conn.cursor()

    tables_to_parse_in_order = ["DBManagers", "Players", "Titles", "Sponsors", "Teams", "PlayerTeams", "Coaches", "CoachCertifications", "Arbiters", "ArbiterCertifications", "Halls", "Tables", "Matches", "MatchAssignments"]
    for name in tables_to_parse_in_order:
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

