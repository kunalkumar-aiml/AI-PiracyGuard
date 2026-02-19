import os
from flask import Flask, request, jsonify
from src.pipeline import run_pipeline
from core.detection_engine import register_known_video
from database.db_manager import (
    get_db_stats,
    save_scan_history,
    get_scan_history
)
from visualizer import generate_summary

app = Flask(__name__)

# API key from environment variable
API_KEY = os.environ.get("API_KEY", "default_key")


def authorize(req):
    key = req.headers.get("x-api-key")
    return key == API_KEY


@app.route("/")
def home():
    return jsonify({
        "service": "AI Piracy Guard",
        "status": "API Running"
    })


@app.route("/run", methods=["POST"])
def run_scan():
    if not authorize(request):
        return jsonify({"error": "Unauthorized"}), 401

    run_pipeline()
    summary = generate_summary()

    # Save scan history
    save_scan_history(
        summary["total_videos"],
        summary["piracy_matches"],
        summary["safe_videos"]
    )

    return jsonify({
        "status": "Scan completed",
        "summary": summary
    })


@app.route("/register", methods=["POST"])
def register():
    if not authorize(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    if not data or "video_path" not in data:
        return jsonify({"error": "video_path required"}), 400

    video_path = data["video_path"]
    register_known_video(video_path)

    return jsonify({
        "status": "Video registered",
        "video_path": video_path
    })


@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(generate_summary())


@app.route("/db-info", methods=["GET"])
def db_info():
    return jsonify(get_db_stats())


@app.route("/history", methods=["GET"])
def history():
    return jsonify({
        "scan_history": get_scan_history()
    })


if __name__ == "__main__":
    app.run(debug=True)
