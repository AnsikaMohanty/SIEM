import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt

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
        query = "SELECT ip, status, url, log_timestamp, referer, user_agent FROM server_access_logs"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Error as e:
        print("Error:", e)
        return pd.DataFrame()

def label_data(df):
    df['label'] = df['user_agent'].str.contains(
        'bot|crawler|spider|crawl|slurp', case=False, na=False
    ).astype(int)  # 1 = bot, 0 = human
    return df

def feature_engineering(df):
    df['log_timestamp'] = pd.to_datetime(df['log_timestamp'], errors='coerce')
    df['hour'] = df['log_timestamp'].dt.hour
    df['url_length'] = df['url'].astype(str).apply(len)
    df['path_depth'] = df['url'].astype(str).apply(lambda x: x.count('/'))
    df['has_referer'] = df['referer'].apply(lambda x: 0 if x == '-' or pd.isna(x) else 1)
    df['is_error'] = df['status'].apply(lambda x: 1 if int(x) >= 400 else 0)

    agg_df = df.groupby('ip').agg({
        'hour': 'mean',
        'url_length': 'mean',
        'path_depth': 'mean',
        'has_referer': 'mean',
        'is_error': 'mean',
        'label': 'max'
    }).reset_index()

    return agg_df

def train_classifier(features):
    X = features[['hour', 'url_length', 'path_depth', 'has_referer', 'is_error']]
    y = features['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred))

    # Bot-to-human ratio
    bot_ratio = y.value_counts(normalize=True) * 100
    print(f"\n🤖 Bot traffic: {bot_ratio.get(1, 0):.2f}% | 👤 Human traffic: {bot_ratio.get(0, 0):.2f}%")

    # Top bot IPs
    top_bots = features[features['label'] == 1].sort_values(by='url_length', ascending=False).head(10)
    print("\n🏆 Top 10 Bot IPs:")
    print(top_bots[['ip', 'url_length', 'path_depth', 'is_error']])

    # Feature importance
    importance = pd.Series(clf.feature_importances_, index=X.columns)
    importance.sort_values().plot(kind='barh', title="Feature Importance")
    plt.tight_layout()
    plt.show()

    return clf

if __name__ == "__main__":
    df_logs = load_data_from_mysql()
    if df_logs.empty:
        print("No data found in MySQL.")
    else:
        df_logs = label_data(df_logs)
        features = feature_engineering(df_logs)
        model = train_classifier(features)
