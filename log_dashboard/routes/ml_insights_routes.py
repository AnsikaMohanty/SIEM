from flask import Blueprint, render_template
from pathlib import Path

# Import our refactored Antivirus ML scripts
from ml_models.antivirus_ml.anomaly_detection_antiV import run_anomaly_detection
from ml_models.antivirus_ml.malware_type_prediction import run_malware_type_prediction
from ml_models.antivirus_ml.severity_prediction import run_severity_prediction

# RDP ML import remains unchanged
from ml_models.rdp_ml.rdp_ml1 import analyze_rdp_logs

ml_insights_bp = Blueprint('ml_insights', __name__, url_prefix='/ml_insights')

@ml_insights_bp.route('/antivirus')
def antivirus():
    anomaly_results = run_anomaly_detection()
    malware_results = run_malware_type_prediction()
    severity_results = run_severity_prediction()

    return render_template(
        "ml_insights/antivirus_insights.html",
        anomaly=anomaly_results,
        malware=malware_results,
        severity=severity_results
    )



@ml_insights_bp.route('/rdp')
def rdp():
    try:
        classification_results, user_stats, images = analyze_rdp_logs()
    except FileNotFoundError as e:
        return f"CSV file not found at: {e.filename}"

    return render_template(
        "ml_insights/rdp_insights.html",
        results=classification_results,
        user_stats=user_stats,
        images=images
    )
