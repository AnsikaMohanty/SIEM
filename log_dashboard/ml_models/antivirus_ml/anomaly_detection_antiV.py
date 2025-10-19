import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import IsolationForest
import os

OUTPUT_FOLDER = "static/antivirus_outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def fetch_data():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="rootroot",
        database="siem"
    )
    query = "SELECT file_path, timestamp, malware_type, severity, scan_type, os, detection_method FROM antivirus_logs"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def run_anomaly_detection():
    df = fetch_data()
    df_clean = df.drop(columns=["file_path", "timestamp"])
    categorical_cols = df_clean.select_dtypes(include=["object"]).columns.tolist()
    
    encoder = OneHotEncoder(handle_unknown="ignore")
    encoded = encoder.fit_transform(df_clean[categorical_cols])
    df_encoded = pd.DataFrame(encoded.toarray(), columns=encoder.get_feature_names_out(categorical_cols))

    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    anomaly_labels = iso_forest.fit_predict(df_encoded)
    
    df["Anomaly_Flag"] = anomaly_labels
    df["Anomaly_Flag"] = df["Anomaly_Flag"].map({1: "Normal", -1: "Anomaly"})
    
    # Plot distribution
    plt.figure(figsize=(6,4))
    sns.countplot(x="Anomaly_Flag", data=df)
    plt.title("Anomaly Distribution")
    anomaly_plot = "anomaly_distribution.png"
    plt.savefig(os.path.join(OUTPUT_FOLDER, anomaly_plot))
    plt.close()
    
    # Sample anomalies
    sample = df[df["Anomaly_Flag"]=="Anomaly"].head(5)
    
    return {
        "counts": df["Anomaly_Flag"].value_counts().to_dict(),
        "sample": sample.to_dict(orient="records"),
        "images": [anomaly_plot]
    }
