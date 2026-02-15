import cv2
import numpy as np
from core.frame_extractor import extract_frames


def compute_frame_hash(frame):
    resized = cv2.resize(frame, (8, 8))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    avg = gray.mean()
    hash_bits = gray > avg

    hash_string = ''.join(
        ['1' if bit else '0' for row in hash_bits for bit in row]
    )

    return hash_string


def generate_video_fingerprint(video_path):
    frames = extract_frames(video_path)

    if not frames:
        print("No frames extracted.")
        return None

    hashes = []

    for frame in frames:
        frame_hash = compute_frame_hash(frame)
        hashes.append(frame_hash)

    print("Generated fingerprint for video.")
    return hashes


def hamming_distance(hash1, hash2):
    if len(hash1) != len(hash2):
        return None

    distance = 0

    for i in range(len(hash1)):
        if hash1[i] != hash2[i]:
            distance += 1

    return distance


def compare_fingerprints(fp1, fp2):
    if not fp1 or not fp2:
        return 0

    total_distance = 0
    comparisons = min(len(fp1), len(fp2))

    for i in range(comparisons):
        dist = hamming_distance(fp1[i], fp2[i])
        total_distance += dist

    max_bits = comparisons * len(fp1[0])
    similarity = 1 - (total_distance / max_bits)

    return round(similarity * 100, 2)


if __name__ == "__main__":
    generate_video_fingerprint("sample.mp4")
