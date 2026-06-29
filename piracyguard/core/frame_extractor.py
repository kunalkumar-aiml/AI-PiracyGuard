"""Frame extraction utilities for video forensics.

Provides efficient frame sampling from video files with support for
uniform sampling and keyframe/scene boundary checks.
"""

import os
from typing import Generator, List, Optional, Tuple

import cv2
import numpy as np

from piracyguard.exceptions import FrameExtractionError, VideoNotFoundError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


class FrameExtractor:
    """Extracts frames from video files for forensic analysis.

    Supports uniform frame sampling and extracts frame metadata.
    """

    @staticmethod
    def get_video_properties(video_path: str) -> Tuple[int, float, float, int, int]:
        """Extract basic video properties without decoding all frames.

        Args:
            video_path: Path to the video file.

        Returns:
            Tuple of (total_frames, fps, duration_seconds, width, height).

        Raises:
            VideoNotFoundError: If the file does not exist.
            FrameExtractionError: If OpenCV fails to open the video.
        """
        if not os.path.exists(video_path):
            raise VideoNotFoundError(video_path)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FrameExtractionError(
                video_path, reason="OpenCV failed to open the video file."
            )

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Handle edge case where frame count is reported as 0 or negative
            if total_frames <= 0:
                total_frames = 0

            # Calculate duration
            duration = total_frames / fps if fps > 0 else 0.0

            return total_frames, fps, duration, width, height
        finally:
            cap.release()

    def extract_uniform(
        self,
        video_path: str,
        step: int = 30,
        max_frames: Optional[int] = None,
    ) -> List[Tuple[int, float, np.ndarray]]:
        """Extract frames at regular intervals.

        Args:
            video_path: Path to the video file.
            step: Interval between extracted frames (e.g. every 30th frame).
            max_frames: Maximum number of frames to extract.

        Returns:
            List of tuples containing (frame_index, timestamp_ms, frame_image).

        Raises:
            FrameExtractionError: If frame extraction fails.
        """
        logger.info(
            "Starting uniform frame extraction",
            extra={"video_path": video_path, "step": step},
        )

        try:
            total_frames, fps, duration, _, _ = self.get_video_properties(video_path)
        except Exception as e:
            raise FrameExtractionError(video_path, reason=str(e))

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FrameExtractionError(
                video_path, reason="Failed to re-open video for frame extraction."
            )

        extracted_frames: List[Tuple[int, float, np.ndarray]] = []
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % step == 0:
                    timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                    extracted_frames.append((frame_idx, timestamp_ms, frame))

                    if max_frames and len(extracted_frames) >= max_frames:
                        logger.debug("Reached maximum requested frames limit")
                        break

                frame_idx += 1

            logger.info(
                "Uniform frame extraction completed",
                extra={
                    "video_path": video_path,
                    "extracted_count": len(extracted_frames),
                    "total_frames": frame_idx,
                },
            )
            return extracted_frames

        except Exception as e:
            logger.error(
                f"Error during frame extraction: {e}",
                extra={"video_path": video_path},
                exc_info=True,
            )
            raise FrameExtractionError(video_path, reason=str(e))
        finally:
            cap.release()

    def extract_generator(
        self,
        video_path: str,
        step: int = 30,
    ) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        """Generator version for streaming frame extraction (memory efficient).

        Args:
            video_path: Path to the video file.
            step: Interval between extracted frames.

        Yields:
            Tuple of (frame_index, timestamp_ms, frame_image).
        """
        if not os.path.exists(video_path):
            raise VideoNotFoundError(video_path)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FrameExtractionError(
                video_path, reason="Failed to open video in generator mode."
            )

        frame_idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % step == 0:
                    timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                    yield frame_idx, timestamp_ms, frame

                frame_idx += 1
        finally:
            cap.release()
