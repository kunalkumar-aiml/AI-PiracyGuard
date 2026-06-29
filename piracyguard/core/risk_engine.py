"""Multi-signal weighted risk engine.

Processes forensics results (fingerprint, deepfake, watermark, metadata, ocr,
logo) and computes a composite threat score, risk level, and action plan.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

from piracyguard.config import settings
from piracyguard.database.models import RiskLevel
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RiskAssessment:
    """Dataclass holding composite threat scoring outputs."""
    risk_score: float                # Overall threat rating (0.0 - 100.0)
    risk_level: RiskLevel           # NONE, LOW, MEDIUM, HIGH, CRITICAL
    confidence: float               # Confidence rating (0.0 - 1.0)
    explanation: Dict[str, Any]     # Contributions of each signal
    recommended_action: str         # Action plan recommendation


class RiskEngine:
    """Combines forensic scores using weights config to classify safety risk."""

    @staticmethod
    def assess(
        similarity_score: float,
        deepfake_score: float = 0.0,
        watermark_present_score: float = 0.0,
        watermark_tampering_score: float = 0.0,
        metadata_anomaly_score: float = 0.0,
        audio_anomaly_score: float = 0.0,
        logo_detected: bool = False,
        ocr_flagged: bool = False
    ) -> RiskAssessment:
        """Perform multi-signal weighted threat assessment.

        Args:
            similarity_score: Fingerprint piracy match score (0 - 100).
            deepfake_score: Face manipulation likelihood (0 - 100).
            watermark_present_score: Score indicating watermark presence (0 - 100).
            watermark_tampering_score: Score indicating watermark tampering (0 - 100).
            metadata_anomaly_score: Container/codec anomaly score (0 - 100).
            audio_anomaly_score: Audio anomaly/manipulation score (0 - 100).
            logo_detected: True if an unauthorized logo overlay is found.
            logo_detected: True if unauthorized OCR copyright string matches.

        Returns:
            RiskAssessment.
        """
        # Read weights from settings
        w_sim = settings.RISK_WEIGHT_SIMILARITY
        w_deep = settings.RISK_WEIGHT_DEEPFAKE
        w_water = settings.RISK_WEIGHT_WATERMARK
        w_meta = settings.RISK_WEIGHT_METADATA
        w_audio = settings.RISK_WEIGHT_AUDIO

        # 1. Base Weighted Score Calculation
        # Similarity score weighs 100% copy match vs no match
        weighted_sim = similarity_score * w_sim
        weighted_deep = deepfake_score * w_deep
        
        # Watermark score is a combination of presence/tampering indicators
        watermark_score = max(watermark_present_score, watermark_tampering_score)
        weighted_water = watermark_score * w_water
        
        weighted_meta = metadata_anomaly_score * w_meta
        weighted_audio = audio_anomaly_score * w_audio

        composite_score = (
            weighted_sim +
            weighted_deep +
            weighted_water +
            weighted_meta +
            weighted_audio
        )

        # 2. Heuristic Bonuses (Overlays/Copyright Flags)
        # Unauthorized overlay logo presence increases score by a flat bonus (up to 15 points)
        if logo_detected:
            composite_score += 10.0
        
        # OCR flagged text (e.g. copyright notices) adds minor risk weight
        if ocr_flagged:
            composite_score += 5.0

        # Bound composite score
        risk_score = min(100.0, max(0.0, round(composite_score, 2)))

        # 3. Determine Risk Level
        # Classification thresholds:
        # - CRITICAL: >= 90 (Almost certain copyright leak / deepfake attack)
        # - HIGH: >= 75
        # - MEDIUM: >= 40
        # - LOW: >= 15
        # - NONE: < 15
        if risk_score >= 90.0:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 75.0:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 40.0:
            risk_level = RiskLevel.MEDIUM
        elif risk_score >= 15.0:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.NONE

        # 4. Confidence Score Calculation
        # Confidence increases with the number of high-quality active signals checked
        signals_checked = 1  # Similarity checked by default
        if deepfake_score > 0.0:
            signals_checked += 1
        if watermark_score > 0.0:
            signals_checked += 1
        if metadata_anomaly_score > 0.0:
            signals_checked += 1
        if audio_anomaly_score > 0.0:
            signals_checked += 1

        confidence = min(1.0, 0.5 + (signals_checked * 0.1))

        # 5. Generate Explanation and Action Plan
        explanation = {
            "similarity_contribution": round(weighted_sim, 2),
            "deepfake_contribution": round(weighted_deep, 2),
            "watermark_contribution": round(weighted_water, 2),
            "metadata_contribution": round(weighted_meta, 2),
            "audio_contribution": round(weighted_audio, 2),
            "logo_bonus": 10.0 if logo_detected else 0.0,
            "ocr_bonus": 5.0 if ocr_flagged else 0.0
        }

        # Recommended Action Plan
        if risk_level == RiskLevel.CRITICAL:
            action = "CRITICAL THREAT: Automatic takedown recommended. Register forensic evidence in ledger."
        elif risk_level == RiskLevel.HIGH:
            action = "HIGH THREAT: Restrict video access. Queue for manual forensic analyst verification."
        elif risk_level == RiskLevel.MEDIUM:
            action = "MODERATE RISK: Flag file for continuous traffic and copyright monitoring."
        elif risk_level == RiskLevel.LOW:
            action = "LOW RISK: Safe to release. Minor anomalies logged."
        else:
            action = "CLEAN: No action required. Clear of piracy or deepfake signals."

        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=round(confidence, 2),
            explanation=explanation,
            recommended_action=action
        )
