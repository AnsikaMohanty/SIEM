import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import Error
import os

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootroot'
MYSQL_DATABASE = 'siem'

OUTPUT_DIR = os.path.join('static', 'server_outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def analyze_status_patterns():
    """Analyze status code distribution and request patterns."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        query = "SELECT ip, status, method, size FROM server_access_logs"
        df = pd.read_sql(query, conn)
        conn.close()
    except Error as e:
        return {"summary": f"MySQL error: {e}", "plot": None, "metrics": {}}

    if df.empty:
        return {"summary": "⚠️ No server access log data found.", "plot": None, "metrics": {}}

    # Clean up data
    df['status'] = pd.to_numeric(df['status'], errors='coerce')
    df['size'] = pd.to_numeric(df['size'], errors='coerce')
    df = df.dropna(subset=['status', 'size', 'method'])

    # Status code categories
    df['status_group'] = df['status'].apply(
        lambda x: '2xx Success' if 200 <= x < 300 else
                  '3xx Redirect' if 300 <= x < 400 else
                  '4xx Client Error' if 400 <= x < 500 else
                  '5xx Server Error' if 500 <= x < 600 else 'Other'
    )

    # Aggregation
    agg = df.groupby(['ip', 'status_group']).size().unstack(fill_value=0)
    agg['total_requests'] = agg.sum(axis=1)
    agg['error_rate'] = (agg.get('4xx Client Error', 0) + agg.get('5xx Server Error', 0)) / agg['total_requests']

    # Find top IPs by error rate
    top_ips = agg.sort_values(by='error_rate', ascending=False).head(10).reset_index()

    # Summary metrics
    summary = {
        "Total Unique IPs": len(df['ip'].unique()),
        "Average Error Rate": f"{agg['error_rate'].mean() * 100:.2f}%",
        "Most Problematic IP": top_ips.iloc[0]['ip'] if not top_ips.empty else "N/A"
    }

    # Visualization
    status_counts = df['status_group'].value_counts()
    plt.figure(figsize=(6, 4))
    status_counts.plot(kind='bar', color=['green', 'blue', 'orange', 'red', 'gray'])
    plt.title("HTTP Status Code Distribution")
    plt.ylabel("Number of Requests")
    plt.tight_layout()

    plot_path = os.path.join(OUTPUT_DIR, 'status_pattern_analysis.png')
    plt.savefig(plot_path)
    plt.close()

    return {
        "summary": f"✅ Status pattern analysis complete. {summary['Total Unique IPs']} IPs analyzed.",
        "plot": 'status_pattern_analysis.png',
        "metrics": summary,
        "top_ips": top_ips.head(5).to_dict(orient="records")
    }
