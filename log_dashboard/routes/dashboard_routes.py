from flask import Blueprint, render_template
from db_utils.queries import fetch_count

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def dashboard():
    try:
        return render_template(
            "dashboard.html",
            antivirus_count=fetch_count("antivirus_logs"),
            login_count=fetch_count("login_log_data"),
            access_count=fetch_count("server_access_logs"),
            winlog_count=fetch_count("windows_logon_events")
        )
    except Exception as e:
        return f"Error loading dashboard: {str(e)}"
