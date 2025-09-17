import pandas as pd
import mysql.connector
from mysql.connector import Error
import os

# 🔧 MySQL Credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'
TABLE_NAME = 'antivirus_logs'

def create_database_and_table():
    conn = None  # Initialize conn to None
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        print(f"Database '{MYSQL_DATABASE}' ready.")

        # Switch to database
        conn.database = MYSQL_DATABASE

        # Create table if not exists
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                log_id VARCHAR(100),
                timestamp VARCHAR(100),
                file_path TEXT,
                malware_type VARCHAR(100),
                severity VARCHAR(50),
                scan_type VARCHAR(100),
                os VARCHAR(50),
                detection_method VARCHAR(100)
            )
        """)
        print(f"Table '{TABLE_NAME}' ready.")
        conn.commit()

    except Error as e:
        print("Database/Table creation error:", e)
    finally:
        if conn is not None and conn.is_connected(): # Check if conn is not None
            cursor.close()
            conn.close()

def insert_csv_to_db(csv_path):
    conn = None # Initialize conn to None
    try:
        # Read CSV
        df = pd.read_csv(csv_path)

        # Clean column names
        df.columns = df.columns.str.strip()

        # Connect to DB
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()

        # Insert rows
        for _, row in df.iterrows():
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME}
                (log_id, timestamp, file_path, malware_type, severity, scan_type, os, detection_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(row['log_id']),
                str(row['timestamp']),
                str(row['file_path']),
                str(row['malware_type']),
                str(row['severity']),
                str(row['scan_type']),
                str(row['os']),
                str(row['detection_method'])
            ))

        conn.commit()
        print(f"Inserted {len(df)} rows into '{TABLE_NAME}'.")

    except Error as e:
        print("Data insertion error:", e)
    finally:
        if conn is not None and conn.is_connected(): # Check if conn is not None
            cursor.close()
            conn.close()

if __name__ == "__main__":
    csv_file_path = os.path.abspath("antivirus_logs.csv")

    create_database_and_table()
    insert_csv_to_db(csv_file_path)