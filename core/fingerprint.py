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
        try:
            frame_hash = compute_frame_hash(frame)
            hashes.append(frame_hash)
        except Exception as e:
            print("Error hashing frame:", str(e))

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

    total_similarity = 0
    comparisons = 0

    for hash1 in fp1:
        best_distance = None

        for hash2 in fp2:
            dist = hamming_distance(hash1, hash2)

            if dist is None:
                continue

            if best_distance is None or dist < best_distance:
                best_distance = dist

        if best_distance is not None:
            max_bits = len(hash1)
            similarity = 1 - (best_distance / max_bits)
            total_similarity += similarity
            comparisons += 1

    if comparisons == 0:
        return 0

    final_score = (total_similarity / comparisons) * 100
    return round(final_score, 2)
