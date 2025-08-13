import re
import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
import unicodedata

# 🔧 MySQL Credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'

# 📌 Apache Combined Log Format with STRICT IP Regex
log_pattern = re.compile(
    r'(?P<ip>(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.'
    r'(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.'
    r'(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.'
    r'(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})) - - '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH|TRACE|CONNECT) (?P<url>\S+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\d+|-) '
    r'"(?P<referer>[^"]*)" '
    r'"(?P<user_agent>[^"]*)"'
)

def group_log_data(log_entry):
    match = log_pattern.match(log_entry)
    if match:
        data = match.groupdict()
        data['size'] = int(data['size']) if data['size'].isdigit() else 0
        return (
            data['ip'], data['timestamp'], data['method'], data['url'],
            data['status'], data['size'], data['referer'], data['user_agent']
        )
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

    processed_data = []
    for entry in log_entries:
        result = group_log_data(entry.strip())
        if result:
            processed_data.append(result)

    if not processed_data:
        print("No valid log entries matched the expected format.")
        return pd.DataFrame()

    return pd.DataFrame(processed_data, columns=[
        'IP', 'LogTimestamp', 'Method', 'URL', 'Status', 'Size', 'Referer', 'UserAgent'
    ])

def create_database_and_table():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        print(f"Database '{MYSQL_DATABASE}' checked/created successfully.")

        conn.database = MYSQL_DATABASE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS server_access_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(45),
                log_timestamp VARCHAR(100),
                method VARCHAR(10),
                url TEXT,
                status INT,
                size INT,
                referer TEXT,
                user_agent TEXT
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
                    INSERT INTO server_access_logs
                    (ip, log_timestamp, method, url, status, size, referer, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    row['IP'], row['LogTimestamp'], row['Method'], row['URL'],
                    int(row['Status']), int(row['Size']), row['Referer'], row['UserAgent']
                ))
            conn.commit()
            print("Data inserted successfully.")
    except Error as e:
        print("Error inserting data into MySQL:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def main():
    # Direct path to Logs.txt in the same folder as this script
    log_file_path = os.path.join(os.path.dirname(__file__), "Logs.txt")

    if not os.path.exists(log_file_path):
        print(f"Log file not found at: {log_file_path}")
        return

    create_database_and_table()
    grouped_data = process_log_file(log_file_path)
    if grouped_data.empty:
        print("No valid log entries found.")
    else:
        insert_data_into_db(grouped_data)

if __name__ == "__main__":
    main()
