"""Watermark analysis module

Implements visible watermark detection and simple tampering checks using
OpenCV image processing and frequency-domain analysis (DCT). The API
returns a structured result with a tampering score and confidence so the
`core/risk_engine.py` can combine it into the final forensic score.
"""

import os
import math
import cv2
import numpy as np
from typing import Dict


def _frame_dct_energy(gray: np.ndarray) -> float:
    # Compute block-wise DCT and return normalized high-frequency energy
    h, w = gray.shape
    # Resize to multiple of 8 for block DCT
    nh = (h // 8) * 8
    nw = (w // 8) * 8
    if nh == 0 or nw == 0:
        return 0.0
    gray = cv2.resize(gray, (nw, nh))

    total_energy = 0.0
    hf_energy = 0.0
    for y in range(0, nh, 8):
        for x in range(0, nw, 8):
            block = np.float32(gray[y:y+8, x:x+8])
            dct = cv2.dct(block)
            total_energy += np.sum(np.abs(dct))
            # high-frequency components (upper-right triangle excluding DC)
            hf = dct[3:, 3:]
            hf_energy += np.sum(np.abs(hf))

    if total_energy == 0:
        return 0.0
    return float(hf_energy / total_energy)


def _detect_visible_watermark(frame_gray: np.ndarray, template: np.ndarray = None) -> float:
    # If template provided, use template matching score (normalized)
    if template is not None:
        try:
            res = cv2.matchTemplate(frame_gray, template, cv2.TM_CCOEFF_NORMED)
            _, maxval, _, _ = cv2.minMaxLoc(res)
            return float(maxval)
        except Exception:
            return 0.0

    # Heuristic: detect high-contrast logos/text in border regions
    h, w = frame_gray.shape
    border = frame_gray[ int(h*0.85): h, int(w*0.05): int(w*0.95) ]
    # edge density
    edges = cv2.Canny(border, 100, 200)
    edge_density = float(np.sum(edges > 0) / edges.size)
    return min(1.0, edge_density * 10)


def analyze_watermark(video_path: str, template_path: str = None, sample_rate: int = 30) -> Dict:
    """Analyze the video for watermark presence and tampering.

    Returns:
      {
        "watermark_present_score": 0-100,
        "tampering_score": 0-100,
        "is_suspected": bool,
        "confidence": 0-1
      }
    """
    if not os.path.exists(video_path):
        return {
            "watermark_present_score": 0,
            "tampering_score": 0,
            "is_suspected": False,
            "confidence": 0.0,
        }

    template = None
    if template_path and os.path.exists(template_path):
        timg = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if timg is not None:
            template = timg

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "watermark_present_score": 0,
            "tampering_score": 0,
            "is_suspected": False,
            "confidence": 0.0,
        }

    frame_idx = 0
    pres_scores = []
    tamper_scores = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_rate != 0:
            frame_idx += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        present_score = _detect_visible_watermark(gray, template)
        dct_energy = _frame_dct_energy(gray)

        # Tampering heuristic: unusually low HF energy or inconsistent watermark presence
        tamper_score = 0.0
        if present_score < 0.2 and dct_energy < 0.02:
            tamper_score = 0.9
        else:
            # moderate tampering risk proportional to changes in dct energy
            tamper_score = min(1.0, dct_energy * 5)

        pres_scores.append(present_score)
        tamper_scores.append(tamper_score)

        frame_idx += 1

    cap.release()

    if len(pres_scores) == 0:
        return {
            "watermark_present_score": 0,
            "tampering_score": 0,
            "is_suspected": False,
            "confidence": 0.0,
        }

    present_mean = float(sum(pres_scores) / len(pres_scores))
    tamper_mean = float(sum(tamper_scores) / len(tamper_scores))

    watermark_present_score = int(round(present_mean * 100))
    tampering_score = int(round(tamper_mean * 100))

    # Final suspicion rule: tampering_score > 50 or inconsistent watermark presence
    is_suspected = tampering_score >= 50 or (watermark_present_score < 30 and tampering_score >= 30)

    # Confidence: higher when template matched or strong DCT signal
    confidence = 0.5 + min(0.45, present_mean * 0.5 + tamper_mean * 0.5)

    return {
        "watermark_present_score": watermark_present_score,
        "tampering_score": tampering_score,
        "is_suspected": bool(is_suspected),
        "confidence": round(float(confidence), 2),
    }
