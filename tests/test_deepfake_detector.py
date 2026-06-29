import os
import tempfile
import cv2
import numpy as np

from piracyguard.core.deepfake.detector import DeepfakeDetector


def test_analyze_synthetic_video():
    tmp = tempfile.mkdtemp()
    vid = os.path.join(tmp, "test_vid.mp4")

    # Create a tiny synthetic video (12 frames)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(vid, fourcc, 5.0, (64, 64))
    for i in range(12):
        frame = (i * 20) % 255
        img = frame * np.ones((64, 64, 3), dtype=np.uint8)
        out.write(img)
    out.release()

    detector = DeepfakeDetector()
    res = detector.analyze(vid)
    assert res.deepfake_score >= 0.0
    assert hasattr(res, "is_suspected")
    assert res.confidence >= 0.0
