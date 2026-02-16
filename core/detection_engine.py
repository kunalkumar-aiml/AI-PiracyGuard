DETECTION_RESULTS = []
from core.fingerprint import generate_video_fingerprint, compare_fingerprints

# Simulated known pirated fingerprint storage
KNOWN_FINGERPRINTS = {}

def register_known_video(video_path):
    print("Registering known video:", video_path)
    fingerprint = generate_video_fingerprint(video_path)
    if fingerprint:
        KNOWN_FINGERPRINTS[video_path] = fingerprint
        print("Video registered.\n")


def check_video(video_path, threshold=75):
    print("Checking video:", video_path)

    new_fp = generate_video_fingerprint(video_path)

    if not new_fp:
        print("Fingerprint generation failed.")
        return

    for known_video, known_fp in KNOWN_FINGERPRINTS.items():
        similarity = compare_fingerprints(new_fp, known_fp)
        print("Compared with:", known_video)
        print("Similarity:", similarity, "%")

        if similarity >= threshold:
            print("⚠ High similarity detected. Possible piracy.\n")
            return

    print("No strong match found.\n")


if __name__ == "__main__":
    # Example usage
    register_known_video("known_video.mp4")
    check_video("test_video.mp4")
