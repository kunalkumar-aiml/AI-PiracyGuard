import config
from core.fingerprint import generate_video_fingerprint, compare_fingerprints
from logger import log_activity
from database.db_manager import init_db, save_fingerprint, get_all_fingerprints


# initialize database on import
init_db()

# store scan results
DETECTION_RESULTS = []


def register_known_video(video_path):
    print("Registering known video:", video_path)

    fingerprint = generate_video_fingerprint(video_path)

    if fingerprint:
        save_fingerprint(video_path, fingerprint)
        print("Video saved to database.\n")
        log_activity(f"Saved fingerprint for {video_path}")


def check_video(video_path):
    print("Checking video:", video_path)

    new_fp = generate_video_fingerprint(video_path)

    if not new_fp:
        print("Fingerprint generation failed.")
        return

    best_similarity = 0

    known_data = get_all_fingerprints()

    for known_video, known_fp in known_data.items():
        similarity = compare_fingerprints(new_fp, known_fp)

        print("Compared with:", known_video)
        print("Similarity:", similarity, "%")

        if similarity > best_similarity:
            best_similarity = similarity

    if best_similarity >= config.PIRACY_THRESHOLD:
        status = "Pirated"
    else:
        status = "Safe"

    result = {
        "video": video_path,
        "similarity": best_similarity,
        "status": status
    }

    DETECTION_RESULTS.append(result)

    log_activity(f"{video_path} - {status} ({best_similarity}%)")

    print("Final decision:", status, "\n")


if __name__ == "__main__":
    register_known_video("known_video.mp4")
    check_video("test_video.mp4")
