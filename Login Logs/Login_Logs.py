import pandas as pd
import mysql.connector
from mysql.connector import Error
import os

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

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        print(f"✅ Database '{MYSQL_DATABASE}' ready.")

        conn.database = MYSQL_DATABASE

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
    conn = None
    try:
        if not os.path.isfile(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()

        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()

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

    except FileNotFoundError as fnf:
        print("❌ CSV file not found:", fnf)
    except Exception as e:
        print("❌ Data insertion error:", e)
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    #csv_file_path = r"C:\Users\MY PC\Desktop\SIEM\SIEM\Login Logs\loginlogoffff.csv"
    # Get the directory of the current Python file
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the CSV file (in the same folder)
    csv_file_path = os.path.join(base_dir, "loginlogoffff.csv")
    create_database_and_table()
    insert_csv_to_db(csv_file_path)
