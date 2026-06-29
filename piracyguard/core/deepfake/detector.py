"""Orchestrator for deepfake detection.

Extracts faces from video frames, executes PyTorch model inference,
and falls back to deterministic heuristics when weights are missing.
"""

from dataclasses import dataclass
import os
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image

from piracyguard.config import settings
from piracyguard.core.deepfake.models.base import BaseDeepfakeModel, get_model
from piracyguard.core.frame_extractor import FrameExtractor
from piracyguard.exceptions import ModelInferenceError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DeepfakeResult:
    """Dataclass holding deepfake analysis outcome."""
    video_path: str
    deepfake_score: float  # Composite score (0 - 100)
    confidence: float       # Confidence score (0.0 - 1.0)
    is_suspected: bool     # True if score >= threshold
    frame_scores: List[float]  # Probabilities per frame
    model_used: str        # Name of model used


class DeepfakeDetector:
    """Detects facial manipulation and deepfakes in video streams.

    Utilizes Haar cascade face extraction followed by neural network inference.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        weights_path: Optional[str] = None,
        device: Optional[str] = None,
        frame_extractor: Optional[FrameExtractor] = None,
    ) -> None:
        self.model_name = model_name or settings.DEEPFAKE_MODEL_NAME
        self.device = device or ("cuda" if settings.USE_GPU else "cpu")
        self.extractor = frame_extractor or FrameExtractor()

        # Initialize face detector (Haar Cascade)
        # Using default OpenCV Haar Cascade XML path
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # Lazy load weights/model
        self.weights_path = weights_path
        self.model: Optional[BaseDeepfakeModel] = None
        self.is_fallback_mode = False

        # Attempt to initialize the neural net
        try:
            self._init_model()
        except Exception as e:
            logger.warning(
                f"Failed to load neural network. Entering fallback mode: {e}"
            )
            self.is_fallback_mode = True

    def _init_model(self) -> None:
        """Initialize and configure PyTorch model architecture."""
        self.model = get_model(self.model_name, device=self.device)

        # Look for weights in the configured weight folder
        w_path = self.weights_path
        if not w_path:
            # Check settings directory
            possible_path = settings.BASE_DIR / settings.MODEL_DIR / f"{self.model_name}.pth"
            if possible_path.exists():
                w_path = str(possible_path)

        if w_path and os.path.exists(w_path):
            self.model.load_weights(w_path)
            self.is_fallback_mode = False
        else:
            logger.warning(
                f"No weight file found for {self.model_name}. "
                "Classifier will run with random initialization or fallback."
            )
            # If no weight file, we can fall back to ImageNet feature-based heuristic,
            # or if in production, raise error. We will allow running random but set fallback mode
            # if we explicitly want deterministic mock weights.
            # To match requirements, we'll mark fallback mode = True if weights are completely absent.
            self.is_fallback_mode = True

    def detect_face(self, frame: np.ndarray) -> Optional[Image.Image]:
        """Detect and crop the primary face in a frame.

        Args:
            frame: Grayscale or BGR frame image.

        Returns:
            PIL Image of face crop, or None if no face detected.
        """
        # Convert BGR to Grayscale for Haar
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        if len(faces) == 0:
            return None

        # Take the largest face area detected
        # x, y, w, h
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face

        # Crop face with a small padding (10%)
        height, width = frame.shape[:2]
        pad_x = int(w * 0.1)
        pad_y = int(h * 0.1)

        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(width, x + w + pad_x)
        y2 = min(height, y + h + pad_y)

        face_crop = frame[y1:y2, x1:x2]

        # Convert back to RGB for PIL / PyTorch
        if len(face_crop.shape) == 3:
            face_crop_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        else:
            face_crop_rgb = cv2.cvtColor(face_crop, cv2.COLOR_GRAY2RGB)

        return Image.fromarray(face_crop_rgb)

    def _deterministic_mock_predict(self, frame: np.ndarray) -> float:
        """Fallback deterministic heuristic for deepfake scoring.

        Uses Laplace variance (blurriness check) and color histogram entropy
        to compute a pseudo-score, ensuring reproducibility.
        """
        # Grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Compute blurriness using Laplacian variance
        # Manipulated deepfakes often have blurred boundary anomalies
        val = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_factor = min(1.0, max(0.0, 1.0 - (val / 500.0)))

        # Compute basic pixel variance
        std_dev = float(np.std(gray))
        var_factor = min(1.0, max(0.0, std_dev / 128.0))

        # Combine into deterministic score [0.0 - 1.0]
        # High blur and high color variance flags anomalous facial boundaries
        score = (blur_factor * 0.70) + (var_factor * 0.30)
        return float(score)

    def analyze(self, video_path: str, step: int = 30) -> DeepfakeResult:
        """Run deepfake analysis over a video.

        Args:
            video_path: Path to the video file.
            step: Frame sampling interval.

        Returns:
            DeepfakeResult.
        """
        logger.info(
            "Starting deepfake analysis",
            extra={"video_path": video_path, "step": step, "fallback": self.is_fallback_mode}
        )

        try:
            frames_data = self.extractor.extract_uniform(video_path, step=step)
        except Exception as e:
            raise ModelInferenceError("DeepfakeDetector", reason=f"Failed to read frames: {e}")

        if not frames_data:
            return DeepfakeResult(
                video_path=video_path,
                deepfake_score=0.0,
                confidence=0.0,
                is_suspected=False,
                frame_scores=[],
                model_used=self.model_name
            )

        frame_scores: List[float] = []
        face_crops: List[Image.Image] = []
        valid_indices: List[int] = []

        # Process each frame
        for idx, (f_idx, timestamp, frame) in enumerate(frames_data):
            if self.is_fallback_mode:
                # Use deterministic mock score
                score = self._deterministic_mock_predict(frame)
                frame_scores.append(score)
            else:
                # Face detection
                face_pil = self.detect_face(frame)
                if face_pil:
                    face_crops.append(face_pil)
                    valid_indices.append(idx)
                else:
                    # If no face detected, we can default to 0.0 or evaluate full frame.
                    # We will append 0.0 for frames without faces, or skip.
                    # To be clean, let's treat no-face frames as low risk (0.0)
                    frame_scores.append(0.0)

        # Batch prediction for neural net if not in fallback mode
        if not self.is_fallback_mode and face_crops and self.model:
            try:
                batch_probs = self.model.predict_batch(face_crops)
                # Map batch outputs back to correct indices
                for prob_idx, frame_list_idx in enumerate(valid_indices):
                    frame_scores[frame_list_idx] = batch_probs[prob_idx]
            except Exception as e:
                logger.error(
                    f"Batch inference failed, falling back to mock scoring: {e}"
                )
                # Recover by filling remaining with mock predictions
                for idx, (f_idx, timestamp, frame) in enumerate(frames_data):
                    if idx >= len(frame_scores):
                        frame_scores.append(self._deterministic_mock_predict(frame))

        # Calculate composite results
        if not frame_scores:
            composite_score = 0.0
            confidence = 0.0
        else:
            # We average the top-3 highest frame scores to identify localized video manipulation
            sorted_scores = sorted(frame_scores, reverse=True)
            top_scores = sorted_scores[:3] if len(sorted_scores) >= 3 else sorted_scores
            composite_score = float(np.mean(top_scores)) * 100.0
            confidence = 0.85 if not self.is_fallback_mode else 0.50

        threshold = settings.DEEPFAKE_THRESHOLD
        is_suspected = composite_score >= threshold

        result = DeepfakeResult(
            video_path=video_path,
            deepfake_score=round(composite_score, 2),
            confidence=confidence,
            is_suspected=is_suspected,
            frame_scores=[round(s, 4) for s in frame_scores],
            model_used=self.model_name if not self.is_fallback_mode else "deterministic_heuristic"
        )

        logger.info(
            "Deepfake analysis complete",
            extra={
                "video_path": video_path,
                "score": result.deepfake_score,
                "is_suspected": result.is_suspected,
                "model": result.model_used
            }
        )

        return result
