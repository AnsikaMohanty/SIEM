import re
import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
import unicodedata
from tkinter import Tk, filedialog

# 🔧 MySQL Credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'

def group_log_data(log_entry):
    log_pattern = r'\b(?P<ip>(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}\.){3}(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2}))\b - - \[(?P<date>\d{1,2}\/([A-Za-z]{3})\/(\d{4}):.*?)\] "(?P<method>GET|POST)\s'
    match = re.match(log_pattern, log_entry)
    if match:
        return (match.group('ip'), match.group('date'), match.group('method'))
    else:
        return None

def process_log_file(log_file_path):
    if not os.path.isfile(log_file_path):
        print(f"❌ File does not exist: {log_file_path}")
        return pd.DataFrame()

    _, ext = os.path.splitext(log_file_path)
    ext = ext.lower()
    log_entries = []

    try:
        if ext == '.csv':
            df = pd.read_csv(log_file_path, header=None)
            log_entries = df.iloc[:, 0].astype(str).tolist()

        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(log_file_path, header=None)
            log_entries = df.iloc[:, 0].astype(str).tolist()

        else:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                log_entries = file.readlines()

    except Exception as e:
        print(f"⚠️ Error reading the file: {e}")
        return pd.DataFrame()

    # Extract valid log lines
    processed_data = []
    for entry in log_entries:
        result = group_log_data(entry.strip())
        if result:
            processed_data.append(result)

    if not processed_data:
        print("⚠️ No valid log entries matched the expected format.")
    return pd.DataFrame(processed_data, columns=['IP', 'Date', 'Method'])

def create_database_and_table():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        print(f"✅ Database '{MYSQL_DATABASE}' checked/created successfully.")

        conn.database = MYSQL_DATABASE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS server_access_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(45),
                date VARCHAR(100),
                method VARCHAR(10)
            )
        """)
        print("✅ Table 'server_access_logs' checked/created successfully.")
        conn.commit()
    except Error as e:
        print("❌ Error while setting up database or table:", e)
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
            print("✅ Connected to MySQL database for data insertion.")
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO server_access_logs (ip, date, method)
                    VALUES (%s, %s, %s)
                ''', (row['IP'], row['Date'], row['Method']))
            conn.commit()
            print("✅ Data inserted successfully.")
    except Error as e:
        print("❌ Error inserting data into MySQL:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def select_file_dialog():
    Tk().withdraw()  # Hide the GUI root
    file_path = filedialog.askopenfilename(
        title="Select a Log File",
        filetypes=[
            ("All supported files", "*.txt *.csv *.log *.xls *.xlsx"),
            ("Text files", "*.txt"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xls *.xlsx"),
            ("Log files", "*.log"),
            ("All files", "*.*")
        ]
    )
    return unicodedata.normalize("NFKD", file_path.strip())

def main():
    print("📂 Please choose a log file...")
    log_file_path = select_file_dialog()

    if not log_file_path:
        print("❌ No file selected. Exiting.")
        return

    create_database_and_table()
    grouped_data = process_log_file(log_file_path)
    if grouped_data.empty:
        print("❌ No valid log entries found.")
    else:
        insert_data_into_db(grouped_data)

if __name__ == "__main__":
    main()
