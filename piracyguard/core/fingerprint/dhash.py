"""Difference Hash (dHash) implementation for frames.

Measures horizontal gradients of pixel intensity.
"""

import cv2
import numpy as np


def compute_dhash(frame: np.ndarray) -> str:
    """Compute difference hash (dHash) for a given frame.

    Resizes to 9x8 (9 columns, 8 rows) and converts to grayscale.
    Compares adjacent pixels horizontally (col[x] > col[x+1])
    to generate a 64-character binary string.
    """
    # Resize to 9x8 and convert to grayscale
    # 9 columns, 8 rows. cv2.resize takes (width, height) i.e. (9, 8)
    resized = cv2.resize(frame, (9, 8), interpolation=cv2.INTER_AREA)
    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized

    # Compute difference between adjacent pixels in each row
    # Compare column x with column x+1. This yields 8 differences per row,
    # across 8 rows, total of 64 bits.
    hash_bits = gray[:, :-1] > gray[:, 1:]

    # Generate binary hash string
    hash_string = "".join(
        ["1" if bit else "0" for row in hash_bits for bit in row]
    )

    return hash_string
