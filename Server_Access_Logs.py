import re
import pandas as pd
import mysql.connector
from mysql.connector import Error

# 🔧 Hardcoded MySQL credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'      # <-- Replace with your MySQL username
MYSQL_PASSWORD = 'rootroot'  # <-- Replace with your MySQL password
MYSQL_DATABASE = 'siem'

def group_log_data(log_entry):
    log_pattern = r'\b(?P<ip>(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}\.){3}(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}))\b - - \[(?P<date>\d{1,2}\/([A-Za-z]{3})\/(\d{4}):.*?)\] "(?P<method>GET|POST)\s'
    match = re.match(log_pattern, log_entry)
    if match:
        return (match.group('ip'), match.group('date'), match.group('method'))
    else:
        return None

def process_log_file(log_file_path):
    with open(log_file_path, 'r') as file:
        log_entries = file.readlines()
    processed_data = [group_log_data(entry) for entry in log_entries if group_log_data(entry)]
    return pd.DataFrame(processed_data, columns=['IP', 'Date', 'Method'])

def create_database_and_table():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        print(f"Database '{MYSQL_DATABASE}' checked/created successfully.")

        # Connect to the new database and create table
        conn.database = MYSQL_DATABASE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS server_access_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(45),
                date VARCHAR(100),
                method VARCHAR(10)
            )
        """)
        print("Table 'server_access_logs' checked/created successfully.")
        conn.commit()
    except Error as e:
        print("Error while setting up database or table:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def insert_data_into_db(df):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        if conn.is_connected():
            print("Connected to MySQL database for data insertion.")
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO server_access_logs (ip, date, method) VALUES (%s, %s, %s)
                ''', (row['IP'], row['Date'], row['Method']))
            conn.commit()
            print("Data inserted successfully.")
    except Error as e:
        print("Error inserting data into MySQL:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def main():
    log_file_path = input("Enter the path to the log file: ")
    create_database_and_table()  # Ensure DB and table exist before processing
    grouped_data = process_log_file(log_file_path)
    if grouped_data.empty:
        print("No valid log entries found.")
    else:
        insert_data_into_db(grouped_data)

if __name__ == "__main__":
    main()
