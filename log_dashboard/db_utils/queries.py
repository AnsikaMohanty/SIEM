from db_utils.connection import get_db_connection

def fetch_logs(table_name, limit=50):
    """
    Fetch last {limit} rows from given table.
    """
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}")
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return logs

def fetch_count(table_name):
    """
    Returns the total number of rows in a table.
    """
    conn = get_db_connection()
    if not conn:
        return 0
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0

def fetch_chart_summary(table_name, group_by_column):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT {group_by_column}, COUNT(*) as count FROM {table_name} GROUP BY {group_by_column}")
        summary = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching chart summary for {table_name}: {e}")
        summary = []
    cursor.close()
    conn.close()

    labels = [row[group_by_column] if row[group_by_column] else "Unknown" for row in summary]
    data = [row["count"] for row in summary]

    return {"labels": labels, "data": data}
