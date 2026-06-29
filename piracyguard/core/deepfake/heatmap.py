"""GradCAM heatmap generation for deepfake model interpretability.

Visualizes which parts of a face frame contributed most to the model's
classification score, generating a localized heatmap overlay.
"""

from typing import Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image

from piracyguard.core.deepfake.models.base import BaseDeepfakeModel
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


class GradCAM:
    """Computes GradCAM class activation maps for interpretability.

    Compatible with PyTorch models using CNN backbones.
    """

    def __init__(self, model: BaseDeepfakeModel, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self.gradients: torch.Tensor | None = None
        self.activations: torch.Tensor | None = None

        # Hook to capture gradients
        def save_gradient(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        # Hook to capture forward activations
        def save_activation(module, input, output):
            self.activations = output

        # Register hook handlers
        self.forward_hook = target_layer.register_forward_hook(save_activation)
        self.backward_hook = target_layer.register_full_backward_hook(save_gradient)

    def remove_hooks(self) -> None:
        """Remove PyTorch hooks to release memory."""
        self.forward_hook.remove()
        self.backward_hook.remove()

    def generate_heatmap(
        self,
        input_image: Image.Image,
        alpha: float = 0.4
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate a GradCAM heatmap overlay on the input image.

        Args:
            input_image: PIL Image of the face/frame.
            alpha: Transparency of the heatmap overlay (0.0 to 1.0).

        Returns:
            Tuple of (heatmap_only, blended_result) as RGB numpy arrays.
        """
        # Preprocess and prepare tensor
        preprocess = self.model.transform
        input_tensor = preprocess(input_image).unsqueeze(0).to(self.model.device)

        # Run forward pass
        self.model.eval()
        output = self.model(input_tensor)

        # Set gradients to zero
        self.model.zero_grad()

        # Backward pass for the single output node
        # Since it's a binary classifier, we backpropagate output directly
        output.backward()

        if self.gradients is None or self.activations is None:
            logger.warning("GradCAM failed to capture activations or gradients")
            # Return original image as fallback
            orig_np = np.array(input_image)
            return orig_np, orig_np

        # Extract gradients and activations
        gradients = self.gradients.cpu().data.numpy()[0]  # [Channel, Height, Width]
        activations = self.activations.cpu().data.numpy()[0]  # [Channel, Height, Width]

        # Global average pool the gradients
        weights = np.mean(gradients, axis=(1, 2))  # [Channel]

        # Compute weighted sum of activations
        cam = np.zeros(activations.shape[1:], dtype=np.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i, :, :]

        # Apply ReLU to keep only features that positively contribute to the class
        cam = np.maximum(cam, 0)

        # Normalize between 0 and 1
        if np.max(cam) > 0:
            cam = cam / np.max(cam)

        # Resize CAM to match original image size
        orig_width, orig_height = input_image.size
        cam_resized = cv2.resize(cam, (orig_width, orig_height))

        # Convert to colored heatmap (Jet colormap)
        heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        # Blend with original image
        original_np = np.array(input_image)
        # Handle grayscale original image edge case
        if len(original_np.shape) == 2:
            original_np = cv2.cvtColor(original_np, cv2.COLOR_GRAY2RGB)

        blended = cv2.addWeighted(original_np, 1.0 - alpha, heatmap, alpha, 0)

        return heatmap, blended
