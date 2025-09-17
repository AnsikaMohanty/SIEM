import pandas as pd
import mysql.connector
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import IsolationForest

def fetch_data():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",                # 🔹 your MySQL username
        password="rootroot",   # 🔹 your MySQL password
        database="siem"
    )
    query = "SELECT file_path, timestamp, malware_type, severity, scan_type, os, detection_method FROM antivirus_logs"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = fetch_data()

# Drop unused
df_clean = df.drop(columns=["file_path", "timestamp"])

# Encode categorical
categorical_cols = df_clean.select_dtypes(include=["object"]).columns.tolist()
encoder = OneHotEncoder(handle_unknown="ignore")
encoded = encoder.fit_transform(df_clean[categorical_cols])
encoded_df = pd.DataFrame(encoded.toarray(), columns=encoder.get_feature_names_out(categorical_cols))

df_encoded = encoded_df.reset_index(drop=True)

# Anomaly detection
iso_forest = IsolationForest(contamination=0.05, random_state=42)
anomaly_labels = iso_forest.fit_predict(df_encoded)

df["Anomaly_Flag"] = anomaly_labels
df["Anomaly_Flag"] = df["Anomaly_Flag"].map({1: "Normal", -1: "Anomaly"})

print("\n=== Anomaly Detection ===")
print(df["Anomaly_Flag"].value_counts())
print("\nSample anomalies:")
print(df[df["Anomaly_Flag"] == "Anomaly"].head())
