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
        print(f"File does not exist: {log_file_path}")
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
        print(f"Error reading the file: {e}")
        return pd.DataFrame()

    # Extract valid log lines
    processed_data = []
    for entry in log_entries:
        result = group_log_data(entry.strip())
        if result:
            processed_data.append(result)

    if not processed_data:
        print("No valid log entries matched the expected format.")
    return pd.DataFrame(processed_data, columns=['IP', 'Date', 'Method'])

def create_database_and_table():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='rootroot'
        )
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS siem")
        print("Database 'siem' checked/created successfully.")
        
        # Use the database
        cursor.execute("USE siem")
        
        # Create server access logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS server_access_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(45),
                date VARCHAR(255),
                method VARCHAR(10),
                url VARCHAR(255),
                status INT,
                user_agent TEXT
            )
        """)
        print("Table 'server_access_logs' checked/created successfully.")

        # Create login logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                hostname VARCHAR(255),
                event_type ENUM('login', 'logoff') NOT NULL,
                event_time DATETIME NOT NULL,
                source_ip VARCHAR(45),
                session_id VARCHAR(100),
                success BOOLEAN DEFAULT TRUE,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'login_logs' checked/created successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def insert_data_into_db(df):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='rootroot',
            database='siem'
        )
        cursor = conn.cursor()
        
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO server_access_logs (ip, date, method, url, status, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (row['ip'], row['date'], row['method'], row['url'], row['status'], row['user_agent']))
        
        conn.commit()
        print("Data inserted successfully")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def insert_login_event(username, hostname, event_type, source_ip, success=True, details=None):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='rootroot',
            database='siem'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO login_logs (username, hostname, event_type, event_time, source_ip, success, details)
            VALUES (%s, %s, %s, NOW(), %s, %s, %s)
        """, (username, hostname, event_type, source_ip, success, details))
        
        conn.commit()
        print(f"Login event logged: {username} {event_type} from {hostname}")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def process_login_log_file(file_path):
    """Process a login log file and extract relevant information"""
    try:
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            insert_login_event(
                username=row['username'],
                hostname=row['hostname'],
                event_type=row['event_type'],
                source_ip=row['source_ip'],
                success=row['success'],
                details=row.get('details', None)
            )
        return True
    except Exception as e:
        print(f"Error processing login log file: {e}")
        return False

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
    print("Please choose a log file...")
    log_file_path = select_file_dialog()

    if not log_file_path:
        print("No file selected. Exiting.")
        return

    create_database_and_table()
    grouped_data = process_log_file(log_file_path)
    if grouped_data.empty:
        print("No valid log entries found.")
    else:
        insert_data_into_db(grouped_data)

if __name__ == "__main__":
    main()
