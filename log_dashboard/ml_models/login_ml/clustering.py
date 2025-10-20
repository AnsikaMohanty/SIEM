import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "loginlogoffff.csv")

if not os.path.exists(csv_path):
    print(f"❌ CSV file not found: {csv_path}")
    raise SystemExit(0)


df = pd.read_csv(csv_path)
df.columns = [col.strip().replace(" ", "_") for col in df.columns]

if "Login_Timestamp" not in df.columns or "Login_Successful" not in df.columns:
    print("❌ Missing required columns.")
    raise SystemExit(0)

df["Login_Timestamp"] = pd.to_datetime(df["Login_Timestamp"])
df["hour"] = df["Login_Timestamp"].dt.hour
df["Login_Failed"] = df["Login_Successful"].apply(lambda x: 0 if x else 1)

features_df = df.groupby(["IP_Address", "ASN"]).agg(
    total_logins=("Login_Timestamp", "count"),
    failure_percentage=("Login_Failed", "mean"),
    unique_login_hours=("hour", "nunique")
).reset_index()

scaler = StandardScaler()
scaled = scaler.fit_transform(features_df[["total_logins", "failure_percentage", "unique_login_hours"]])

dbscan = DBSCAN(eps=0.5, min_samples=5)
features_df["cluster"] = dbscan.fit_predict(scaled)

summary = features_df.groupby("cluster")[["total_logins", "failure_percentage", "unique_login_hours"]].mean()
print("\n📊 DBSCAN Cluster Summary:\n", summary)

plt.figure(figsize=(8,6))
plt.scatter(features_df["failure_percentage"], features_df["total_logins"], c=features_df["cluster"], cmap="plasma", s=80, alpha=0.7)
plt.title("IP/ASN Clusters (DBSCAN)")
plt.xlabel("Failure %")
plt.ylabel("Total Logins")
plt.grid(True, alpha=0.3)

output_path = os.path.join(base_dir, "ip_asn_dbscan_clusters.png")
plt.tight_layout()
plt.savefig(output_path)
print(f"✅ Cluster plot saved at: {output_path}")
