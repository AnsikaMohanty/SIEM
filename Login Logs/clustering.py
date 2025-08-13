import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt

# Load the dataset
df = pd.read_csv("loginlogoffff.csv")

# Data preprocessing
df['Login Timestamp'] = pd.to_datetime(df['Login Timestamp'])
df['hour'] = df['Login Timestamp'].dt.hour
df['Login Failed'] = df['Login Successful'].apply(lambda x: 0 if x else 1)

# Feature engineering
features_df = df.groupby(['IP Address', 'ASN']).agg(
    total_logins=('Login Timestamp', 'count'),
    failure_percentage=('Login Failed', 'mean'),
    unique_login_hours=('hour', 'nunique')
).reset_index()

# Preprocessing for clustering
# Scale the features
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features_df[['total_logins', 'failure_percentage', 'unique_login_hours']])

# Clustering with DBSCAN
# DBSCAN parameters eps and min_samples need to be tuned.
# For demonstration, we'll use common starting values.
dbscan = DBSCAN(eps=0.5, min_samples=5)
features_df['cluster'] = dbscan.fit_predict(scaled_features)

# Analyze the clusters, including noise points (-1)
cluster_summary = features_df.groupby('cluster')[['total_logins', 'failure_percentage', 'unique_login_hours']].mean()
print("DBSCAN Cluster Summary:\n", cluster_summary)

cluster_counts = features_df['cluster'].value_counts()
print("\nDBSCAN Cluster Counts:\n", cluster_counts)

# Visualize the clusters
fig, ax = plt.subplots(figsize=(10, 6))

scatter = ax.scatter(
    features_df['failure_percentage'],
    features_df['total_logins'],
    c=features_df['cluster'],
    cmap='plasma',
    alpha=0.6,
    s=100
)

ax.set_title('IP/ASN Clusters (DBSCAN)', fontsize=16)
ax.set_xlabel('Failure Percentage', fontsize=12)
ax.set_ylabel('Total Logins', fontsize=12)

# Create a legend
legend1 = ax.legend(*scatter.legend_elements(), title="Cluster", loc='upper left')
ax.add_artist(legend1)

plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()

# Save the plot
plt.savefig('ip_asn_dbscan_clusters.png')