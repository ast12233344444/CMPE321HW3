from flask import Flask, request
import pandas as pd
import pymysql
import argparse
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

# --- Utility to create table and insert data ---
def transfer_excel_to_mysql(filepath):
    xls = pd.ExcelFile(filepath)
    conn = get_mysql_connection()
    print(conn)
    cursor = conn.cursor()

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        table_name = sheet_name.strip().replace(' ', '_')  # sanitize

        # Drop and create table
        cols = ", ".join(f"`{col}` TEXT" for col in df.columns)
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute(f"CREATE TABLE `{table_name}` ({cols});")

        # Insert data row-by-row
        for _, row in df.iterrows():
            placeholders = ", ".join(["%s"] * len(row))
            sql = f"INSERT INTO `{table_name}` VALUES ({placeholders})"
            cursor.execute(sql, tuple(str(v) if pd.notna(v) else None for v in row))

    conn.commit()
    cursor.close()
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

