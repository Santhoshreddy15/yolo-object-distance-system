import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.config import Config
from backend.routes.api import api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS: whitelist explicit frontend origins only (never wildcard in production)
    allowed_origins = os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    CORS(app, resources={r"/api/*": {"origins": [o.strip() for o in allowed_origins]}})
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return jsonify({
            "project": "YOLO-Based Object Detection and Distance Measurement",
            "domain": "Artificial Intelligence and Computer Vision",
            "api_endpoints": [
                "/api/health",
                "/api/detect (POST)",
                "/api/distance (POST)"
            ],
            "status": "Online"
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Starting YOLO Object Detection & Distance Measurement Backend on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)
