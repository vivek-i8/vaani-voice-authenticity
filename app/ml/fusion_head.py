import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

class FusionHead(nn.Module):
    """
    Fusion-based classifier head for Vaani.
    
    Architecture: Linear → ReLU → Linear → Softmax
    
    Input: wav2vec_embedding (768-dim) + 3 acoustic features
    Output: 3-class classification (Human/AI/Inconclusive)
    """
    
    def __init__(self, embedding_dim: int = 768, num_classes: int = 3):
        super().__init__()
        
        # Input dimension: wav2vec embedding + 3 acoustic features
        input_dim = embedding_dim + 3
        
        # Fusion head architecture
        self.fc1 = nn.Linear(input_dim, 256)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, num_classes)
        self.dropout = nn.Dropout(0.2)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights for better training stability."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, wav2vec_embedding: torch.Tensor, acoustic_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through fusion head.
        
        Args:
            wav2vec_embedding: (batch_size, embedding_dim)
            acoustic_features: (batch_size, 3) - [pitch_var, spectral_drift, zcr_var]
            
        Returns:
            logits: (batch_size, num_classes)
            entropy: (batch_size,) - uncertainty measure
        """
        # Concatenate wav2vec embedding with acoustic features
        combined_features = torch.cat([wav2vec_embedding, acoustic_features], dim=1)
        
        # Forward through fusion layers
        x = self.fc1(combined_features)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.dropout(x)
        logits = self.fc3(x)
        
        # Compute entropy as uncertainty measure
        probs = F.softmax(logits, dim=1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-8), dim=1)
        
        return logits, entropy
    
    def predict_with_uncertainty(self, wav2vec_embedding: torch.Tensor, acoustic_features: torch.Tensor) -> dict:
        """
        Make prediction with uncertainty handling.
        
        Returns:
            {
                "label": "Human" | "AI" | "Inconclusive",
                "confidence": float,
                "entropy": float,
                "signals": {
                    "pitch_variance": float,
                    "spectral_drift": float,
                    "zcr_variance": float
                }
            }
        """
        logits, entropy = self.forward(wav2vec_embedding, acoustic_features)
        probs = F.softmax(logits, dim=1)
        
        # Get predicted class and confidence
        pred_class = torch.argmax(probs, dim=1)
        confidence = torch.max(probs, dim=1)[0]
        
        # Map class indices to labels
        class_labels = ["Human", "AI", "Inconclusive"]
        predicted_label = class_labels[pred_class.item()]
        
        # Determine if inconclusive based on entropy threshold
        entropy_value = entropy.item()
        if entropy_value > 0.65:
            predicted_label = "Inconclusive"
        
        return {
            "label": predicted_label,
            "confidence": confidence.item(),
            "entropy": entropy_value,
            "signals": {
                "pitch_variance": acoustic_features[0].item() if acoustic_features.dim() > 0 else 0.0,
                "spectral_drift": acoustic_features[1].item() if acoustic_features.dim() > 0 else 0.0,
                "zcr_variance": acoustic_features[2].item() if acoustic_features.dim() > 0 else 0.0
            }
        }
