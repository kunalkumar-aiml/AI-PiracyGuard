"""Logo and overlay icon detection in video frames.

Uses contour analysis to locate non-moving overlay elements (broadcaster watermark
logos) and templates if configured.
"""

from dataclasses import dataclass
import os
from typing import List, Dict, Any, Tuple, Optional

import cv2
import numpy as np

from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class LogoResult:
    """Dataclass holding logo detection output."""
    detections: List[Dict[str, Any]]  # List of dicts with: name, bbox, score
    confidence_scores: List[float]    # Confidences
    detected_count: int               # Count


class LogoDetector:
    """Detects TV/OTT logos and overlay graphics on video frames."""

    def __init__(self, templates_dir: Optional[str] = None) -> None:
        self.templates: Dict[str, np.ndarray] = {}
        
        if templates_dir and os.path.exists(templates_dir):
            try:
                for file in os.listdir(templates_dir):
                    if file.lower().endswith((".png", ".jpg", ".jpeg")):
                        name, _ = os.path.splitext(file)
                        path = os.path.join(templates_dir, file)
                        # Load as grayscale
                        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                        if img is not None:
                            self.templates[name] = img
                logger.info(f"Loaded {len(self.templates)} logo templates from: {templates_dir}")
            except Exception as e:
                logger.warning(f"Error loading logo templates: {e}")

    def detect_static_overlays(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect potential overlay graphics using color segmentation & geometric rules.

        TV logos and OTT watermarks are often semi-transparent or high contrast solid blocks
        located in corners.
        """
        # Convert BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = frame.shape[:2]

        # Extract Saturation channel
        s_channel = hsv[:, :, 1]
        
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(s_channel, (5, 5), 0)

        # Threshold to find highly saturated or high-contrast blocks
        _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY)

        # Focus only on corner regions (where logos are located)
        # using a mask for corners
        mask = np.zeros_like(thresh)
        margin_h = int(h * 0.25)
        margin_w = int(w * 0.25)

        mask[0:margin_h, 0:margin_w] = 255              # Top-Left
        mask[0:margin_h, w - margin_w:w] = 255          # Top-Right
        mask[h - margin_h:h, 0:margin_w] = 255          # Bottom-Left
        mask[h - margin_h:h, w - margin_w:w] = 255      # Bottom-Right

        masked_thresh = cv2.bitwise_and(thresh, mask)

        # Find contours
        contours, _ = cv2.findContours(masked_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        logo_boxes = []
        for c in contours:
            x, y, w_box, h_box = cv2.boundingRect(c)
            area = w_box * h_box
            
            # Logo boxes are small but not too small, and roughly square/rectangular
            # Typically 20px to 120px on a standard screen
            if 400 < area < 20000 and 15 < w_box < 150 and 15 < h_box < 150:
                logo_boxes.append((x, y, w_box, h_box))

        return logo_boxes

    def match_known_logos(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Perform template matching against loaded logo templates.

        Returns:
            List of match objects.
        """
        if not self.templates:
            return []

        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        detections = []

        for name, template in self.items():
            t_h, t_w = template.shape[:2]
            
            try:
                res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                # If match is high enough (e.g. > 0.8)
                if max_val > 0.75:
                    detections.append({
                        "name": name,
                        "score": float(max_val),
                        "bbox": (max_loc[0], max_loc[1], t_w, t_h)
                    })
            except cv2.error:
                continue

        return detections

    def items(self) -> List[Tuple[str, np.ndarray]]:
        """Helper to return templates list."""
        return list(self.templates.items())

    def detect(self, frame: np.ndarray) -> LogoResult:
        """Run logo detection on the frame.

        Args:
            frame: Input BGR frame image.

        Returns:
            LogoResult.
        """
        detections = []
        confidences = []

        # 1. Match known logos
        known_matches = self.match_known_logos(frame)
        for match in known_matches:
            detections.append({
                "type": "known_logo",
                "name": match["name"],
                "bbox": match["bbox"]
            })
            confidences.append(match["score"])

        # 2. Match generic static corner overlays (if no known logo matches)
        if not known_matches:
            generic_boxes = self.detect_static_overlays(frame)
            for idx, box in enumerate(generic_boxes):
                detections.append({
                    "type": "generic_overlay",
                    "name": f"Overlay #{idx+1}",
                    "bbox": box
                })
                confidences.append(0.65)  # Default confidence for geometry heuristics

        return LogoResult(
            detections=detections,
            confidence_scores=confidences,
            detected_count=len(detections)
        )
