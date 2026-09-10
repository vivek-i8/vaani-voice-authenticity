import torch
import torch.nn as nn
import torch.nn.functional as F


class FusionHead(nn.Module):
    """Fusion-based classifier head for VAANI V2.

    Architecture: Linear(1027,256) -> ReLU -> Dropout -> Linear(256,128) -> ReLU -> Dropout -> Linear(1027,2)
    Input: concatenated vector of [wav2vec2-large-xlsr-53 embedding (1024-dim) + 3 acoustic features]
    Output: 2-class logits (index 0 = bona fide/Human, index 1 = spoof/AI)

    Inconclusive is determined by entropy threshold in ensemble.py, not here.
    """

    def __init__(self, input_dim: int = 1027, num_classes: int = 2):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            features: (batch_size, input_dim) — concatenated wav2vec2 embedding + acoustic features

        Returns:
            logits: (batch_size, num_classes)
        """
        return self.network(features)

    def predict_proba(self, features: torch.Tensor) -> torch.Tensor:
        """Return softmax probabilities. Convenience method for inference."""
        logits = self.forward(features)
        return F.softmax(logits, dim=1)
