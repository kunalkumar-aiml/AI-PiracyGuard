"""Temporal fingerprinting for video frame sequences.

Captures dynamic changes in a video over time by examining frame-to-frame
hash differences (Hamming distance delta) and structural flows.
"""

from typing import List


def compute_temporal_fingerprint(ahashes: List[str], phashes: List[str]) -> str:
    """Compute a single temporal fingerprint string from a sequence of frame hashes.

    Tracks transitions between consecutive frames.
    Returns a sequence of symbols (e.g., 'U' for rising differences,
    'D' for falling differences, 'S' for stable) representing the velocity
    of visual changes in the video.
    """
    if len(ahashes) < 2 or len(phashes) < 2:
        return ""

    transition_string = []

    for i in range(1, min(len(ahashes), len(phashes))):
        # Calculate Hamming distance between current frame and previous frame
        # representing temporal motion/change
        dist_a = sum(1 for c1, c2 in zip(ahashes[i], ahashes[i - 1]) if c1 != c2)
        dist_p = sum(1 for c1, c2 in zip(phashes[i], phashes[i - 1]) if c1 != c2)

        # Average change velocity
        avg_change = (dist_a + dist_p) / 2.0

        # Discretize change velocity into symbols:
        # - Low motion (Stable): < 5 bits changed
        # - Medium motion: 5 - 15 bits changed
        # - High motion (Cut/Transition): > 15 bits changed
        if avg_change < 5:
            transition_string.append("S")
        elif avg_change < 15:
            transition_string.append("M")
        else:
            transition_string.append("H")

    return "".join(transition_string)


def compare_temporal_fingerprints(tf1: str, tf2: str) -> float:
    """Compare two temporal fingerprints using Levenshtein distance similarity.

    Args:
        tf1: First temporal fingerprint.
        tf2: Second temporal fingerprint.

    Returns:
        Similarity score between 0.0 and 100.0.
    """
    if not tf1 or not tf2:
        return 0.0

    # Clean empty strings
    tf1_len, tf2_len = len(tf1), len(tf2)

    # Dynamic programming for edit distance (Levenshtein)
    dp = [[0] * (tf2_len + 1) for _ in range(tf1_len + 1)]

    for i in range(tf1_len + 1):
        dp[i][0] = i
    for j in range(tf2_len + 1):
        dp[0][j] = j

    for i in range(1, tf1_len + 1):
        for j in range(1, tf2_len + 1):
            if tf1[i - 1] == tf2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,      # Deletion
                    dp[i][j - 1] + 1,      # Insertion
                    dp[i - 1][j - 1] + 1   # Substitution
                )

    edit_distance = dp[tf1_len][tf2_len]
    max_len = max(tf1_len, tf2_len)

    if max_len == 0:
        return 100.0

    similarity = (1 - (edit_distance / max_len)) * 100
    return round(similarity, 2)
