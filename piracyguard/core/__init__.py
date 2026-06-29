"""Core forensics engine for AI-PiracyGuard.

Provides video fingerprinting, deepfake detection, watermark analysis,
metadata forensics, and multi-signal risk calculation.
"""

from piracyguard.core.detection_engine import DetectionEngine
from piracyguard.core.frame_extractor import FrameExtractor
from piracyguard.core.risk_engine import RiskEngine

__all__ = [
    "DetectionEngine",
    "FrameExtractor",
    "RiskEngine",
]
