"""Perceptual Hash (pHash) implementation for frames.

Uses Discrete Cosine Transform (DCT) to capture low-frequency visual features.
"""

import cv2
import numpy as np


def compute_phash(frame: np.ndarray) -> str:
    """Compute perceptual hash (pHash) for a given frame.

    Resizes to 32x32, converts to grayscale, applies Discrete Cosine Transform (DCT),
    takes the top-left 8x8 DCT coefficients (excluding DC coefficient),
    computes median coefficient value, and returns a 64-character binary string.
    """
    # Resize to 32x32 and convert to grayscale
    resized = cv2.resize(frame, (32, 32), interpolation=cv2.INTER_AREA)
    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized

    # Convert to float for DCT
    gray_float = np.float32(gray) / 255.0

    # Apply 2D DCT
    dct = cv2.dct(gray_float)

    # Take the top-left 8x8 region (ignoring the 0,0 DC coefficient for brightness invariance)
    # The 8x8 region runs from index 0 to 7. Sometimes (0,0) is kept or skipped. Skipping (0,0) is better.
    # We will use top-left 8x8 but starting at 1,1 or we can just use the 8x8 block and skip the very first.
    # To be simple and robust: take 8x8 block from top left: dct[0:8, 0:8]
    dct_block = dct[0:8, 0:8]

    # Calculate median (excluding the DC coefficient at 0,0 to preserve brightness invariance)
    # We can flatten and exclude element at 0 (which corresponds to 0,0)
    flat_block = dct_block.flatten()
    median_val = np.median(flat_block[1:])

    # Generate binary hash string
    hash_bits = dct_block > median_val
    hash_string = "".join(
        ["1" if bit else "0" for row in hash_bits for bit in row]
    )

    return hash_string
