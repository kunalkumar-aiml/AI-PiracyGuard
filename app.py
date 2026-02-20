import os
import jwt
import datetime
from flask import Flask, request, jsonify
from functools import wraps

from job_queue import start_background_scan, get_job_status
from core.detection_engine import register_known_video
from database.db_manager import (
    get_db_stats,
    save_scan_history,
    get_scan_history,
    get_trend_data
)
from visualizer import generate_summary

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")


# ---------------- JWT Middleware ---------------- #

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)

    return decorated


# ---------------- Login ---------------- #

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing credentials"}), 400

    if data.get("username") != "admin" or data.get("password") != "admin":
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


# ---------------- Home ---------------- #

@app.route("/")
def home():
    return jsonify({
        "service": "AI Piracy Guard",
        "status": "API Running (Async Mode)"
    })


# ---------------- Async Scan Start ---------------- #

@app.route("/run", methods=["POST"])
@token_required
def run_scan():
    job_id = start_background_scan()

    return jsonify({
        "message": "Scan started",
        "job_id": job_id
    })


# ---------------- Job Status ---------------- #

@app.route("/job/<job_id>", methods=["GET"])
@token_required
def job_status(job_id):
    return jsonify(get_job_status(job_id))


# ---------------- Register Video ---------------- #

@app.route("/register", methods=["POST"])
@token_required
def register():
    data = request.get_json()

    if not data or "video_path" not in data:
        return jsonify({"error": "video_path required"}), 400

    register_known_video(data["video_path"])

    return jsonify({
        "status": "Video registered"
    })


# ---------------- Stats ---------------- #

@app.route("/stats", methods=["GET"])
@token_required
def stats():
    return jsonify(generate_summary())


# ---------------- DB Info ---------------- #

@app.route("/db-info", methods=["GET"])
@token_required
def db_info():
    return jsonify(get_db_stats())


# ---------------- Scan History ---------------- #

@app.route("/history", methods=["GET"])
@token_required
def history():
    return jsonify({
        "scan_history": get_scan_history()
    })


# ---------------- Trend Analytics ---------------- #

@app.route("/analytics/trend", methods=["GET"])
@token_required
def analytics_trend():
    return jsonify({
        "trend": get_trend_data()
    })


if __name__ == "__main__":
    app.run(debug=True)
