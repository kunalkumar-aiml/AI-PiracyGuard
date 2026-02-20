import config
from core.fingerprint import generate_video_fingerprint, compare_fingerprints
from core.risk_engine import calculate_risk
from database.db_manager import init_db, save_fingerprint, get_all_fingerprints

# Initialize DB
init_db()

# Store structured results
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

    # Deepfake + watermark simulated for now
    deepfake_score = 0
    watermark_flag = False

    risk_analysis = calculate_risk(
        similarity_score=highest_similarity,
        deepfake_score=deepfake_score,
        watermark_flag=watermark_flag
    )

    result = {
        "video_path": video_path,
        "similarity": highest_similarity,
        "risk_score": risk_analysis["risk_score"],
        "risk_level": risk_analysis["risk_level"],
        "details": risk_analysis["explanation"]
    }

    DETECTION_RESULTS.append(result)
