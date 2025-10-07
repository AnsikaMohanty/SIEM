# app.py
from flask import Flask
from routes.dashboard_routes import dashboard_bp
from routes.log_detail_routes import log_detail_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(log_detail_bp)

if __name__ == "__main__":
    app.run(debug=True)
