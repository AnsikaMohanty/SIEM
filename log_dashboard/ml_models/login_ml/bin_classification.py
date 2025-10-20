import os
import pandas as pd
import mysql.connector
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

print("=== Binary Classification on Login Anomalies ===")

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="rootroot",
        database="siem"
    )
    query = "SELECT Login_Timestamp, IP_Address, ASN, Login_Successful, hour, anomaly FROM login_anomalies"
    df = pd.read_sql(query, conn)
    conn.close()
except Exception as e:
    print(f"❌ Database read error: {e}")
    raise SystemExit(0)


if df.empty:
    print("⚠️ No data available in login_anomalies. Run anomaly detection first.")
    raise SystemExit(0)


X = df[["hour", "IP_Address", "ASN"]]
y = df["anomaly"]

if len(X) < 10:
    print("⚠️ Not enough samples for training.")
    raise SystemExit(0)


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

print("\n🔍 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("✅ Binary classification completed successfully.")
