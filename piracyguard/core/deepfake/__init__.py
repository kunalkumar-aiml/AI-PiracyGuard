"""Deepfake detection modules for media forensics.

Provides face extraction, deep neural network inference (EfficientNet-B4,
XceptionNet, ResNet18), and visual localization of manipulations via GradCAM.
"""

from piracyguard.core.deepfake.detector import DeepfakeDetector, DeepfakeResult

__all__ = [
    "DeepfakeDetector",
    "DeepfakeResult",
]
