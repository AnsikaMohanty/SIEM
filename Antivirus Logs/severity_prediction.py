import pandas as pd
import mysql.connector
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report

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

df = fetch_data()
df_clean = df.drop(columns=["file_path", "timestamp"])

categorical_cols = df_clean.select_dtypes(include=["object"]).columns.tolist()
numerical_cols = df_clean.select_dtypes(include=["int64", "float64"]).columns.tolist()

encoder = OneHotEncoder(handle_unknown="ignore")
encoded = encoder.fit_transform(df_clean[categorical_cols])
encoded_df = pd.DataFrame(encoded.toarray(), columns=encoder.get_feature_names_out(categorical_cols))

df_encoded = pd.concat([encoded_df, df_clean[numerical_cols].reset_index(drop=True)], axis=1)

# Features & target
X = df_encoded.drop(columns=[col for col in df_encoded.columns if col.startswith("severity_")])
y = df["severity"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

dt_model = DecisionTreeClassifier(random_state=42)
dt_model.fit(X_train, y_train)
y_pred = dt_model.predict(X_test)

print("\n=== Severity Prediction ===")
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))
