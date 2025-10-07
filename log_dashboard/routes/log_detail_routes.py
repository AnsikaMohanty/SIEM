from flask import Blueprint, render_template
from db_utils.queries import fetch_logs, fetch_chart_summary

log_detail_bp = Blueprint("log_detail", __name__)

@log_detail_bp.route("/logs/<log_type>")
def log_detail(log_type):
    try:
        logs = fetch_logs(log_type)

        # Determine correct grouping for chart summary
        if log_type == "login_log_data":
            summary = fetch_chart_summary(log_type, "log_status")
        elif log_type == "windows_logon_events":
            summary = fetch_chart_summary(log_type, "log_status")
        elif log_type == "antivirus_logs":
            summary = fetch_chart_summary(log_type, "severity")
        elif log_type == "server_access_logs":
            summary = fetch_chart_summary(log_type, "status")
        else:
            summary = {"labels": [], "data": []}

        return render_template(
            f"{log_type}.html",
            logs=logs,
            summary=summary
        )
    except Exception as e:
        return f"Error loading {log_type} details: {str(e)}"
