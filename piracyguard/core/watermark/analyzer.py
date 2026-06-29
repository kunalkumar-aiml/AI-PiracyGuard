"""Unified watermark and tampering forensics analyzer.

Combines visible edge analysis, invisible steganographic checks,
and frequency-domain FFT/DCT verification across video frames.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import numpy as np

from piracyguard.config import settings
from piracyguard.core.frame_extractor import FrameExtractor
from piracyguard.core.watermark.visible import VisibleWatermarkDetector
from piracyguard.core.watermark.invisible import InvisibleWatermarkDetector
from piracyguard.core.watermark.frequency import FrequencyWatermarkDetector
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class WatermarkResult:
    """Dataclass holding watermark and tampering analysis results."""
    video_path: str
    watermark_present_score: float  # Composite watermark score (0 - 100)
    tampering_score: float          # Composite tampering indicator (0 - 100)
    is_suspected: bool              # True if watermark tampering is flagged
    confidence: float               # Combined confidence score (0.0 - 1.0)
    details: Dict[str, Any]         # Details of sub-module metrics


class WatermarkAnalyzer:
    """Orchestrates comprehensive watermark analysis on video files."""

    def __init__(
        self,
        template_path: Optional[str] = None,
        frame_extractor: Optional[FrameExtractor] = None
    ) -> None:
        self.extractor = frame_extractor or FrameExtractor()
        self.visible_detector = VisibleWatermarkDetector(template_path)
        self.invisible_detector = InvisibleWatermarkDetector()
        self.frequency_detector = FrequencyWatermarkDetector()

    def analyze(self, video_path: str, step: int = 30) -> WatermarkResult:
        """Run multi-modal watermark detection over a video.

        Args:
            video_path: Path to the video file.
            step: Frame sampling interval.

        Returns:
            WatermarkResult containing analysis scores.
        """
        logger.info(
            "Starting watermark analysis",
            extra={"video_path": video_path, "step": step}
        )

        try:
            frames_data = self.extractor.extract_uniform(video_path, step=step)
        except Exception as e:
            logger.error(f"Failed to read frames for watermark analysis: {e}")
            frames_data = []

        if not frames_data:
            return WatermarkResult(
                video_path=video_path,
                watermark_present_score=0.0,
                tampering_score=0.0,
                is_suspected=False,
                confidence=0.0,
                details={}
            )

        visible_scores = []
        invisible_scores = []
        fft_scores = []
        dct_scores = []

        # Analyze each frame
        for _, _, frame in frames_data:
            # 1. Visible detection
            vis_score, _ = self.visible_detector.detect(frame)
            visible_scores.append(vis_score)

            # 2. Invisible detection
            invis_score, _ = self.invisible_detector.detect(frame)
            invisible_scores.append(invis_score)

            # 3. Frequency detection
            freq_res = self.frequency_detector.detect(frame)
            fft_scores.append(freq_res["fft_score"])
            dct_scores.append(freq_res["dct_score"])

        # Compute averages across all sampled frames
        avg_visible = float(np.mean(visible_scores)) * 100.0
        avg_invisible = float(np.mean(invisible_scores)) * 100.0
        avg_fft = float(np.mean(fft_scores)) * 100.0
        avg_dct = float(np.mean(dct_scores)) * 100.0

        # Calculate a watermark presence score (combines visible + FFT/DCT frequency signatures)
        presence_score = (avg_visible * 0.50) + (avg_fft * 0.25) + (avg_dct * 0.25)

        # Calculate a tampering score (high invisible steganography or frequency mismatch)
        # Steganography signatures or DWT/DCT coefficient changes typically indicate tampering
        tampering_score = (avg_invisible * 0.60) + (avg_dct * 0.40)

        # Determine flags based on settings thresholds
        threshold = settings.WATERMARK_THRESHOLD
        
        # Suspect watermark tampering if either presence or tampering exceeds threshold
        is_suspected = presence_score >= threshold or tampering_score >= threshold

        # Confidence is derived from the consistency of findings
        confidence = 0.80 if len(frames_data) >= 5 else 0.50

        result = WatermarkResult(
            video_path=video_path,
            watermark_present_score=round(presence_score, 2),
            tampering_score=round(tampering_score, 2),
            is_suspected=is_suspected,
            confidence=confidence,
            details={
                "visible_overlay_score": round(avg_visible, 2),
                "invisible_signature_score": round(avg_invisible, 2),
                "fft_spectrum_score": round(avg_fft, 2),
                "dct_coefficients_score": round(avg_dct, 2),
                "frame_count_evaluated": len(frames_data)
            }
        )

        logger.info(
            "Watermark analysis complete",
            extra={
                "video_path": video_path,
                "presence_score": result.watermark_present_score,
                "tampering_score": result.tampering_score,
                "is_suspected": result.is_suspected
            }
        )

        return result
