import os
import jwt
import datetime
from flask import Flask, request, jsonify
from functools import wraps

from src.pipeline import run_pipeline
from core.detection_engine import register_known_video
from database.db_manager import (
    get_db_stats,
    save_scan_history,
    get_scan_history
)
from visualizer import generate_summary

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or data.get("username") != "admin" or data.get("password") != "admin":
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {
            "user": "admin",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({"token": token})


@app.route("/")
def home():
    return jsonify({"service": "AI Piracy Guard", "status": "API Running"})


@app.route("/run", methods=["POST"])
@token_required
def run_scan():
    run_pipeline()
    summary = generate_summary()

    save_scan_history(
        summary["total_videos"],
        summary["piracy_matches"],
        summary["safe_videos"]
    )

    return jsonify({"status": "Scan completed", "summary": summary})


@app.route("/register", methods=["POST"])
@token_required
def register():
    data = request.get_json()

    if not data or "video_path" not in data:
        return jsonify({"error": "video_path required"}), 400

    register_known_video(data["video_path"])
    return jsonify({"status": "Video registered"})


@app.route("/stats", methods=["GET"])
@token_required
def stats():
    return jsonify(generate_summary())


@app.route("/db-info", methods=["GET"])
@token_required
def db_info():
    return jsonify(get_db_stats())


@app.route("/history", methods=["GET"])
@token_required
def history():
    return jsonify({"scan_history": get_scan_history()})


if __name__ == "__main__":
    app.run(debug=True)
