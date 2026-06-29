"""PyTorch neural network architectures for deepfake classification."""

from piracyguard.core.deepfake.models.base import (
    BaseDeepfakeModel,
    ResNet18Model,
    XceptionModel,
    EfficientNetB4Model,
    get_model,
)

__all__ = [
    "BaseDeepfakeModel",
    "ResNet18Model",
    "XceptionModel",
    "EfficientNetB4Model",
    "get_model",
]
