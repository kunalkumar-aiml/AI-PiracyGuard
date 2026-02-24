import config
from core.fingerprint import generate_video_fingerprint, compare_fingerprints
from core.risk_engine import calculate_risk
from deepfake_detector import analyze_video
from watermark_analyzer import analyze_watermark
from database.db_manager import (
    init_db,
    save_fingerprint,
    get_all_fingerprints,
    save_scan_history
)

init_db()

DETECTION_RESULTS = []


def register_known_video(video_path):
    fingerprint = generate_video_fingerprint(video_path)

    if fingerprint:
        save_fingerprint(video_path, fingerprint)


def check_video(video_path):
    known_videos = get_all_fingerprints()
    new_fp = generate_video_fingerprint(video_path)

    if not new_fp:
        return

    highest_similarity = 0

    for known_video, known_fp in known_videos.items():
        similarity = compare_fingerprints(new_fp, known_fp)
        if similarity > highest_similarity:
            highest_similarity = similarity

    deepfake_result = analyze_video(video_path)
    deepfake_score = deepfake_result["deepfake_score"]

    watermark_result = analyze_watermark(video_path)
    watermark_flag = watermark_result["watermark_suspected"]

    risk_analysis = calculate_risk(
        similarity_score=highest_similarity,
        deepfake_score=deepfake_score,
        watermark_flag=watermark_flag
    )

    result = {
        "video_path": video_path,
        "similarity": highest_similarity,
        "deepfake_score": deepfake_score,
        "risk_score": risk_analysis["risk_score"],
        "risk_level": risk_analysis["risk_level"]
    }

    DETECTION_RESULTS.append(result)

    # 🔥 Save to database history
    save_scan_history(result)
