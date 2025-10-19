# rdp_ml1.py

import os
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# 1. Load Data
# =========================
def load_data(file_path):
    print("📥 Loading data...")
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    return df

# =========================
# 2. Preprocess
# =========================
def preprocess(df):
    print("⚙️ Preprocessing...")
    df = df.dropna(subset=['status', 'username', 'remote_address'])
    
    # Time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    # Encode categorical
    le_user = LabelEncoder()
    le_ip = LabelEncoder()
    le_status = LabelEncoder()

    df['username_enc'] = le_user.fit_transform(df['username'])
    df['remote_address_enc'] = le_ip.fit_transform(df['remote_address'])
    df['status_enc'] = le_status.fit_transform(df['status'])

    features = ['username_enc', 'remote_address_enc', 'remote_port', 'hour', 'day_of_week']
    X = df[features]
    y = df['status_enc']

    return df, X, y, le_status

# =========================
# 3. Classification
# =========================
def run_classification(X, y, output_dir, label_encoder):
    print("🤖 Running Classification...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=500),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42)
    }

    results = {}
    report_path = output_dir / "classification_report.txt"

    with open(report_path, "w") as f:
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            acc = model.score(X_test, y_test)
            results[name] = acc
            f.write(f"\n==== {name} ====\n")
            f.write(f"Accuracy: {acc:.4f}\n")
            f.write(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
            f.write("\n")

            # Confusion matrix plot
            cm = confusion_matrix(y_test, y_pred)
            plt.figure(figsize=(6,5))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
            plt.title(f"Confusion Matrix ({name})")
            plt.xlabel("Predicted")
            plt.ylabel("True")
            plt.tight_layout()
            cm_path = output_dir / f"confusion_matrix_{name.replace(' ', '_').lower()}.png"
            plt.savefig(cm_path)
            plt.close()

    print(f"✅ Classification results saved to: {report_path}")
    return results

# =========================
# 4. Anomaly Detection
# =========================
def run_anomaly_detection(X):
    print("🚨 Running Anomaly Detection...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    iso = IsolationForest(contamination=0.02, random_state=42)
    anomalies = iso.fit_predict(X_scaled)
    return anomalies

# =========================
# 5. Clustering
# =========================
def run_clustering(X, output_dir):
    print("🔍 Running Clustering...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)

    plt.figure(figsize=(8,6))
    plt.scatter(X_scaled[:, 0], X_scaled[:, 1], c=clusters, cmap='viridis', s=50, alpha=0.7)
    plt.title("KMeans Clustering (first 2 features)")
    plt.xlabel(X.columns[0])
    plt.ylabel(X.columns[1])
    plt.grid(True)
    plt.tight_layout()
    cluster_path = output_dir / "clusters_pca.png"
    plt.savefig(cluster_path)
    plt.close()
    print(f"✅ Cluster plot saved to: {cluster_path}")
    return clusters

# =========================
# 6. Time-Series Trends
# =========================
def run_time_series(df, output_dir):
    print("📈 Running Time-Series Trend Analysis...")
    ts = df.groupby(pd.Grouper(key='timestamp', freq='D')).size()
    plt.figure(figsize=(10,5))
    ts.plot(title="Sessions per Day")
    plt.xlabel("Date")
    plt.ylabel("Session Count")
    plt.grid(True)
    plt.tight_layout()
    ts_path = output_dir / "sessions_per_day.png"
    plt.savefig(ts_path)
    plt.close()
    print(f"✅ Time-series plot saved to: {ts_path}")

# =========================
# 7. User Behavior Profiling
# =========================
def run_user_behavior(df):
    print("👤 Running User Behavior Profiling...")
    user_stats = df.groupby('username').agg({
        'session_id': 'count',
        'remote_address': pd.Series.nunique,
        'hour': lambda x: x.mode()[0] if not x.mode().empty else np.nan
    }).rename(columns={
        'session_id': 'total_sessions',
        'remote_address': 'unique_ips',
        'hour': 'most_common_hour'
    })
    return user_stats

# =========================
# 8. Main function for Flask
# =========================
def analyze_rdp_logs():
    print("🚀 Starting RDP Log Analysis Pipeline...")

    # Save outputs in static folder
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir.parent.parent / "static" / "rdp_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / "rdp_dataset.csv"
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    df = load_data(file_path)
    df, X, y, label_encoder = preprocess(df)

    classification_results = run_classification(X, y, output_dir, label_encoder)
    anomalies = run_anomaly_detection(X)
    clusters = run_clustering(X, output_dir)
    df['anomaly'] = anomalies
    df['cluster'] = clusters

    run_time_series(df, output_dir)
    user_stats = run_user_behavior(df)

    df.to_csv(output_dir / "rdp_analysis_output.csv", index=False)
    user_stats.to_csv(output_dir / "user_behavior.csv")

    # Get list of image filenames
    images = [p.name for p in output_dir.glob("*.png")]

    return classification_results, user_stats.reset_index(), images
