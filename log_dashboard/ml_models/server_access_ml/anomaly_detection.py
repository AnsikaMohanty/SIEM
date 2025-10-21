import pandas as pd
from sklearn.ensemble import IsolationForest
import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import os

# Database credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'

OUTPUT_DIR = os.path.join('static', 'server_outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data_from_mysql():
    """Load server access logs from MySQL."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        query = "SELECT ip, status, url, log_timestamp FROM server_access_logs"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Error as e:
        print("Database Error:", e)
        return pd.DataFrame()

def feature_engineering(df):
    """Prepare aggregated feature dataset by IP."""
    if df.empty:
        return pd.DataFrame()

    df['log_timestamp'] = pd.to_datetime(df['log_timestamp'], errors='coerce')
    df = df.dropna(subset=['ip'])

    # Feature calculations
    df['status'] = pd.to_numeric(df['status'], errors='coerce')
    df['error_flag'] = df['status'].apply(lambda x: 1 if x >= 400 else 0)

    req_count = df.groupby('ip').size().reset_index(name='request_count')
    err_ratio = df.groupby('ip')['error_flag'].mean().reset_index(name='error_ratio')
    uniq_urls = df.groupby('ip')['url'].nunique().reset_index(name='unique_url_count')

    features = req_count.merge(err_ratio, on='ip').merge(uniq_urls, on='ip')
    return features

def detect_anomalies(features):
    """Run IsolationForest anomaly detection and return DataFrame of anomalies."""
    if features.empty:
        return pd.DataFrame()

    model = IsolationForest(contamination=0.05, random_state=42)
    X = features[['request_count', 'error_ratio', 'unique_url_count']]
    features['anomaly'] = model.fit_predict(X)

    # Plot: Request Count vs Error Ratio
    plt.figure(figsize=(6,4))
    plt.scatter(features['request_count'], features['error_ratio'],
                c=features['anomaly'], cmap='coolwarm', s=50)
    plt.xlabel("Request Count")
    plt.ylabel("Error Ratio")
    plt.title("Anomaly Detection: IP Activity")
    plt.tight_layout()

    plot_path = os.path.join(OUTPUT_DIR, 'anomaly_detection_plot.png')
    plt.savefig(plot_path)
    plt.close()

    anomalies = features[features['anomaly'] == -1]
    return anomalies  # ✅ Return DataFrame, not dict
