import socket  #It extracts network information
import mysql.connector
from mysql.connector import errorcode #to handle specific mysql errors
from datetime import datetime
import xml.etree.ElementTree as  ET #Certain window logs include xml format
import win32evtlog
import win32com.shell.shell as shell

# MySQL connection
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'          
MYSQL_PASSWORD = 'rootroot'
MYSQL_DB = 'siem'      

# System info
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Check for admin
def is_admin():
    return shell.IsUserAnAdmin()

if not is_admin():
    print(" Please run as Administrator.")
    exit(1)

# Event IDs to search
event_ids = {4624: "Logon", 4634: "Logoff", 4647: "Logoff"}
server = 'localhost'
log_type = 'Security'
flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

def create_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS log_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        log_type VARCHAR(50),
        check_time DATETIME,
        hostname VARCHAR(255),
        ip_address VARCHAR(50),
        username VARCHAR(255),
        event_timestamp DATETIME,
        status VARCHAR(50)
    )
    """
    cursor.execute(create_table_query)

def main():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()
        create_table(cursor)
        conn.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print(" Something is wrong with your username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(" Database does not exist")
        else:
            print(f" MySQL connection error: {err}")
        return
    
    results = []
    skipped = 0

    try:
        hand = win32evtlog.OpenEventLog(server, log_type)
        total = 0
        while total < 100:
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            if not events:
                break
            for event in events:
                if event.EventID not in event_ids:
                    continue
                total += 1
                if total > 50:
                    break

                username = ""
                try:
                    if event.StringInserts and len(event.StringInserts) > 0:
                        # Sometimes the data is inside xml in last StringInsert
                        xml_data = event.StringInserts[-1]
                        try:
                            xml = ET.fromstring(xml_data)
                            for data in xml.findall(".//Data[@Name='TargetUserName']"):
                                if data.text:
                                    username = data.text
                                    break
                        except ET.ParseError:
                            pass
                    if not username and event.StringInserts and len(event.StringInserts) >= 6:
                        username = event.StringInserts[5]
                except Exception:
                    pass

                if not username or username.startswith(("SYSTEM", "DWM-", "UMFD-", "Unknown")):
                    skipped += 1
                    continue
                
                timestamp = event.TimeGenerated.Format()  # e.g. "Mon Feb 21 10:30:40 2022"
                try:
                    event_time = datetime.strptime(timestamp, "%a %b %d %H:%M:%S %Y")
                except Exception:
                    event_time = None

                status = event_ids.get(event.EventID, "Unknown")

                if event_time:
                    results.append((
                        "LOG_DATA",
                        check_time,
                        hostname,
                        ip_address,
                        username,
                        event_time.strftime("%Y-%m-%d %H:%M:%S"),
                        status
                    ))
        print(f" Extracted {len(results)} entries. Skipped {skipped}.")
    except Exception as e:
        print(f" Error reading events: {e}")
        return

    if results:
        try:
            insert_query = """
            INSERT INTO log_data (log_type, check_time, hostname, ip_address, username, event_timestamp, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_query, results)
            conn.commit()
            print(f" Inserted {len(results)} rows into the database.")
        except mysql.connector.Error as err:
            print(f" Error inserting into database: {err}")
    else:
        print(f" No valid entries to insert. Skipped: {skipped}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()

