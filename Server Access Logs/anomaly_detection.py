import pandas as pd
from sklearn.ensemble import IsolationForest
import mysql.connector
from mysql.connector import Error

# MySQL credentials
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'

def load_data_from_mysql():
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
        print("Error:", e)
        return pd.DataFrame()

def feature_engineering(df):
    # Convert timestamp to datetime
    df['log_timestamp'] = pd.to_datetime(df['log_timestamp'], errors='coerce')

    # Requests per IP
    requests_per_ip = df.groupby('ip').size().reset_index(name='request_count')

    # Error ratio (4xx, 5xx)
    df['error_flag'] = df['status'].apply(lambda x: 1 if int(x) >= 400 else 0)
    error_ratio = df.groupby('ip')['error_flag'].mean().reset_index(name='error_ratio')

    # Unique URLs accessed
    unique_urls = df.groupby('ip')['url'].nunique().reset_index(name='unique_url_count')

    # Merge features
    features = requests_per_ip.merge(error_ratio, on='ip').merge(unique_urls, on='ip')
    return features

def detect_anomalies(features):
    model = IsolationForest(contamination=0.05, random_state=42)
    features_for_model = features[['request_count', 'error_ratio', 'unique_url_count']]
    features['anomaly'] = model.fit_predict(features_for_model)
    anomalies = features[features['anomaly'] == -1]
    return anomalies

if __name__ == "__main__":
    df_logs = load_data_from_mysql()
    if df_logs.empty:
        print("No data found in MySQL.")
    else:
        features = feature_engineering(df_logs)
        anomalies = detect_anomalies(features)
        print("\n🚨 Detected Anomalous IPs:")
        print(anomalies[['ip', 'request_count', 'error_ratio', 'unique_url_count']])
