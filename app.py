from flask import Flask, request, jsonify
from src.pipeline import run_pipeline
from core.detection_engine import register_known_video
from database.db_manager import get_db_stats

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({"message": "AI Piracy Guard API Running"})


@app.route("/run", methods=["POST"])
def run_scan():
    run_pipeline()
    return jsonify({"status": "Scan completed"})


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    video_path = data.get("video_path")

    if not video_path:
        return jsonify({"error": "video_path required"}), 400

    register_known_video(video_path)
    return jsonify({"status": "Video registered"})


@app.route("/db-info", methods=["GET"])
def db_info():
    stats = get_db_stats()
    return jsonify(stats)


if __name__ == "__main__":
    app.run(debug=True)
