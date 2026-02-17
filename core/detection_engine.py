import config
from core.fingerprint import generate_video_fingerprint, compare_fingerprints

# store known reference fingerprints
KNOWN_FINGERPRINTS = {}

# store scan results
DETECTION_RESULTS = []


def register_known_video(video_path):
    print("Registering known video:", video_path)

    fingerprint = generate_video_fingerprint(video_path)

    if fingerprint:
        KNOWN_FINGERPRINTS[video_path] = fingerprint
        print("Video registered.\n")


def check_video(video_path):
    print("Checking video:", video_path)

    new_fp = generate_video_fingerprint(video_path)

    if not new_fp:
        print("Fingerprint generation failed.")
        return

    best_similarity = 0

    for known_video, known_fp in KNOWN_FINGERPRINTS.items():
        similarity = compare_fingerprints(new_fp, known_fp)

        print("Compared with:", known_video)
        print("Similarity:", similarity, "%")

        if similarity > best_similarity:
            best_similarity = similarity

    # use threshold from config
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

    print("Final decision:", status, "\n")


if __name__ == "__main__":
    register_known_video("known_video.mp4")
    check_video("test_video.mp4")
