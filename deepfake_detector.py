"""Deepfake detector wrapper

Provides a stable `analyze_video` function that returns a structured
result containing `deepfake_score` (0-100), `is_suspected` (bool) and
`confidence` (0-1).
"""

from models.deepfake_model import DeepfakeModel

_MODEL = DeepfakeModel()
_MODEL.load()


def analyze_video(video_path: str) -> dict:
    """Analyze `video_path` and return structured deepfake results.

    Output example:
    {
      "deepfake_score": 82,
      "is_suspected": True,
      "confidence": 0.91
    }
    """
    prob = _MODEL.predict(video_path)
    score = int(round(prob * 100))

    # Confidence heuristic: if we used an ML model (non-fallback) assume
    # higher confidence, otherwise lower but deterministic.
    confidence = 0.9 if not _MODEL.use_fallback else 0.45

    return {
        "deepfake_score": score,
        "is_suspected": score >= 60,
        "confidence": round(float(confidence), 2),
    }
