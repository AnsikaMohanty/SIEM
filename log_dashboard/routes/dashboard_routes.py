from flask import Blueprint, render_template
from db_utils.queries import fetch_count  # import your new fetch_count function

# Create the blueprint first
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")

@dashboard_bp.route("/")
def home():
    antivirus_count = fetch_count("antivirus_logs")
    login_count = fetch_count("login_log_data")
    rdp_count = fetch_count("rdp_events")
    server_access_count = fetch_count("server_access_logs")

    return render_template(
        "dashboard.html",
        antivirus_count=antivirus_count,
        login_count=login_count,
        rdp_count=rdp_count,
        server_access_count=server_access_count
    )
