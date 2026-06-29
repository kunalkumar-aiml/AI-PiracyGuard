"""PyTorch deepfake detection model architectures.

Implements a unified interface for model loading and batch inference,
supporting ResNet18, Xception, and EfficientNet-B4.
"""

from abc import ABC, abstractmethod
import os
from typing import List, Optional, Type, Union

from PIL import Image
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

from piracyguard.exceptions import ModelLoadError, ModelInferenceError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


# ── Unified Preprocessing ───────────────────────────────────────────

def get_preprocessing_transforms() -> transforms.Compose:
    """Standard preprocessing transforms for ImageNet-trained backbones."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


class BaseDeepfakeModel(nn.Module, ABC):
    """Abstract base class for all deepfake detection backbones.

    Integrates standard serialization and device routing.
    """

    def __init__(self, device: Optional[str] = None) -> None:
        super().__init__()
        # Determine execution device
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.transform = get_preprocessing_transforms()

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Standard PyTorch forward pass."""
        pass

    def load_weights(self, weights_path: str) -> None:
        """Load state dict weights from file.

        Args:
            weights_path: Path to the .pth or .pt weight file.
        """
        if not os.path.exists(weights_path):
            raise ModelLoadError(
                self.__class__.__name__,
                reason=f"Weight file not found: {weights_path}"
            )

        try:
            state_dict = torch.load(weights_path, map_location=self.device)
            self.load_state_dict(state_dict)
            self.to(self.device)
            self.eval()
            logger.info(
                f"Loaded custom weights for {self.__class__.__name__}",
                extra={"weights_path": weights_path, "device": str(self.device)}
            )
        except Exception as e:
            raise ModelLoadError(self.__class__.__name__, reason=str(e))

    def predict_batch(self, faces: List[Image.Image]) -> List[float]:
        """Perform batch inference on extracted faces.

        Args:
            faces: List of face crops as PIL Images.

        Returns:
            List of deepfake probabilities [0.0 - 1.0].
        """
        if not faces:
            return []

        try:
            # Preprocess all faces
            tensors = [self.transform(face) for face in faces]
            # Stack into a batch [Batch, Channel, Height, Width]
            batch_tensor = torch.stack(tensors).to(self.device)

            self.eval()
            with torch.no_grad():
                outputs = self.forward(batch_tensor)
                # Map outputs to probabilities (sigmoid)
                probs = torch.sigmoid(outputs).squeeze(-1)

                # Handle single-element list case vs multi-element
                if len(faces) == 1:
                    return [float(probs.item())]
                return probs.cpu().numpy().tolist()

        except Exception as e:
            logger.error(
                f"Model inference failed: {e}",
                extra={"model": self.__class__.__name__},
                exc_info=True
            )
            raise ModelInferenceError(self.__class__.__name__, reason=str(e))


# ── ResNet18 Backbone ────────────────────────────────────────────────

class ResNet18Model(BaseDeepfakeModel):
    """ResNet18 backbone with a custom binary classifier head."""

    def __init__(self, device: Optional[str] = None, pretrained: bool = True) -> None:
        super().__init__(device=device)
        # Load torchvision ResNet18
        if pretrained:
            # Replaced deprecated 'pretrained' with 'weights'
            self.resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        else:
            self.resnet = models.resnet18(weights=None)

        # Replace standard fully connected layer with custom head for binary output
        num_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(num_features, 1)
        self.to(self.device)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.resnet(x)


# ── EfficientNet-B4 Backbone ─────────────────────────────────────────

class EfficientNetB4Model(BaseDeepfakeModel):
    """EfficientNet-B4 backbone optimized for high resolution face crops."""

    def __init__(self, device: Optional[str] = None, pretrained: bool = True) -> None:
        super().__init__(device=device)
        # Load torchvision EfficientNet-B4
        if pretrained:
            self.effnet = models.efficientnet_b4(weights=models.EfficientNet_B4_Weights.DEFAULT)
        else:
            self.effnet = models.efficientnet_b4(weights=None)

        # Replace standard classifier head
        # EfficientNet classifier has: classifier = nn.Sequential(nn.Dropout(...), nn.Linear(in_features, classes))
        in_features = self.effnet.classifier[1].in_features
        self.effnet.classifier = nn.Sequential(
            nn.Dropout(p=0.4, inplace=True),
            nn.Linear(in_features, 1)
        )
        self.to(self.device)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.effnet(x)


# ── Xception Backbone (Depthwise Separable Convolutions) ─────────────

class SeparableConv2d(nn.Module):
    """Depthwise Separable Convolution block used in Xception."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
        bias: bool = False
    ) -> None:
        super().__init__()
        self.depthwise = nn.Conv2d(
            in_channels,
            in_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            groups=in_channels,
            bias=bias
        )
        self.pointwise = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=1,
            stride=1,
            padding=0,
            bias=bias
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.depthwise(x)
        x = self.pointwise(x)
        return x


class XceptionBlock(nn.Module):
    """Single Xception residual block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        reps: int = 3,
        stride: int = 1,
        start_with_relu: bool = True,
        grow_first: bool = True
    ) -> None:
        super().__init__()

        # Skip connection path
        if out_channels != in_channels or stride != 1:
            self.skip = nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=1,
                stride=stride,
                bias=False
            )
            self.skipbn = nn.BatchNorm2d(out_channels)
        else:
            self.skip = None

        self.rep = nn.ModuleList()
        channels = in_channels

        for i in range(reps):
            if grow_first and i == 0:
                out_ch = out_channels
            elif not grow_first and i == reps - 1:
                out_ch = out_channels
            else:
                out_ch = channels

            if start_with_relu or i > 0:
                self.rep.append(nn.ReLU(inplace=True))

            self.rep.append(
                SeparableConv2d(channels, out_ch, kernel_size=3, padding=1)
            )
            self.rep.append(nn.BatchNorm2d(out_ch))
            channels = out_ch

        if stride != 1:
            self.rep.append(nn.ReLU(inplace=True))
            self.rep.append(
                SeparableConv2d(channels, out_channels, kernel_size=3, padding=1, stride=stride)
            )
            self.rep.append(nn.BatchNorm2d(out_channels))
            self.rep.append(nn.MaxPool2d(3, stride=2, padding=1))

    def forward(self, inp: torch.Tensor) -> torch.Tensor:
        x = inp
        for layer in self.rep:
            x = layer(x)

        if self.skip:
            skip = self.skipbn(self.skip(inp))
        else:
            skip = inp

        return x + skip


class XceptionModel(BaseDeepfakeModel):
    """Xception architecture modified for binary classification.

    Follows the structure of Chollet's Xception model, popular in deepfake research.
    """

    def __init__(self, device: Optional[str] = None) -> None:
        super().__init__(device=device)

        # Entry flow
        self.conv1 = nn.Conv2d(3, 32, 3, 2, 0, bias=False)
        self.bn1 = nn.BatchNorm2d(32)
        self.relu = nn.ReLU(inplace=True)

        self.conv2 = nn.Conv2d(32, 64, 3, bias=False)
        self.bn2 = nn.BatchNorm2d(64)

        self.block1 = XceptionBlock(64, 128, 2, 2, start_with_relu=False, grow_first=True)
        self.block2 = XceptionBlock(128, 256, 2, 2, start_with_relu=True, grow_first=True)
        self.block3 = XceptionBlock(256, 728, 2, 2, start_with_relu=True, grow_first=True)

        # Middle flow
        self.block4 = XceptionBlock(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block5 = XceptionBlock(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block6 = XceptionBlock(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block7 = XceptionBlock(728, 728, 3, 1, start_with_relu=True, grow_first=True)

        # Exit flow
        self.block8 = XceptionBlock(728, 1024, 2, 2, start_with_relu=True, grow_first=False)

        self.conv3 = SeparableConv2d(1024, 1536, 3, 1, 1)
        self.bn3 = nn.BatchNorm2d(1536)

        self.conv4 = SeparableConv2d(1536, 2048, 3, 1, 1)
        self.bn4 = nn.BatchNorm2d(2048)

        # Classifier head
        self.fc = nn.Linear(2048, 1)
        self.to(self.device)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Entry flow
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)

        # Middle flow
        x = self.block4(x)
        x = self.block5(x)
        x = self.block6(x)
        x = self.block7(x)

        # Exit flow
        x = self.block8(x)

        x = self.relu(self.bn3(self.conv3(x)))
        x = self.relu(self.bn4(self.conv4(x)))

        # Global Average Pooling
        x = nn.functional.adaptive_avg_pool2d(x, (1, 1))
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


# ── Model Registry Factory ───────────────────────────────────────────

def get_model(model_name: str, device: Optional[str] = None, pretrained: bool = True) -> BaseDeepfakeModel:
    """Factory to retrieve a configured deepfake model by name.

    Args:
        model_name: Name of architecture ('resnet18', 'xception', 'efficientnet-b4').
        device: Run device.
        pretrained: If True, load default pretrained weights (ImageNet).

    Returns:
        Configured BaseDeepfakeModel.
    """
    name = model_name.lower().strip()
    if name == "resnet18":
        return ResNet18Model(device=device, pretrained=pretrained)
    elif name == "efficientnet-b4":
        return EfficientNetB4Model(device=device, pretrained=pretrained)
    elif name == "xception":
        return XceptionModel(device=device)
    else:
        logger.warning(f"Unknown model name '{model_name}', falling back to ResNet18Model")
        return ResNet18Model(device=device, pretrained=pretrained)
