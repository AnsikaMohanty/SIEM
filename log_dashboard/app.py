from flask import Flask, request, render_template, redirect, url_for, jsonify
import pandas as pd
from log_parser import process_log_file, insert_data_into_db, create_database_and_table, process_login_log_file
import mysql.connector
from collections import Counter
from datetime import datetime, timedelta
import random  # For demo data, remove in production

app = Flask(__name__)

# Initialize DB and table
create_database_and_table()

@app.route('/')
def index():
    return render_template('index.html')  # Now serves landing page

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', stats=get_stats())

@app.route('/login-analytics')
def login_analytics():
    return render_template('login_logoff.html', stats=get_login_analytics())

@app.route('/api/login-timeline')
def login_timeline():
    period = request.args.get('period', '24h')
    return jsonify(get_timeline_data(period))

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['logfile']
    if file:
        filepath = f"uploaded_{file.filename}"
        file.save(filepath)
        
        if 'login' in file.filename.lower():
            process_login_log_file(filepath)
        else:
            df = process_log_file(filepath)
            if not df.empty:
                insert_data_into_db(df)
                
    return redirect(url_for('dashboard'))  # Redirect to dashboard now

def get_login_analytics():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='rootroot',
            database='siem'
        )
        cursor = conn.cursor(dictionary=True)

        # Get summary statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT username) as unique_users,
                COUNT(DISTINCT hostname) as unique_hosts,
                MAX(check_time) as last_check
            FROM log_data
        """)
        summary = cursor.fetchone()

        # Get timeline data for the last 24 hours
        cursor.execute("""
            SELECT 
                DATE_FORMAT(event_timestamp, '%H:00') as hour,
                SUM(CASE WHEN status = 'Logon' THEN 1 ELSE 0 END) as logon_count,
                SUM(CASE WHEN status = 'Logoff' THEN 1 ELSE 0 END) as logoff_count
            FROM log_data
            WHERE event_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY DATE_FORMAT(event_timestamp, '%H:00')
            ORDER BY hour
        """)
        timeline_data = cursor.fetchall()

        # Get all events
        cursor.execute("""
            SELECT 
                DATE_FORMAT(event_timestamp, '%Y-%m-%d %H:%i:%s') as timestamp,
                username,
                hostname,
                ip_address,
                status
            FROM log_data
            ORDER BY event_timestamp DESC
        """)
        events = cursor.fetchall()

        return {
            'total_events': summary['total_events'] or 0,
            'unique_users': summary['unique_users'] or 0,
            'unique_hosts': summary['unique_hosts'] or 0,
            'last_check': summary['last_check'].strftime('%Y-%m-%d %H:%M:%S') if summary['last_check'] else 'Never',
            'events': events,
            'timeline_labels': [row['hour'] for row in timeline_data],
            'logon_timeline': [row['logon_count'] for row in timeline_data],
            'logoff_timeline': [row['logoff_count'] for row in timeline_data]
        }
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return {
            'total_events': 0,
            'unique_users': 0,
            'unique_hosts': 0,
            'last_check': 'Never',
            'events': [],
            'timeline_labels': [],
            'logon_timeline': [],
            'logoff_timeline': []
        }
    finally:
        cursor.close()
        conn.close()

def get_timeline_data(period):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='rootroot',
            database='siem'
        )
        cursor = conn.cursor(dictionary=True)

        if period == '24h':
            interval = 'HOUR'
            lookback = 'INTERVAL 24 HOUR'
            format_str = '%H:00'
        elif period == '7d':
            interval = 'DAY'
            lookback = 'INTERVAL 7 DAY'
            format_str = '%Y-%m-%d'
        else:  # 30d
            interval = 'DAY'
            lookback = 'INTERVAL 30 DAY'
            format_str = '%Y-%m-%d'

        cursor.execute(f"""
            SELECT 
                DATE_FORMAT(event_time, '{format_str}') as period,
                SUM(CASE WHEN event_type = 'login' THEN 1 ELSE 0 END) as logins,
                SUM(CASE WHEN event_type = 'logoff' THEN 1 ELSE 0 END) as logoffs
            FROM login_logs
            WHERE event_time >= DATE_SUB(NOW(), {lookback})
            GROUP BY DATE_FORMAT(event_time, '{format_str}')
            ORDER BY event_time
        """)
        results = cursor.fetchall()

        return {
            'labels': [row['period'] for row in results],
            'login_data': [row['logins'] for row in results],
            'logoff_data': [row['logoffs'] for row in results]
        }
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return {
            'labels': [],
            'login_data': [],
            'logoff_data': []
        }
    finally:
        cursor.close()
        conn.close()

def get_stats():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='rootroot',
            database='siem'
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT ip, date, method FROM server_access_logs")
        rows = cursor.fetchall()

        total = len(rows)
        method_counts = Counter(row['method'] for row in rows)
        ip_counts = Counter(row['ip'] for row in rows)
        day_counts = Counter(row['date'].split(':')[0] for row in rows)

        return {
            'total': total,
            'method_counts': dict(method_counts),
            'ip_counts': dict(ip_counts.most_common(5)),
            'daily_counts': dict(day_counts)
        }
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
