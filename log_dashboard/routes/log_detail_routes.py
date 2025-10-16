from flask import Blueprint, render_template, request, jsonify
from db_utils.queries import fetch_logs, fetch_summary
from config import get_db_connection


log_detail_bp = Blueprint("logs", __name__, url_prefix="/logs")

def safe_summary(raw_summary, key_map=None):
    """Return a dict with labels and data safe for JSON."""
    labels = []
    data = []
    if raw_summary:
        for row in raw_summary:
            label = row[list(row.keys())[0]]
            if key_map:
                label = key_map.get(label, label)
            labels.append(str(label))
            data.append(row["count"])
    return {"labels": labels, "data": data}

# ---------- Antivirus Logs ----------
@log_detail_bp.route("/antivirus_logs")
def antivirus_logs():
    logs = fetch_logs("antivirus_logs", limit=50)
    severity_summary = safe_summary(fetch_summary("antivirus_logs", "severity"))
    malware_summary = safe_summary(fetch_summary("antivirus_logs", "malware_type"))
    return render_template(
        "antivirus_logs.html",
        logs=logs,
        severity_summary=severity_summary,
        malware_summary=malware_summary
    )

# Show more endpoint for antivirus logs
@log_detail_bp.route("/antivirus_logs/more")
def antivirus_logs_more():
    offset = int(request.args.get("offset", 0))
    search = request.args.get("search", "")
    severity_filter = request.args.get("severity", "")
    all_logs = fetch_logs("antivirus_logs", limit=50, offset=offset, search=search)
    # Apply severity filter manually
    if severity_filter:
        all_logs = [log for log in all_logs if log["severity"].lower() == severity_filter.lower()]
    return jsonify(all_logs)


# ---------- Login Logs ----------
@log_detail_bp.route("/login_log_data")
def login_logs():
    logs = fetch_logs("login_log_data", limit=50)
    
    # Status summary (Success/Failed)
    status_summary = safe_summary(
        fetch_summary("login_log_data", "login_successful"),
        key_map={1: "Successful", 0: "Failed"}  # keep these exact strings
    )

    
    # ASN summary (number of attempts per ASN)
    asn_summary = safe_summary(fetch_summary("login_log_data", "asn"))
    
    return render_template(
        "login_log_data.html",
        logs=logs,
        summary=status_summary,
        asn_summary=asn_summary
    )

# ---------- RDP Events ----------
@log_detail_bp.route('/rdp_events')
def rdp_events():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM rdp_events ORDER BY id DESC LIMIT 50")
    logs = cursor.fetchall()

    # For chart: count Connected, Disconnected, Failed
    cursor.execute("SELECT status, COUNT(*) as count FROM rdp_events GROUP BY status")
    summary_data = cursor.fetchall()

    summary_status = {
        "labels": [row['status'] for row in summary_data],
        "data": [row['count'] for row in summary_data]
    }

    conn.close()
    return render_template('rdp_events.html', logs=logs, summary_status=summary_status)

@log_detail_bp.route('/rdp_events/more')
def rdp_events_more():
    offset = int(request.args.get('offset', 0))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rdp_events ORDER BY id DESC LIMIT %s, 50", (offset,))
    more_logs = cursor.fetchall()
    conn.close()
    return jsonify(more_logs)


# ---------- Server Access Logs ----------
@log_detail_bp.route("/server_access_logs")
def server_access_logs():
    logs = fetch_logs("server_access_logs", limit=50)
    method_summary = safe_summary(fetch_summary("server_access_logs", "method"))
    status_summary = safe_summary(fetch_summary("server_access_logs", "status"))
    return render_template(
        "server_access_logs.html",
        logs=logs,
        method_summary=method_summary,
        status_summary=status_summary
    )

# "Show More" endpoints for JS
@log_detail_bp.route("/<table_name>/more")
def logs_more(table_name):
    offset = int(request.args.get("offset", 0))
    search = request.args.get("search", "")
    logs = fetch_logs(table_name, limit=50, offset=offset, search=search)
    return jsonify(logs)
