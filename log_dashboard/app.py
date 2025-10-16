from flask import Flask
from routes.dashboard_routes import dashboard_bp
from routes.log_detail_routes import log_detail_bp
import os

# Explicit template folder
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

# Register Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(log_detail_bp)

if __name__ == "__main__":
    app.run(debug=True)
