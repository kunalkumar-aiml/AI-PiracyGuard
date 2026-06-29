"""Invisible watermark and steganography detection.

Analyzes Least Significant Bits (LSB) and pixel statistics for
anomalous payloads or hidden signatures.
"""

from typing import Tuple
import cv2
import numpy as np


class InvisibleWatermarkDetector:
    """Detects invisible watermarking patterns and steganographic modifications."""

    def analyze_lsb_entropy(self, channel: np.ndarray) -> float:
        """Analyze the entropy of the Least Significant Bits (LSB).

        Natural images have structured LSBs. Steganography/watermarks randomize LSBs,
        causing their entropy to approach 1.0 (maximum uncertainty).

        Args:
            channel: Grayscale channel or single color plane (numpy array).

        Returns:
            Entropy ratio indicator (0.0 to 1.0).
        """
        # Extract LSB (bit 0)
        lsb = channel & 1

        # Flatten and compute frequency of 0s and 1s
        total = lsb.size
        count_ones = np.sum(lsb)
        count_zeros = total - count_ones

        p1 = count_ones / total
        p0 = count_zeros / total

        # Compute entropy
        if p1 == 0 or p0 == 0:
            entropy = 0.0
        else:
            entropy = - (p0 * np.log2(p0) + p1 * np.log2(p1))

        # In natural images LSB entropy is high, but artificial noise injection
        # pushed it closer to 1.0. We check how close it is to 1.0
        # If it is extremely close (e.g. > 0.999), it indicates high-density steganography.
        # Let's map it:
        if entropy > 0.9995:
            return 1.0
        elif entropy > 0.99:
            return float((entropy - 0.90) / 0.10)
        return 0.0

    def analyze_dwt_statistics(self, channel: np.ndarray) -> float:
        """Analyze Discrete Wavelet Transform (DWT) subband statistical anomalies.

        Digital watermarking (like Cox algorithm) inserts signals into high/mid-frequency
        DWT bands. This modifies the coefficient distribution (kurtosis/variance).

        Args:
            channel: Grayscale channel (numpy array).

        Returns:
            Anomaly confidence score (0.0 to 1.0).
        """
        # Simple DWT Haar approximation using differences:
        # H1 = (col[even] - col[odd])
        # V1 = (row[even] - row[odd])
        # This gives high frequency coefficients without pywt package dependency.
        if channel.shape[0] < 4 or channel.shape[1] < 4:
            return 0.0

        # Cast to float for math
        img_f = channel.astype(np.float32)

        # Compute horizontal difference (high-frequency)
        horiz_hf = img_f[:, 0::2] - img_f[:, 1::2]
        # Compute vertical difference (high-frequency)
        vert_hf = img_f[0::2, :] - img_f[1::2, :]

        # Combine high frequency bands
        hf_coefficients = np.concatenate([horiz_hf.flatten(), vert_hf.flatten()])

        # Calculate statistics
        mean = np.mean(hf_coefficients)
        variance = np.var(hf_coefficients)

        if variance == 0:
            return 0.0

        # Calculate kurtosis: E[(X-mu)^4] / sigma^4
        kurtosis = np.mean((hf_coefficients - mean) ** 4) / (variance ** 2)

        # Natural image high frequency subbands exhibit highly leptokurtic distribution (kurtosis > 6)
        # Low kurtosis (< 3) in high-frequency bands indicates artificial signal injection
        if kurtosis < 3.0:
            # Low kurtosis: uniform/normal noise added (watermark signature)
            return float(min(1.0, (3.0 - kurtosis) / 2.0))
        return 0.0

    def detect(self, frame: np.ndarray) -> Tuple[float, str]:
        """Detect invisible watermarks.

        Returns:
            Tuple of (confidence_score [0.0 - 1.0], method_used).
        """
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Check LSB entropy
        lsb_score = self.analyze_lsb_entropy(gray)
        # Check DWT statistics
        dwt_score = self.analyze_dwt_statistics(gray)

        best_score = max(lsb_score, dwt_score)
        method = "lsb_entropy" if lsb_score >= dwt_score else "dwt_kurtosis"

        return best_score, method
