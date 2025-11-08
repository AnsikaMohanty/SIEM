import pandas as pd
import mysql.connector
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import numpy as np
import os

# ====== Load CSV ======
# Get the directory where the current script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the CSV file relative to the script location
csv_path = os.path.join(script_dir, "loginlogoffff.csv")

# Read the CSV
df = pd.read_csv(csv_path)

# Standardize column names
df.columns = [col.strip().replace(" ", "_") for col in df.columns]

# Check if required columns exist
required_cols = ["Login_Timestamp", "IP_Address", "ASN", "Login_Successful"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Missing column: {col}")

# Convert timestamp
df["Login_Timestamp"] = pd.to_datetime(df["Login_Timestamp"], errors='coerce')

# Extract hour
df["hour"] = df["Login_Timestamp"].dt.hour

# Convert boolean / categorical to numeric
label_enc = LabelEncoder()
df["IP_Address"] = label_enc.fit_transform(df["IP_Address"].astype(str))
df["ASN"] = label_enc.fit_transform(df["ASN"].astype(str))
df["Login_Successful"] = df["Login_Successful"].astype(int)

# Drop rows with missing values
df.dropna(inplace=True)

# ====== Features for Anomaly Detection ======
features = ["hour", "IP_Address", "ASN", "Login_Successful"]
X = df[features].values

# Adjust contamination: 5% anomalies by default
contamination = min(0.05, max(1 / len(df), 0.05))

# Isolation Forest Model
model = IsolationForest(contamination=contamination, random_state=42)
df["anomaly"] = model.fit_predict(X)

# Map -1 to 1 (anomaly), 1 to 0 (normal)
df["anomaly"] = df["anomaly"].map({-1: 1, 1: 0})

print(f"✅ Anomaly Detection Complete — {df['anomaly'].sum()} anomalies found.")

# ====== Store in MySQL ======
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="rootroot",
        database="siem"
    )
    cursor = conn.cursor()

    # Create table if not exists
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

    # Insert rows
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO login_anomalies (Login_Timestamp, IP_Address, ASN, Login_Successful, hour, anomaly)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            row["Login_Timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
            row["IP_Address"],
            row["ASN"],
            row["Login_Successful"],
            int(row["hour"]),
            int(row["anomaly"])
        ))

    conn.commit()
    print("✅ Data inserted into MySQL successfully.")

except mysql.connector.Error as err:
    print(f"MySQL Error: {err}")

finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
