import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import os
import seaborn as sns

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'

OUTPUT_DIR = os.path.join('static', 'server_outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data():
    """Load server access logs from MySQL."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        query = "SELECT ip, status, method, url, size, referer, user_agent FROM server_access_logs"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Error as e:
        print("MySQL Error:", e)
        return pd.DataFrame()

def label_data(df):
    """Label requests as bot or human based on User-Agent."""
    df['label'] = df['user_agent'].str.contains(
        'bot|crawler|spider|crawl|slurp', case=False, na=False
    ).astype(int)
    return df

def feature_engineering(df):
    """Extract numeric behavioral features."""
    df['url_length'] = df['url'].astype(str).apply(len)
    df['path_depth'] = df['url'].astype(str).apply(lambda x: x.count('/'))
    df['is_error'] = df['status'].apply(lambda x: 1 if int(x) >= 400 else 0)
    df['has_referer'] = df['referer'].apply(lambda x: 0 if x == '-' or pd.isna(x) else 1)

    agg = df.groupby('ip').agg({
        'url_length': 'mean',
        'path_depth': 'mean',
        'is_error': 'mean',
        'has_referer': 'mean',
        'label': 'max'
    }).reset_index()

    return agg

def train_classifier(features):
    """Train a RandomForest model and output metrics."""
    X = features[['url_length', 'path_depth', 'is_error', 'has_referer']]
    y = features['label']

    if len(X) < 10 or y.nunique() < 2:
        return {"metrics": {}, "plot": None}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)

    # Plot confusion matrix
    plt.figure(figsize=(4, 3))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Human', 'Bot'], yticklabels=['Human', 'Bot'])
    plt.title('Bot vs Human Classification')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.tight_layout()

    plot_path = os.path.join(OUTPUT_DIR, 'bot_classification_confusion_matrix.png')
    plt.savefig(plot_path)
    plt.close()

    return {"metrics": report, "plot": 'bot_classification_confusion_matrix.png'}
