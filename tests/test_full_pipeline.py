"""End-to-end integration test for the full forensics analysis pipeline."""

import os
import tempfile
import cv2
import numpy as np

from piracyguard.core.detection_engine import DetectionEngine, ForensicAnalysis
from piracyguard.core.fingerprint.engine import FingerprintEngine


def test_full_forensics_pipeline():
    tmp = tempfile.mkdtemp()
    
    # 1. Create a reference original video (15 frames)
    ref_vid_path = os.path.join(tmp, "reference.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(ref_vid_path, fourcc, 5.0, (128, 128))
    for i in range(15):
        # Draw a moving square to generate motion/temporal variations
        img = np.zeros((128, 128, 3), dtype=np.uint8)
        cv2.rectangle(img, (i * 4, 30), (i * 4 + 20, 50), (255, 255, 255), -1)
        out.write(img)
    out.release()

    # 2. Create a slightly altered duplicate video (pirated copy)
    copy_vid_path = os.path.join(tmp, "copy_pirated.mp4")
    out = cv2.VideoWriter(copy_vid_path, fourcc, 5.0, (128, 128))
    for i in range(15):
        img = np.zeros((128, 128, 3), dtype=np.uint8)
        cv2.rectangle(img, (i * 4, 30), (i * 4 + 20, 50), (255, 255, 255), -1)
        # Add a watermarked overlay block in the top-right corner to test overlay detection
        cv2.rectangle(img, (100, 10), (120, 20), (200, 200, 200), -1)
        out.write(img)
    out.release()

    # 3. Initialize engine
    engine = DetectionEngine()

    # 4. Generate and register reference fingerprint
    ref_fp = engine.fp_engine.generate(ref_vid_path, step=5)
    assert ref_fp is not None
    assert ref_fp.frame_count > 0

    known_references = {
        ref_vid_path: ref_fp
    }

    # 5. Run full check on the copy video
    analysis = engine.check_video(copy_vid_path, known_references, step=5)

    # 6. Verify full ForensicAnalysis profile outputs
    assert isinstance(analysis, ForensicAnalysis)
    assert analysis.video_path == copy_vid_path
    assert analysis.duration_seconds > 0
    assert analysis.similarity_score > 50.0  # High similarity to reference
    assert analysis.matched_video_path == ref_vid_path

    # Verify deepfake output
    assert hasattr(analysis.deepfake, "deepfake_score")
    
    # Verify watermark output
    assert hasattr(analysis.watermark, "watermark_present_score")
    
    # Verify metadata output
    assert analysis.metadata.video_path == copy_vid_path
    
    # Verify risk outputs
    assert analysis.risk.risk_score >= 0.0
    assert analysis.risk.recommended_action != ""

    print("\nE2E Pipeline Integration Test Passed!")
    print(f"Match Similarity: {analysis.similarity_score}%")
    print(f"Risk Score: {analysis.risk.risk_score} ({analysis.risk.risk_level.value})")
    print(f"Recommended Action: {analysis.risk.recommended_action}")
