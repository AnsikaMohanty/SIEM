import os
import pandas as pd
import mysql.connector
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# ====== Setup Paths ======
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "loginlogoffff.csv")

if not os.path.exists(csv_path):
    print(f"CSV file not found at: {csv_path}")
    exit()

# ====== Load CSV ======
df = pd.read_csv(csv_path)
df.columns = [col.strip().replace(" ", "_") for col in df.columns]

required_cols = ["Login_Timestamp", "IP_Address", "ASN", "Login_Successful"]
for col in required_cols:
    if col not in df.columns:
        print(f"Missing column: {col}")
        raise SystemExit(0)

# ====== Preprocessing ======
df["Login_Timestamp"] = pd.to_datetime(df["Login_Timestamp"], errors='coerce')
df["hour"] = df["Login_Timestamp"].dt.hour

le_ip = LabelEncoder()
le_asn = LabelEncoder()

df["IP_Address"] = le_ip.fit_transform(df["IP_Address"].astype(str))
df["ASN"] = le_asn.fit_transform(df["ASN"].astype(str))
df["Login_Successful"] = df["Login_Successful"].astype(int)
df.dropna(inplace=True)

# ====== Isolation Forest ======
features = ["hour", "IP_Address", "ASN", "Login_Successful"]
X = df[features]

if len(X) < 10:
    print(" Not enough records for anomaly detection.")
    raise SystemExit(0)

model = IsolationForest(contamination=0.05, random_state=42)
df["anomaly"] = model.fit_predict(X)
df["anomaly"] = df["anomaly"].map({-1: 1, 1: 0})

print(f"✅ Anomaly Detection Complete — {df['anomaly'].sum()} anomalies found.")

# ====== MySQL Insert ======
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="rootroot",
        database="siem"
    )
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_anomalies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Login_Timestamp DATETIME,
            IP_Address INT,
            ASN INT,
            Login_Successful BOOLEAN,
            hour INT,
            anomaly INT
        )
    """)

    cursor.execute("TRUNCATE TABLE login_anomalies")

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO login_anomalies (Login_Timestamp, IP_Address, ASN, Login_Successful, hour, anomaly)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            row["Login_Timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
            int(row["IP_Address"]),
            int(row["ASN"]),
            int(row["Login_Successful"]),
            int(row["hour"]),
            int(row["anomaly"])
        ))

    conn.commit()
    print(" Data inserted into MySQL successfully.")

except mysql.connector.Error as err:
    print(f" MySQL Error: {err}")

finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
