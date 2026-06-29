"""Unified video fingerprinting engine.

Combines spatial hashing (aHash, pHash, dHash) with temporal sequence
analysis to generate a multi-dimensional VideoFingerprint.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional
import json

from piracyguard.core.fingerprint.ahash import compute_ahash
from piracyguard.core.fingerprint.dhash import compute_dhash
from piracyguard.core.fingerprint.phash import compute_phash
from piracyguard.core.fingerprint.temporal import (
    compare_temporal_fingerprints,
    compute_temporal_fingerprint,
)
from piracyguard.core.frame_extractor import FrameExtractor
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VideoFingerprint:
    """Dataclass holding all fingerprint components of a video."""
    video_path: str
    ahashes: List[str]
    phashes: List[str]
    dhashes: List[str]
    temporal: str
    frame_count: int
    duration_seconds: float

    def to_json(self) -> str:
        """Serialize fingerprint to JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "VideoFingerprint":
        """Deserialize fingerprint from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class FingerprintEngine:
    """Unified engine for extracting and comparing video fingerprints."""

    def __init__(self, frame_extractor: Optional[FrameExtractor] = None) -> None:
        self.extractor = frame_extractor or FrameExtractor()

    def generate(self, video_path: str, step: int = 30) -> Optional[VideoFingerprint]:
        """Generate a complete multi-dimensional fingerprint for a video.

        Args:
            video_path: Path to the video file.
            step: Frame sampling interval.

        Returns:
            VideoFingerprint object if successful, None otherwise.
        """
        logger.info(
            "Generating video fingerprint",
            extra={"video_path": video_path, "step": step},
        )

        try:
            # Extract frames
            frames_data = self.extractor.extract_uniform(video_path, step=step)
            if not frames_data:
                logger.warning("No frames extracted, fingerprint generation skipped.")
                return None

            ahashes = []
            phashes = []
            dhashes = []

            for idx, timestamp, frame in frames_data:
                # Compute individual hashes
                ahashes.append(compute_ahash(frame))
                phashes.append(compute_phash(frame))
                dhashes.append(compute_dhash(frame))

            # Compute temporal fingerprint
            temporal = compute_temporal_fingerprint(ahashes, phashes)

            # Get video properties
            total_frames, _, duration, _, _ = self.extractor.get_video_properties(video_path)

            return VideoFingerprint(
                video_path=video_path,
                ahashes=ahashes,
                phashes=phashes,
                dhashes=dhashes,
                temporal=temporal,
                frame_count=total_frames,
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error(
                f"Failed to generate fingerprint: {e}",
                extra={"video_path": video_path},
                exc_info=True,
            )
            return None

    @staticmethod
    def hamming_distance(h1: str, h2: str) -> float:
        """Compute normalized Hamming distance similarity between two hashes.

        Returns:
            Similarity percentage between 0.0 and 100.0.
        """
        if len(h1) != len(h2) or not h1:
            return 0.0

        differences = sum(1 for c1, c2 in zip(h1, h2) if c1 != c2)
        similarity = (1 - (differences / len(h1))) * 100
        return similarity

    def compare_spatial_lists(self, list1: List[str], list2: List[str]) -> float:
        """Compare two lists of frame hashes using an alignment-free match.

        Compares each hash in list1 with all hashes in list2 to find the best match.
        Matches are averaged.
        """
        if not list1 or not list2:
            return 0.0

        total_similarity = 0.0
        comparisons = 0

        # Optimization: limit search space if list is extremely large
        # Here we do cross-frame comparison but cap to avoid n^2 explosion on long lists
        for h1 in list1:
            best_sim = 0.0
            for h2 in list2:
                sim = self.hamming_distance(h1, h2)
                if sim > best_sim:
                    best_sim = sim
                if best_sim >= 98.0:  # Early stop if exact match found
                    break

            total_similarity += best_sim
            comparisons += 1

        if comparisons == 0:
            return 0.0

        return total_similarity / comparisons

    def compare(self, fp1: VideoFingerprint, fp2: VideoFingerprint) -> float:
        """Compare two video fingerprints and return a similarity score.

        Combines:
        - aHash similarity (20% weight)
        - pHash similarity (40% weight)
        - dHash similarity (20% weight)
        - Temporal sequence similarity (20% weight)

        Returns:
            Composite similarity percentage (0.0 to 100.0).
        """
        logger.debug(
            "Comparing video fingerprints",
            extra={"video1": fp1.video_path, "video2": fp2.video_path},
        )

        sim_a = self.compare_spatial_lists(fp1.ahashes, fp2.ahashes)
        sim_p = self.compare_spatial_lists(fp1.phashes, fp2.phashes)
        sim_d = self.compare_spatial_lists(fp1.dhashes, fp2.dhashes)
        sim_t = compare_temporal_fingerprints(fp1.temporal, fp2.temporal)

        # Weighted combination
        composite_score = (
            (sim_a * 0.20) +
            (sim_p * 0.40) +
            (sim_d * 0.20) +
            (sim_t * 0.20)
        )

        logger.info(
            "Fingerprint comparison complete",
            extra={
                "video1": fp1.video_path,
                "video2": fp2.video_path,
                "sim_a": round(sim_a, 2),
                "sim_p": round(sim_p, 2),
                "sim_d": round(sim_d, 2),
                "sim_t": round(sim_t, 2),
                "composite": round(composite_score, 2),
            },
        )

        return round(composite_score, 2)
