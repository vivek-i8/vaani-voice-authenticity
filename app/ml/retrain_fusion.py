"""VAANI fusion-head retraining script.

Trains the fusion head on the TRAIN partition of the leakage-safe split.
Tuning uses VALIDATION only. TEST is never touched during training.

Architecture (matches app/ml/fusion_head.py exactly):
  Linear(1027,256) -> ReLU -> Dropout(0.2) -> Linear(256,128) -> ReLU -> Dropout(0.2) -> Linear(128,2)

Input: concatenated vector of [wav2vec2-large-xlsr-53 embedding (1024-dim) + 3 acoustic features]
Output: 2-class logits (index 0 = bona fide/Human, index 1 = spoof/AI)

Usage:
    python -m app.ml.retrain_fusion --split data/splits/in_the_wild_speaker_split.json \
        --train-cap 7000 --val-cap 2000 --patience 8

Compute strategy (Source of Truth, Section 5 amendment): trains on a
deterministic, speaker-aware, class-balanced subset of TRAIN by default
(--train-cap). Omit the caps only when measured validation results justify
full-partition training. Early stopping via --patience; the best validation
checkpoint is always kept regardless.
"""
import argparse
import json
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset
import numpy as np
import librosa
from datetime import datetime
from typing import List, Tuple

from app.ml.fusion_head import FusionHead
from app.ml.acoustic_features import extract_acoustic_features
from app.ml.embedding_cache import EmbeddingCache, get_feature_extractor_config_hash
from app.ml.subset_selection import select_balanced_subset, subset_stats
from app.core.device import DEVICE


def _collect_clips_and_labels(
    split_partition: dict, dataset_dir: str
) -> Tuple[List[str], List[int]]:
    """Extract file paths and integer labels from a split partition.

    Split format (from create_dataset_split.py):
        split["train"][speaker_id] = {"speaker": str, "clips": [{"file": str, "label": str}]}

    Args:
        split_partition: dict mapping speaker_id -> {"speaker": str, "clips": list}
        dataset_dir: base directory containing the WAV files

    Returns:
        (file_paths, labels) where labels are 0=bonafide, 1=spoof
    """
    files: List[str] = []
    labels: List[int] = []
    for speaker_id, speaker_data in split_partition.items():
        clips = speaker_data["clips"]
        for clip in clips:
            # clip["file"] is relative filename like "0.wav"
            files.append(clip["file"])
            labels.append(0 if clip["label"] == "bonafide" else 1)
    return files, labels


class FusionDataset(Dataset):
    """Dataset with precomputed scaled feature vectors."""

    def __init__(self, features: np.ndarray, labels: List[int]):
        self.features = torch.FloatTensor(features)
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        return self.features[idx], self.labels[idx]


def train_fusion_head(
    split_path: str,
    dataset_dir: str = "datasets/in_the_wild/release_in_the_wild",
    epochs: int = 50,
    batch_size: int = 16,
    learning_rate: float = 1e-4,
    output_dir: str = "models/vaani_model",
    train_cap: int | None = None,
    val_cap: int | None = None,
    patience: int | None = None,
):
    """Train fusion head on (a subset of) the TRAIN partition.

    Pipeline:
        1. Load split; apply deterministic class-balanced caps if provided
        2. Extract Wav2Vec2 embeddings via resumable cache (frozen backbone)
        3. Extract acoustic features (pitch_variance, spectral_drift, zcr_variance)
        4. Concatenate: [wav2vec2(1024) + acoustic(3)] = 1027-dim
        5. Fit StandardScaler on TRAIN only
        6. Transform TRAIN and VALIDATION through fitted scaler
        7. Train FusionHead on scaled TRAIN features with best-validation-
           checkpoint selection (+ patience-based early stopping if set)
        8. Save artifacts: fusion_head.pth, scaler.pkl, metadata.json
    """
    print(f"Loading split from {split_path}...")
    with open(split_path) as f:
        split = json.load(f)

    train_partition = split.get("train", {})
    val_partition = split.get("validation", {})

    if not train_partition:
        print("ERROR: No training data. Aborting.")
        return

    # Compute-strategy gate: default to a deterministic balanced subset.
    full_train_stats = subset_stats(train_partition)
    full_val_stats = subset_stats(val_partition)
    if train_cap is not None:
        train_partition = select_balanced_subset(train_partition, train_cap)
    if val_cap is not None and val_partition:
        val_partition = select_balanced_subset(val_partition, val_cap)
    train_subset_stats = subset_stats(train_partition)
    val_subset_stats = subset_stats(val_partition)
    print(
        f"Train subset: {train_subset_stats['clips']}/{full_train_stats['clips']} clips "
        f"({train_subset_stats['speakers']}/{full_train_stats['speakers']} speakers, "
        f"{train_subset_stats['bonafide']} bonafide / {train_subset_stats['spoof']} spoof)"
    )
    print(
        f"Val subset:   {val_subset_stats['clips']}/{full_val_stats['clips']} clips "
        f"({val_subset_stats['speakers']}/{full_val_stats['speakers']} speakers, "
        f"{val_subset_stats['bonafide']} bonafide / {val_subset_stats['spoof']} spoof)"
    )

    # Collect relative file paths and labels from split
    train_files, train_labels = _collect_clips_and_labels(train_partition, dataset_dir)
    val_files, val_labels = _collect_clips_and_labels(val_partition, dataset_dir)

    print(f"Train: {len(train_files)} clips ({sum(1 for l in train_labels if l==0)} bonafide, {sum(1 for l in train_labels if l==1)} spoof)")
    print(f"Val:   {len(val_files)} clips ({sum(1 for l in val_labels if l==0)} bonafide, {sum(1 for l in val_labels if l==1)} spoof)")

    # Step 1: Extract Wav2Vec2 embeddings via resumable cache
    print("\n--- Step 1: Extracting Wav2Vec2 embeddings (cached) ---")
    config_hash = get_feature_extractor_config_hash()
    print(f"  Config hash: {config_hash}")

    train_cache = EmbeddingCache(partition="train", config_hash=config_hash)
    val_cache = EmbeddingCache(partition="validation", config_hash=config_hash)

    train_embeddings = train_cache.get_or_compute(train_files, dataset_dir, batch_size=batch_size)
    print(f"  Train embeddings shape: {train_embeddings.shape}")

    val_embeddings = val_cache.get_or_compute(val_files, dataset_dir, batch_size=batch_size) if val_files else np.array([])
    if val_embeddings.size > 0:
        print(f"  Val embeddings shape: {val_embeddings.shape}")

    # Step 2: Extract acoustic features
    print("\n--- Step 2: Extracting acoustic features ---")
    train_acoustic = []
    for i, path in enumerate(train_files):
        if (i + 1) % 500 == 0:
            print(f"  Acoustic: {i+1}/{len(train_files)}")
        audio, sr = librosa.load(os.path.join(dataset_dir, path), sr=16000, mono=True)
        train_acoustic.append(extract_acoustic_features(audio, sr))
    train_acoustic = np.array(train_acoustic)
    print(f"  Train acoustic shape: {train_acoustic.shape}")

    val_acoustic_list = []
    if val_files:
        for path in val_files:
            audio, sr = librosa.load(os.path.join(dataset_dir, path), sr=16000, mono=True)
            val_acoustic_list.append(extract_acoustic_features(audio, sr))
    val_acoustic = np.array(val_acoustic_list) if val_acoustic_list else np.array([])

    # Step 3: Concatenate features [wav2vec2(1024) + acoustic(3)] = 1027-dim
    print("\n--- Step 3: Concatenating features ---")
    train_features = np.concatenate([train_embeddings, train_acoustic], axis=1)
    print(f"  Train features shape: {train_features.shape} (expected: N x 1027)")
    assert train_features.shape[1] == 1027, f"Expected 1027 features, got {train_features.shape[1]}"

    val_features = np.array([])
    if val_embeddings.size > 0 and val_acoustic.size > 0:
        val_features = np.concatenate([val_embeddings, val_acoustic], axis=1)
        print(f"  Val features shape: {val_features.shape}")

    # Step 4: Fit scaler on TRAIN only
    print("\n--- Step 4: Fitting StandardScaler on TRAIN ---")
    from sklearn.preprocessing import StandardScaler
    import joblib

    scaler = StandardScaler()
    scaler.fit(train_features)
    print(f"  Scaler fitted on {scaler.n_samples_seen_} training samples")
    print(f"  Feature means (first 5): {scaler.mean_[:5]}")
    print(f"  Feature stds (first 5): {scaler.scale_[:5]}")

    # Transform through fitted scaler
    train_scaled = scaler.transform(train_features)
    val_scaled = scaler.transform(val_features) if val_features.size > 0 else np.array([])

    # Save scaler immediately (before training, in case training fails)
    os.makedirs(output_dir, exist_ok=True)
    scaler_path = os.path.join(output_dir, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    print(f"  Scaler saved to {scaler_path}")

    # Step 5: Create datasets and train
    print(f"\n--- Step 5: Training FusionHead ---")
    print(f"  Architecture: Linear(1027,256)->ReLU->Dropout(0.2)->Linear(256,128)->ReLU->Dropout(0.2)->Linear(128,2)")
    print(f"  Device: {DEVICE}")
    print(f"  Epochs: {epochs}, Batch size: {batch_size}, LR: {learning_rate}")

    train_dataset = FusionDataset(train_scaled, train_labels)
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True
    )

    fusion_head = FusionHead(input_dim=1027, num_classes=2).to(DEVICE)
    optimizer = optim.Adam(fusion_head.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    # Training loop with best model tracking
    best_val_loss = float("inf")
    best_epoch = 0
    epochs_since_improvement = 0
    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        fusion_head.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for features_batch, labels in train_loader:
            features_batch = features_batch.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()
            logits = fusion_head(features_batch)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * features_batch.size(0)

            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        avg_loss = total_loss / total
        train_acc = correct / total
        train_losses.append(avg_loss)

        # Validation
        val_loss_str = ""
        val_acc_str = ""
        if val_scaled.size > 0:
            fusion_head.eval()
            val_dataset = FusionDataset(val_scaled, val_labels)
            val_loader = torch.utils.data.DataLoader(
                val_dataset, batch_size=batch_size
            )
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            with torch.no_grad():
                for features_batch, labels in val_loader:
                    features_batch = features_batch.to(DEVICE)
                    labels = labels.to(DEVICE)
                    logits = fusion_head(features_batch)
                    val_loss += criterion(logits, labels).item() * features_batch.size(0)
                    preds = logits.argmax(dim=1)
                    val_correct += (preds == labels).sum().item()
                    val_total += labels.size(0)
            val_loss /= val_total
            val_acc = val_correct / val_total
            val_losses.append(val_loss)
            val_loss_str = f", Val Loss: {val_loss:.4f}"
            val_acc_str = f", Val Acc: {val_acc:.4f}"

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch + 1
                epochs_since_improvement = 0
                # Save best model
                best_state = {k: v.cpu().clone() for k, v in fusion_head.state_dict().items()}
            else:
                epochs_since_improvement += 1

        if patience is not None and val_scaled.size > 0 and epochs_since_improvement >= patience:
            print(f"  Early stopping at epoch {epoch+1} (no val improvement for {patience} epochs)")
            break

        if (epoch + 1) % 5 == 0 or epoch == 0 or epoch == epochs - 1:
            print(f"  Epoch {epoch+1}/{epochs} | Train Loss: {avg_loss:.4f}, Train Acc: {train_acc:.4f}{val_loss_str}{val_acc_str}")

    # Load best model weights
    if best_epoch > 0:
        fusion_head.load_state_dict(best_state)
        print(f"\n  Best epoch: {best_epoch} (Val Loss: {best_val_loss:.4f})")

    # Step 6: Save model
    print("\n--- Step 6: Saving artifacts ---")
    model_path = os.path.join(output_dir, "fusion_head.pth")
    torch.save(fusion_head.state_dict(), model_path)
    print(f"  Model saved to {model_path}")

    # Step 7: Save metadata
    metadata = {
        "model_version": "vaani_v2_fusion",
        "training_date": datetime.now().isoformat(),
        "dataset": "In-the-Wild",
        "dataset_source": "https://huggingface.co/datasets/mueller91/In-The-Wild",
        "dataset_license": "cc-by-sa-4.0",
        "split_file": split_path,
        "architecture": {
            "input_dim": 1027,
            "layers": [256, 128, 2],
            "activation": "ReLU",
            "dropout": 0.2,
            "classes": ["bonafide", "spoof"],
            "class_mapping": {"bonafide": 0, "spoof": 1},
            "description": "Linear(1027,256)->ReLU->Dropout(0.2)->Linear(256,128)->ReLU->Dropout(0.2)->Linear(128,2)",
        },
        "feature_ordering": [
            *["wav2vec2_dim_{}".format(i) for i in range(1024)],
            "pitch_variance",
            "spectral_drift",
            "zcr_variance",
        ],
        "feature_dimensions": {
            "wav2vec2_embedding": 1024,
            "acoustic_features": 3,
            "total": 1027,
        },
        "backbone": "facebook/wav2vec2-large-xlsr-53 (frozen)",
        "training_params": {
            "epochs": epochs,
            "best_epoch": best_epoch,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "optimizer": "Adam",
            "criterion": "CrossEntropyLoss",
            "seed": 42,
            "patience": patience,
        },
        "compute_strategy": {
            "approach": "staged subset training (Source of Truth Section 5 amendment)",
            "train_cap": train_cap,
            "val_cap": val_cap,
            "train_subset_clips": train_subset_stats["clips"],
            "train_full_clips": full_train_stats["clips"],
            "val_subset_clips": val_subset_stats["clips"],
            "val_full_clips": full_val_stats["clips"],
        },
        "data": {
            "train_speakers": len(train_partition),
            "train_clips": len(train_files),
            "train_bonafide": sum(1 for l in train_labels if l == 0),
            "train_spoof": sum(1 for l in train_labels if l == 1),
            "val_speakers": len(val_partition),
            "val_clips": len(val_files),
            "val_bonafide": sum(1 for l in val_labels if l == 0),
            "val_spoof": sum(1 for l in val_labels if l == 1),
        },
        "metrics": {
            "best_val_loss": best_val_loss if best_epoch > 0 else None,
            "final_train_loss": train_losses[-1] if train_losses else None,
            "final_train_acc": train_acc if train_losses else None,
        },
        "scaler": {
            "type": "StandardScaler",
            "fitted_on": "TRAIN only",
            "n_samples": int(scaler.n_samples_seen_),
        },
        "preprocessing": {
            "sample_rate": 16000,
            "audio_format": "IEEE float WAV, mono",
            "wav2vec2_model": "facebook/wav2vec2-large-xlsr-53",
            "wav2vec2_method": "mean pooling of last_hidden_state",
            "acoustic_features": ["pitch_variance", "spectral_drift", "zcr_variance"],
            "normalization": "StandardScaler fitted on TRAIN",
        },
    }
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata saved to {metadata_path}")

    print("\n=== Training Complete ===")
    print(f"  Artifacts: {output_dir}/")
    print(f"    fusion_head.pth  ({os.path.getsize(os.path.join(output_dir, 'fusion_head.pth')) / 1024:.1f} KB)")
    print(f"    scaler.pkl       ({os.path.getsize(os.path.join(output_dir, 'scaler.pkl')) / 1024:.1f} KB)")
    print(f"    metadata.json")
    print(f"  Best val loss: {best_val_loss:.4f} (epoch {best_epoch})")
    print(f"  Final train acc: {train_acc:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train VAANI V2 fusion head")
    parser.add_argument(
        "--split",
        default="data/splits/in_the_wild_speaker_split.json",
        help="Path to the speaker-disjoint split JSON",
    )
    parser.add_argument(
        "--dataset-dir",
        default="datasets/in_the_wild/release_in_the_wild",
        help="Directory containing meta.csv and WAV files",
    )
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument(
        "--train-cap",
        type=int,
        default=None,
        help="Deterministic class-balanced TRAIN subset cap (recommended; e.g. 7000). Omit for full partition.",
    )
    parser.add_argument(
        "--val-cap",
        type=int,
        default=None,
        help="Deterministic VALIDATION subset cap (e.g. 2000). Omit for full partition.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=None,
        help="Early stopping patience (epochs without val improvement). Recommended: 8.",
    )
    parser.add_argument(
        "--output-dir",
        default="models/vaani_model",
        help="Directory to save trained model artifacts",
    )
    args = parser.parse_args()

    # Set deterministic seed
    torch.manual_seed(42)
    np.random.seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)

    train_fusion_head(
        args.split,
        args.dataset_dir,
        args.epochs,
        args.batch_size,
        args.lr,
        args.output_dir,
        train_cap=args.train_cap,
        val_cap=args.val_cap,
        patience=args.patience,
    )
