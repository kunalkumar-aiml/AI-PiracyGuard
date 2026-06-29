"""Optical Character Recognition (OCR) package for AI-PiracyGuard.

Provides text extraction from video frames to identify burn-in watermarks,
copyright strings, and overlay text.
"""

from piracyguard.core.ocr.text_extractor import OCRExtractor, OCRResult

__all__ = [
    "OCRExtractor",
    "OCRResult",
]
