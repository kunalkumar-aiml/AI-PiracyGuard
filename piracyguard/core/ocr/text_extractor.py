"""OCR text extraction from video frames.

Optionally uses pytesseract for full text parsing, with a robust OpenCV
contour-based fallback for text bounding box localization.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

import cv2
import numpy as np

from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

# Try importing pytesseract
try:
    import pytesseract
except ImportError:
    pytesseract = None


@dataclass
class OCRResult:
    """Dataclass holding OCR extraction results."""
    extracted_texts: List[str]      # List of strings extracted
    confidence_scores: List[float]  # Confidence for each string
    regions: List[Tuple[int, int, int, int]]  # Bounding boxes (x, y, w, h)


class OCRExtractor:
    """Extracts burnt-in text, channel names, and copyright strings from video frames."""

    def __init__(self) -> None:
        self.tesseract_available = pytesseract is not None
        if self.tesseract_available:
            try:
                # Basic test to verify tesseract binary is on PATH
                pytesseract.get_tesseract_version()
            except Exception:
                logger.warning(
                    "pytesseract library is installed but Tesseract binary is not on PATH. "
                    "Entering OpenCV contour-based localization mode."
                )
                self.tesseract_available = False

    def localize_text_regions(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Identify potential text regions using OpenCV contour analysis (MSER approximation).

        Useful for cropping frame parts before OCR, or for fallback bounding-box output.
        """
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        h, w = gray.shape[:2]
        
        # Apply morphological gradient to highlight text edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)

        # Threshold to binary
        _, thresh = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Connect text blocks using morphological closing
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)

        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        text_regions = []
        for c in contours:
            x, y, w_box, h_box = cv2.boundingRect(c)
            # Filter based on typical text region aspect ratios and sizes
            aspect = w_box / float(h_box) if h_box > 0 else 0.0
            
            # Text bounding boxes are usually wider than they are tall,
            # and are within reasonable size bounds
            if 1.5 < aspect < 20.0 and 8 < h_box < 80 and w_box > 25:
                # Keep text region bounding box
                text_regions.append((x, y, w_box, h_box))

        return text_regions

    def extract(self, frame: np.ndarray) -> OCRResult:
        """Extract text from a frame.

        Args:
            frame: Input BGR frame image.

        Returns:
            OCRResult.
        """
        extracted_texts = []
        confidence_scores = []
        regions = self.localize_text_regions(frame)

        if not regions:
            return OCRResult(extracted_texts=[], confidence_scores=[], regions=[])

        # If tesseract is available, perform OCR on cropped regions
        if self.tesseract_available and pytesseract:
            for (x, y, w, h) in regions:
                # Crop region with a tiny 2px border
                h_max, w_max = frame.shape[:2]
                y1, y2 = max(0, y - 2), min(h_max, y + h + 2)
                x1, x2 = max(0, x - 2), min(w_max, x + w + 2)
                
                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    continue

                try:
                    # Run Tesseract OCR on crop
                    # --psm 7: Treat the image as a single text line.
                    text = pytesseract.image_to_string(
                        crop, 
                        config="--psm 7"
                    ).strip()
                    
                    if len(text) > 2:  # Ignore tiny noise characters
                        extracted_texts.append(text)
                        confidence_scores.append(0.90)  # Average Tesseract confidence
                except Exception as e:
                    logger.debug(f"OCR region extraction error: {e}")
                    
        else:
            # OpenCV fallback: we return localized bounding box coordinates,
            # indicating where text regions exist, but leave text strings empty
            # (or log them as localized boxes)
            for idx, (x, y, w, h) in enumerate(regions):
                extracted_texts.append(f"[Localized Text Region #{idx+1}]")
                confidence_scores.append(0.50)

        return OCRResult(
            extracted_texts=extracted_texts,
            confidence_scores=confidence_scores,
            regions=regions
        )
