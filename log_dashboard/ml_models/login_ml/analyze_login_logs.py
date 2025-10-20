# analyze_login_logs.py
import os
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.cluster import DBSCAN
from sklearn.metrics import classification_report, confusion_matrix, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX

plt.switch_backend("Agg")  # Avoid GUI backend errors

# =====================================
# 1. Load Data
# =====================================
def load_data(file_path):
    print("📥 Loading data...")
    df = pd.read_csv(file_path)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df["Login_Timestamp"] = pd.to_datetime(df["Login_Timestamp"], errors="coerce")
    df.dropna(subset=["Login_Timestamp"], inplace=True)
    return df

# =====================================
# 2. Anomaly Detection (IsolationForest)
# =====================================
def run_anomaly_detection(df):
    print("🚨 Running Anomaly Detection...")
    df["hour"] = df["Login_Timestamp"].dt.hour
    le_ip = LabelEncoder()
    le_asn = LabelEncoder()

    df["IP_Address"] = le_ip.fit_transform(df["IP_Address"].astype(str))
    df["ASN"] = le_asn.fit_transform(df["ASN"].astype(str))
    df["Login_Successful"] = df["Login_Successful"].astype(int)

    features = ["hour", "IP_Address", "ASN", "Login_Successful"]
    X = df[features]
    if len(X) < 10:
        print("⚠️ Not enough data for anomaly detection.")
        return df, 0

    model = IsolationForest(contamination=0.05, random_state=42)
    df["anomaly"] = model.fit_predict(X)
    df["anomaly"] = df["anomaly"].map({-1: 1, 1: 0})
    anomalies = int(df["anomaly"].sum())
    print(f"✅ {anomalies} anomalies detected.")
    return df, anomalies

# =====================================
# 3. Binary Classification (RandomForest)
# =====================================
def run_classification(df, output_dir):
    print("🤖 Running Binary Classification...")
    if "anomaly" not in df.columns or df["anomaly"].sum() == 0:
        print("⚠️ No anomalies found — skipping classification.")
        return None

    X = df[["hour", "IP_Address", "ASN"]]
    y = df["anomaly"]

    if len(X) < 10:
        print("⚠️ Not enough samples for training.")
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    report = classification_report(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    print("✅ Classification completed successfully.")
    print(report)

    # Save confusion matrix plot
    plt.figure(figsize=(5, 4))
    plt.imshow(cm, cmap="Blues")
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.colorbar()
    plt.tight_layout()
    cm_path = output_dir / "login_confusion_matrix.png"
    plt.savefig(cm_path)
    plt.close()

    return {"report": report, "matrix": cm_path.name}

# =====================================
# 4. Clustering (DBSCAN)
# =====================================
def run_clustering(df, output_dir):
    print("🔍 Running DBSCAN Clustering...")
    df["hour"] = df["Login_Timestamp"].dt.hour
    df["Login_Failed"] = df["Login_Successful"].apply(lambda x: 0 if x else 1)
    agg_df = df.groupby(["IP_Address", "ASN"]).agg(
        total_logins=("Login_Timestamp", "count"),
        failure_pct=("Login_Failed", "mean"),
        active_hours=("hour", "nunique"),
    ).reset_index()

    scaler = StandardScaler()
    scaled = scaler.fit_transform(agg_df[["total_logins", "failure_pct", "active_hours"]])
    db = DBSCAN(eps=0.5, min_samples=5).fit(scaled)
    agg_df["cluster"] = db.labels_

    plt.figure(figsize=(8, 6))
    plt.scatter(agg_df["failure_pct"], agg_df["total_logins"], c=agg_df["cluster"], cmap="plasma", s=80)
    plt.title("IP/ASN Clusters")
    plt.xlabel("Failure %")
    plt.ylabel("Total Logins")
    plt.tight_layout()
    cluster_path = output_dir / "login_clusters.png"
    plt.savefig(cluster_path)
    plt.close()

    print("✅ Clustering complete.")
    return {"clusters": agg_df["cluster"].nunique(), "plot": cluster_path.name}

# =====================================
# 5. Time-Series (SARIMAX)
# =====================================
def run_time_series(df, output_dir):
    print("📈 Running Time Series Forecasting...")
    hourly = df.groupby(df["Login_Timestamp"].dt.floor("h")).size()
    if len(hourly) < 48:
        print("⚠️ Not enough data for time-series modeling.")
        return None

    train_size = int(len(hourly) * 0.8)
    train, test = hourly[:train_size], hourly[train_size:]

    model = SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 24))
    res = model.fit(disp=False)
    forecast = res.get_forecast(steps=len(test))
    forecast_mean = forecast.predicted_mean

    mae = mean_absolute_error(test, forecast_mean)
    rmse = np.sqrt(mean_squared_error(test, forecast_mean))

    plt.figure(figsize=(10, 4))
    plt.plot(train.index, train, label="Train")
    plt.plot(test.index, test, label="Test", color="orange")
    plt.plot(test.index, forecast_mean, label="Forecast", color="green")
    plt.legend()
    plt.tight_layout()
    ts_path = output_dir / "login_forecast.png"
    plt.savefig(ts_path)
    plt.close()

    print(f"✅ Forecast complete. MAE={mae:.2f}, RMSE={rmse:.2f}")
    return {"mae": mae, "rmse": rmse, "plot": ts_path.name}

# =====================================
# 6. Main Function (Flask entry)
# =====================================
def analyze_login_logs():
    print("🚀 Starting Login Log ML Pipeline...")
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir.parent.parent / "static" / "login_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / "loginlogoffff.csv"
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    df = load_data(file_path)
    df, anomalies = run_anomaly_detection(df)
    classification = run_classification(df, output_dir)
    clustering = run_clustering(df, output_dir)
    ts_results = run_time_series(df, output_dir)

    images = [p.name for p in output_dir.glob("*.png")]

    return {
        "anomalies": anomalies,
        "classification": classification,
        "clustering": clustering,
        "timeseries": ts_results,
    }, images
