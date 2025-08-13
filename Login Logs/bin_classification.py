import pandas as pd
import mysql.connector
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# ====== MySQL Connection ======
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="rootroot",
    database="siem"
)

# ====== Load data from MySQL ======
query = "SELECT Login_Timestamp, IP_Address, ASN, Login_Successful, hour, anomaly FROM login_anomalies"
df = pd.read_sql(query, conn)

# Close connection
conn.close()

# ====== Prepare features & target ======
# Corrected code snippet
X = df[["hour", "IP_Address", "ASN"]]
y = df["anomaly"]

# The rest of your code remains the same
# ====== Train-test split ======
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ====== Model training ======
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# ====== Predictions ======
y_pred = clf.predict(X_test)

# ====== Evaluation ======
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

print("\n🔍 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))
