"""Watermark detection and analysis modules.

Provides algorithms for visible overlay matching, invisible watermarking
(LSB/DWT), and frequency-domain tampering analysis (FFT/DCT).
"""

from piracyguard.core.watermark.analyzer import WatermarkAnalyzer, WatermarkResult

__all__ = [
    "WatermarkAnalyzer",
    "WatermarkResult",
]
