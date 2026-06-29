"""Frequency-domain watermark and tampering analysis.

Performs Fast Fourier Transform (FFT) and Discrete Cosine Transform (DCT)
analyses to detect periodic grid patterns and compression artifacts.
"""

from typing import Dict, Any
import cv2
import numpy as np


class FrequencyWatermarkDetector:
    """Detects frequency-domain watermark signatures and compression traces."""

    def analyze_fft_grid(self, gray_frame: np.ndarray) -> float:
        """Detect periodic grid watermarks using 2D FFT magnitude spectrum.

        Periodic watermarks (like grid overlays or frequency noise signatures)
        manifest as distinct high-magnitude spikes (peaks) in the FFT spectrum.

        Args:
            gray_frame: Input grayscale frame image.

        Returns:
            Normalized peak magnitude detection score (0.0 to 1.0).
        """
        h, w = gray_frame.shape[:2]
        # Perform 2D Fast Fourier Transform
        f_transform = np.fft.fft2(gray_frame)
        f_shift = np.fft.fftshift(f_transform)
        
        # Calculate magnitude spectrum (log scale for visualization/scoring)
        magnitude = np.abs(f_shift)
        
        # Avoid division by zero
        magnitude_log = np.log(magnitude + 1.0)

        # Normalize spectrum
        norm_mag = (magnitude_log - np.min(magnitude_log)) / (np.max(magnitude_log) - np.min(magnitude_log) + 1e-6)

        # Center coordinates
        cy, cx = h // 2, w // 2

        # Create a mask to block out the DC component (central low frequencies)
        # using a radius of 15 pixels
        y, x = np.ogrid[:h, :w]
        center_mask = ((x - cx) ** 2 + (y - cy) ** 2) <= 15 ** 2
        norm_mag_high = norm_mag.copy()
        norm_mag_high[center_mask] = 0.0

        # Find the highest peak in high-frequency bands
        max_peak = np.max(norm_mag_high)

        # Find average background high frequency magnitude
        mean_high = np.mean(norm_mag_high[norm_mag_high > 0])

        # If the peak is significantly higher than the average,
        # it indicates a periodic grid watermark signature
        peak_ratio = max_peak / mean_high if mean_high > 0 else 0.0

        # Map typical spikes (ratio > 4.5) to confidence score [0.0 - 1.0]
        confidence = min(1.0, max(0.0, (peak_ratio - 2.0) / 3.0))
        return float(confidence)

    def analyze_block_dct(self, gray_frame: np.ndarray) -> float:
        """Analyze frame using 8x8 block-level Discrete Cosine Transform (DCT).

        Upgraded from original DCT check in watermark_analyzer.py.
        Measures variance of mid-frequency coefficients across all 8x8 blocks.

        Args:
            gray_frame: Grayscale frame image.

        Returns:
            Confidence score (0.0 to 1.0).
        """
        h, w = gray_frame.shape[:2]
        # Ensure dimensions are multiples of 8
        h_crop = (h // 8) * 8
        w_crop = (w // 8) * 8
        cropped = gray_frame[0:h_crop, 0:w_crop].astype(np.float32) / 255.0

        # Iterate over 8x8 blocks and calculate DCT
        dct_variances = []
        
        # Optimize loop by using a step of 16 instead of 8 to sample blocks,
        # speeding up processing for high-res frames
        for y in range(0, h_crop, 16):
            for x in range(0, w_crop, 16):
                block = cropped[y:y+8, x:x+8]
                if block.shape != (8, 8):
                    continue
                
                # Apply 2D DCT
                block_dct = cv2.dct(block)
                
                # Extract mid-frequency coefficients
                # Mid frequencies lie along diagonal: (0,2), (1,1), (2,0), etc.
                mid_freqs = [
                    block_dct[0, 2], block_dct[1, 1], block_dct[2, 0],
                    block_dct[1, 2], block_dct[2, 1], block_dct[2, 2]
                ]
                
                # Accumulate variance of mid frequencies across the block
                dct_variances.append(np.var(mid_freqs))

        # Check distribution variance of mid-freq coefficients
        mean_variance = np.mean(dct_variances) if dct_variances else 0.0

        # Natural unwatermarked blocks have low variance in mid frequencies.
        # Structured watermark signatures increase this variance.
        # Normalize relative to reference variance threshold (0.01)
        score = min(1.0, mean_variance / 0.01)
        return float(score)

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """Perform frequency domain checks on the frame.

        Returns:
            Dict containing fft_score, dct_score, and composite frequency score.
        """
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        fft_score = self.analyze_fft_grid(gray)
        dct_score = self.analyze_block_dct(gray)

        # Composite frequency score (average)
        composite = (fft_score + dct_score) / 2.0

        return {
            "fft_score": round(fft_score, 4),
            "dct_score": round(dct_score, 4),
            "frequency_composite": round(composite, 4)
        }
