"""Visible watermark and logo overlay detection.

Analyzes border regions for static visual elements, high edge density,
and matches logo templates if provided.
"""

from typing import Optional, Tuple
import cv2
import numpy as np


class VisibleWatermarkDetector:
    """Detects visible channel logos, overlays, and burn-in watermarks."""

    def __init__(self, template_path: Optional[str] = None) -> None:
        self.template: Optional[np.ndarray] = None
        if template_path and os.path.exists(template_path):
            # Load template in grayscale
            self.template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    def analyze_edge_density(self, frame: np.ndarray) -> float:
        """Analyze edge density in typical logo/watermark locations (corners/borders).

        Args:
            frame: Input BGR frame image.

        Returns:
            Normalized edge density score (0.0 to 1.0).
        """
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        h, w = gray.shape[:2]

        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Define border/corner regions (top-left, top-right, bottom-left, bottom-right)
        # using a 20% margin from borders
        margin_h = int(h * 0.2)
        margin_w = int(w * 0.2)

        corners = [
            edges[0:margin_h, 0:margin_w],              # Top-Left
            edges[0:margin_h, w - margin_w:w],          # Top-Right
            edges[h - margin_h:h, 0:margin_w],          # Bottom-Left
            edges[h - margin_h:h, w - margin_w:w]       # Bottom-Right
        ]

        # Compute ratio of edge pixels to total pixels in the corner regions
        edge_pixels = sum(np.sum(corner > 0) for corner in corners)
        total_pixels = 4 * (margin_h * margin_w)

        density = edge_pixels / total_pixels if total_pixels > 0 else 0.0

        # Normalize relative to a typical watermark threshold (e.g. 5% edge pixels)
        # Cap at 1.0
        normalized_score = min(1.0, density / 0.05)
        return float(normalized_score)

    def match_template(self, frame: np.ndarray) -> float:
        """Perform template matching if a reference watermark template is loaded.

        Args:
            frame: Input BGR frame image.

        Returns:
            Match confidence score (0.0 to 1.0).
        """
        if self.template is None:
            return 0.0

        # Convert frame to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Template matching using normalized cross-correlation
        try:
            res = cv2.matchTemplate(gray, self.template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            return float(max(0.0, max_val))
        except cv2.error:
            # Handle template size mismatch or other OpenCV errors
            return 0.0

    def detect(self, frame: np.ndarray) -> Tuple[float, str]:
        """Detect visible watermarks in a frame.

        Returns:
            Tuple of (confidence_score [0.0 - 1.0], method_used).
        """
        if self.template is not None:
            score = self.match_template(frame)
            return score, "template_matching"
        
        score = self.analyze_edge_density(frame)
        return score, "border_edge_density"
