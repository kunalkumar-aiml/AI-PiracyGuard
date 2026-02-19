from flask import Flask, request, jsonify
from src.pipeline import run_pipeline
from core.detection_engine import register_known_video
from database.db_manager import get_db_stats
from visualizer import generate_summary

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "service": "AI Piracy Guard",
        "status": "API Running"
    })


@app.route("/run", methods=["POST"])
def run_scan():
    run_pipeline()
    summary = generate_summary()

    return jsonify({
        "status": "Scan completed",
        "summary": summary
    })


@app.route("/register", methods=["POST"])
def register():
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
    summary = generate_summary()
    return jsonify(summary)


@app.route("/db-info", methods=["GET"])
def db_info():
    stats = get_db_stats()
    return jsonify(stats)


if __name__ == "__main__":
    app.run(debug=True)
