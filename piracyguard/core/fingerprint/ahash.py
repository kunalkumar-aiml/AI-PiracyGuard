"""Average Hash (aHash) implementation for frames."""

import cv2
import numpy as np


def compute_ahash(frame: np.ndarray) -> str:
    """Compute average hash (aHash) for a given frame.

    Resizes to 8x8, converts to grayscale, computes average intensity,
    and returns a 64-character binary string representation.
    """
    # Resize to 8x8 and convert to grayscale
    resized = cv2.resize(frame, (8, 8), interpolation=cv2.INTER_AREA)
    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized

    # Compute mean intensity
    mean_val = gray.mean()

    # Generate binary hash string
    hash_bits = gray > mean_val
    hash_string = "".join(
        ["1" if bit else "0" for row in hash_bits for bit in row]
    )

    return hash_string
