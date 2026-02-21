import config
from core.fingerprint import generate_video_fingerprint, compare_fingerprints
from core.risk_engine import calculate_risk
from deepfake_detector import analyze_video
from database.db_manager import init_db, save_fingerprint, get_all_fingerprints

# Initialize DB
init_db()

# Structured detection results
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

    # Compare against known fingerprints
    for known_video, known_fp in known_videos.items():
        similarity = compare_fingerprints(new_fp, known_fp)

        if similarity > highest_similarity:
            highest_similarity = similarity

    # 🔥 Deepfake Analysis Integration
    deepfake_result = analyze_video(video_path)
    deepfake_score = deepfake_result["deepfake_score"]

    # Placeholder watermark flag (future integration)
    watermark_flag = False

    # Composite Risk Calculation
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
        "risk_level": risk_analysis["risk_level"],
        "details": risk_analysis["explanation"]
    }

    DETECTION_RESULTS.append(result)
