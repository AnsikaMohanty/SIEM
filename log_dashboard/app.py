from flask import Flask
from routes.dashboard_routes import dashboard_bp
from routes.log_detail_routes import log_detail_bp
from routes.ml_insights_routes import ml_insights_bp   # 🔹 New import
import os

# Explicit template folder
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

# Register Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(log_detail_bp)
app.register_blueprint(ml_insights_bp)  # 🔹 Register the new ML Insights blueprint

if __name__ == "__main__":
    app.run(debug=True)
