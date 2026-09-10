"""Build reference evidence index from REFERENCE-INDEX speakers.

Creates: models/vaani_model/reference_index.npz

The index contains L2-normalized Wav2Vec2 embeddings for brute-force
cosine similarity retrieval. No vector database needed.

Usage:
    python -m app.ml.build_reference_index --split data/splits/in_the_wild_speaker_split.json
"""

import argparse
import json
import os
import numpy as np
import torch
import librosa
from typing import List, Dict

from app.ml.model_loader import initialize_models, get_wav2vec_model, get_feature_extractor
from app.core.device import DEVICE

DATASET_DIR = "datasets/in_the_wild/release_in_the_wild"

MIN_REFERENCE_SIMILARITY = 0.5


def build_reference_index(
    split_path: str,
    output_path: str = "models/vaani_model/reference_index.npz",
    sr: int = 16000,
):
    """Build the reference index from REFERENCE-INDEX speakers."""
    print(f"Loading split from {split_path}...")
    with open(split_path) as f:
        split = json.load(f)

    ref_data = split.get("reference_index", {})
    if not ref_data:
        print("WARNING: No reference speakers. Creating empty index.")
        np.savez_compressed(output_path, embeddings=np.array([]), labels=np.array([]),
                          source_ids=np.array([]), speaker_ids=np.array([]))
        return

    # Initialize models
    print("Loading models...")
    initialize_models()
    wav2vec = get_wav2vec_model()
    feat_ext = get_feature_extractor()

    if wav2vec is None or feat_ext is None:
        print("ERROR: Wav2Vec2 model not loaded")
        return

    embeddings = []
    labels = []
    source_ids = []
    speaker_ids = []

    total_clips = sum(len(clips) for clips in ref_data.values())
    print(f"Processing {total_clips} clips from {len(ref_data)} speakers...")

    for speaker_id, speaker_data in ref_data.items():
        clips = speaker_data["clips"]
        for clip in clips:
            try:
                audio_path = os.path.join(DATASET_DIR, clip["file"])
                audio, _ = librosa.load(audio_path, sr=sr, mono=True)

                with torch.no_grad():
                    inputs = feat_ext(audio, sampling_rate=sr, return_tensors="pt")
                    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
                    outputs = wav2vec(**inputs)
                    emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

                # L2 normalize
                emb = emb / (np.linalg.norm(emb) + 1e-8)

                embeddings.append(emb)
                labels.append(clip["label"])
                source_ids.append(clip.get("file", "unknown"))
                speaker_ids.append(speaker_id)
            except Exception as e:
                print(f"  Skipping {clip.get('file', '?')}: {e}")

    # Save index
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    np.savez_compressed(
        output_path,
        embeddings=np.array(embeddings),
        labels=np.array(labels),
        source_ids=np.array(source_ids),
        speaker_ids=np.array(speaker_ids),
    )
    print(f"Reference index saved to {output_path} ({len(embeddings)} entries)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="data/splits/in_the_wild_speaker_split.json")
    parser.add_argument("--output", default="models/vaani_model/reference_index.npz")
    args = parser.parse_args()
    build_reference_index(args.split, args.output)
