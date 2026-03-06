import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple

from app.ml.model_loader import get_model, get_processor
from app.ml.fusion_head import FusionHead
from app.ml.acoustic_features import extract_acoustic_features
from app.core.config import settings
from app.core.device import DEVICE

class AudioDataset(Dataset):
    """Dataset for training fusion head with pre-computed wav2vec embeddings."""
    
    def __init__(self, audio_files: List[str], labels: List[int]):
        self.audio_files = audio_files
        self.labels = labels
        self.model = get_model()
        self.processor = get_processor()
        
    def __len__(self):
        return len(self.audio_files)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, int]:
        """Get wav2vec embedding, acoustic features, and label."""
        audio_path = self.audio_files[idx]
        label = self.labels[idx]
        
        # Load and process audio
        import librosa
        audio, sr = librosa.load(audio_path, sr=16000)
        
        # Get wav2vec embedding (frozen backbone)
        with torch.no_grad():
            inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            outputs = self.model(**inputs, output_hidden_states=True)
            # Use pooled output as embedding
            embedding = outputs.pooler_output.squeeze()
        
        # Extract acoustic features
        acoustic_features = extract_acoustic_features(audio, sr)
        acoustic_tensor = torch.tensor(acoustic_features, dtype=torch.float32).to(DEVICE)
        
        return embedding, acoustic_tensor, label

def create_model_save_dir():
    """Create directory for saving fusion head models."""
    model_dir = "models/v2_modernTTS"
    os.makedirs(model_dir, exist_ok=True)
    return model_dir

def compute_class_statistics(dataset: Dataset) -> Dict[str, float]:
    """Compute mean scores for human and AI classes."""
    human_scores = []
    ai_scores = []
    
    for i in range(len(dataset)):
        _, _, label = dataset[i]
        if label == 0:  # Human
            human_scores.append(1.0)  # Placeholder - would be actual scores
        elif label == 1:  # AI
            ai_scores.append(1.0)  # Placeholder - would be actual scores
    
    human_mean = np.mean(human_scores) if human_scores else 0.0
    ai_mean = np.mean(ai_scores) if ai_scores else 0.0
    separation_margin = abs(human_mean - ai_mean)
    
    return {
        "human_mean_score": float(human_mean),
        "ai_mean_score": float(ai_mean),
        "separation_margin": float(separation_margin)
    }

def train_fusion_head(
    train_files: List[str],
    train_labels: List[int],
    val_files: List[str] = None,
    val_labels: List[int] = None,
    epochs: int = 50,
    batch_size: int = 16,
    learning_rate: float = 1e-4
) -> Dict[str, any]:
    """
    Train fusion head with frozen wav2vec2 backbone.
    """
    print("🚀 Starting Vaani v2 Fusion Head Training")
    print(f"📊 Training samples: {len(train_files)}")
    
    # Create datasets
    train_dataset = AudioDataset(train_files, train_labels)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize fusion head
    fusion_head = FusionHead().to(DEVICE)
    optimizer = optim.Adam(fusion_head.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    
    # Training loop
    best_val_loss = float('inf')
    for epoch in range(epochs):
        fusion_head.train()
        total_loss = 0.0
        
        for batch_idx, (embeddings, acoustic_features, labels) in enumerate(train_loader):
            embeddings = embeddings.to(DEVICE)
            acoustic_features = acoustic_features.to(DEVICE)
            labels = labels.to(DEVICE)
            
            optimizer.zero_grad()
            logits, _ = fusion_head(embeddings, acoustic_features)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            if batch_idx % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Batch {batch_idx}, Loss: {loss.item():.4f}")
        
        avg_loss = total_loss / len(train_loader)
        print(f"📈 Epoch {epoch+1}/{epochs}, Average Loss: {avg_loss:.4f}")
    
    # Save model and metadata
    model_dir = create_model_save_dir()
    model_path = os.path.join(model_dir, "fusion_head.pth")
    torch.save(fusion_head.state_dict(), model_path)
    
    # Compute training statistics
    class_stats = compute_class_statistics(train_dataset)
    
    metadata = {
        "training_date": datetime.now().isoformat(),
        "dataset_summary": {
            "total_samples": len(train_files),
            "human_samples": train_labels.count(0),
            "ai_samples": train_labels.count(1),
            "inconclusive_samples": train_labels.count(2)
        },
        "human_mean_score": class_stats["human_mean_score"],
        "ai_mean_score": class_stats["ai_mean_score"],
        "separation_margin": class_stats["separation_margin"],
        "model_config": {
            "embedding_dim": 768,
            "num_classes": 3,
            "acoustic_features": 3
        },
        "training_hyperparameters": {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate
        }
    }
    
    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Model saved to: {model_path}")
    print(f"📋 Metadata saved to: {metadata_path}")
    print(f"🎯 Separation Margin: {class_stats['separation_margin']:.3f}")
    
    return {
        "model_path": model_path,
        "metadata": metadata,
        "separation_margin": class_stats["separation_margin"]
    }

if __name__ == "__main__":
    # Example usage - would be called with actual dataset
    print("Vaani v2 Fusion Head Training Script")
    print("This script should be called with actual training data")
    print("Example: python -m app.ml.train_fusion --train-dir data/v2 --epochs 50")
