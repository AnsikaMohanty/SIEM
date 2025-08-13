import pandas as pd
import mysql.connector
from mysql.connector import Error
import os

# 🔧 MySQL Credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'
TABLE_NAME = 'login_log_data'

def create_database_and_table():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        print(f"✅ Database '{MYSQL_DATABASE}' ready.")

        # Switch to database
        conn.database = MYSQL_DATABASE

        # Create table if not exists
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                login_timestamp VARCHAR(100),
                ip_address VARCHAR(45),
                asn VARCHAR(50),
                login_successful BOOLEAN
            )
        """)
        print(f"✅ Table '{TABLE_NAME}' ready.")
        conn.commit()

    except Error as e:
        print("❌ Database/Table creation error:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def insert_csv_to_db(csv_path):
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
                (login_timestamp, ip_address, asn, login_successful)
                VALUES (%s, %s, %s, %s)
            """, (
                str(row['Login Timestamp']),
                str(row['IP Address']),
                str(row['ASN']),
                bool(row['Login Successful'])
            ))

        conn.commit()
        print(f"✅ Inserted {len(df)} rows into '{TABLE_NAME}'.")

    except Error as e:
        print("❌ Data insertion error:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    # Change this to your CSV file path
    csv_file_path = os.path.abspath("loginlogoffff.csv")

    create_database_and_table()
    insert_csv_to_db(csv_file_path)
