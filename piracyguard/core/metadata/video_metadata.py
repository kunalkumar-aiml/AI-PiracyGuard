"""Video metadata forensics and anomaly detection.

Extracts stream parameters and detects container level edit traces
or mismatched codecs.
"""

from dataclasses import dataclass
import os
import subprocess
import json
from typing import Dict, Any, Optional

from piracyguard.core.frame_extractor import FrameExtractor
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MetadataResult:
    """Dataclass holding video metadata forensics analysis."""
    video_path: str
    anomaly_score: float             # Score (0 - 100) indicating tampering/irregularity
    details: Dict[str, Any]         # Collected metadata properties
    is_anomaly: bool                # True if anomaly_score >= threshold


class MetadataAnalyzer:
    """Extracts video stream metadata and flags editing software traces."""

    def __init__(self, frame_extractor: Optional[FrameExtractor] = None) -> None:
        self.extractor = frame_extractor or FrameExtractor()

    def _run_ffprobe(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Attempt to call ffprobe to extract extensive container/stream metadata.

        Falls back gracefully to None if ffprobe is not installed on system.
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            logger.debug("ffprobe not available on system, falling back to OpenCV.")
            return None

    def analyze(self, video_path: str) -> MetadataResult:
        """Run metadata forensics on a video file.

        Args:
            video_path: Path to the video file.

        Returns:
            MetadataResult.
        """
        logger.info("Starting metadata analysis", extra={"video_path": video_path})

        anomaly_score = 0.0
        details: Dict[str, Any] = {}

        # 1. Fetch properties using OpenCV FrameExtractor (guaranteed fallback)
        try:
            total_frames, fps, duration, width, height = self.extractor.get_video_properties(video_path)
            file_size_bytes = os.path.getsize(video_path)

            details.update({
                "source": "opencv",
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "duration_seconds": round(duration, 2),
                "frame_count": total_frames,
                "file_size_bytes": file_size_bytes
            })
        except Exception as e:
            logger.error(f"OpenCV metadata extraction failed: {e}")
            return MetadataResult(
                video_path=video_path,
                anomaly_score=100.0,
                details={"error": f"Failed to parse video: {e}"},
                is_anomaly=True
            )

        # 2. Try ffprobe for deep metadata (codecs, encoding software, tags)
        ffprobe_data = self._run_ffprobe(video_path)
        
        if ffprobe_data:
            details["source"] = "ffprobe"
            
            # Format metadata
            fmt = ffprobe_data.get("format", {})
            streams = ffprobe_data.get("streams", [])
            
            # Extract tags (editing software indicators)
            tags = fmt.get("tags", {})
            encoder = tags.get("encoder", "").lower()
            compatible_brands = fmt.get("compatible_brands", "")

            # Video stream details
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

            details.update({
                "format_name": fmt.get("format_name"),
                "format_long_name": fmt.get("format_long_name"),
                "video_codec": video_stream.get("codec_name"),
                "video_codec_long": video_stream.get("codec_long_name"),
                "audio_codec": audio_stream.get("codec_name") if audio_stream else "none",
                "encoder": tags.get("encoder"),
                "writing_library": tags.get("writing_library") or tags.get("comment"),
                "bitrate_kbps": int(fmt.get("bit_rate", 0)) // 1000 if fmt.get("bit_rate") else None,
            })

            # Check anomalies
            # Anomalies:
            # - Traces of video editing software (Premiere, Handbrake, FFmpeg, Adobe, DaVinci)
            editing_tools = ["adobe", "premiere", "handbrake", "imovie", "final cut", "shotcut", "davinci"]
            for tool in editing_tools:
                if tool in encoder or tool in details.get("writing_library", "").lower():
                    anomaly_score += 40.0
                    details["editing_software_trace"] = f"Detected trace of {tool} in encoder metadata."
                    break

            # - Missing standard camera metadata tags (e.g. model, make)
            # Standard cell phone/camera videos contain metadata like 'make', 'model'.
            # Screen recorded or re-encoded videos lack these, which is a moderate anomaly.
            if not tags.get("make") and not tags.get("model"):
                # Standard for camera captures, lack thereof adds slight anomaly score
                anomaly_score += 15.0
                details["camera_metadata_missing"] = True

            # - Video container mismatch
            # If the compatible brands tag doesn't match standard container types
            if "isom" not in compatible_brands and "mp42" not in compatible_brands and details.get("video_codec") == "h264":
                # Editing tools often output h264 but with custom brand signatures
                anomaly_score += 10.0

        else:
            # OpenCV fallback basic anomaly checks
            # Mismatched file extension vs OpenCV readability check
            _, ext = os.path.splitext(video_path)
            if ext.lower() not in [".mp4", ".mkv", ".mov"] and details["frame_count"] > 0:
                anomaly_score += 20.0
                details["extension_warning"] = f"Unusual container extension: {ext}"

        # Bound anomaly score between 0 and 100
        anomaly_score = min(100.0, max(0.0, anomaly_score))
        
        # Consider a score >= 40.0 as an anomaly (indicates editing or metadata stripping)
        is_anomaly = anomaly_score >= 40.0

        logger.info(
            "Metadata analysis complete",
            extra={
                "video_path": video_path,
                "anomaly_score": anomaly_score,
                "is_anomaly": is_anomaly
            }
        )

        return MetadataResult(
            video_path=video_path,
            anomaly_score=round(anomaly_score, 2),
            details=details,
            is_anomaly=is_anomaly
        )
