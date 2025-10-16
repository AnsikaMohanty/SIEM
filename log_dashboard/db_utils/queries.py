import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "rootroot",
    "database": "siem"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def fetch_logs(table_name, limit=50, offset=0, search=""):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM {table_name}"
        if search:
            # Search all text columns
            query += " WHERE CONCAT_WS(' ', " \
                     "id, log_timestamp, ip, username, session_id, remote_address, method, url, status, size, file_path, malware_type, severity, scan_type) " \
                     f"LIKE '%{search}%'"
        query += f" LIMIT {limit} OFFSET {offset}"
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def fetch_summary(table_name, column_name):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT {column_name}, COUNT(*) as count FROM {table_name} GROUP BY {column_name}"
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def fetch_count(table_name):
    """
    Returns total number of rows in a table
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0] or 0
    except Error as e:
        print(f"Error fetching count from {table_name}: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()
