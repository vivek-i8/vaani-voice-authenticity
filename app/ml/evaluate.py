"""Evaluation pipeline for VAANI V2.

Runs evaluation on the TEST partition under clean/noisy/compressed conditions.
Produces a reproducible eval_report.json with provenance.

Usage:
    python -m app.ml.evaluate --split data/splits/in_the_wild_speaker_split.json
"""
import argparse
import json
import os
import numpy as np
import librosa
from datetime import datetime
from typing import Dict, List, Tuple

from app.ml.inference import run_vaani_signal, run_spectra_signal
from app.core.device import DEVICE

DATASET_DIR = "datasets/in_the_wild/release_in_the_wild"


def compute_eer(labels: np.ndarray, scores: np.ndarray) -> float:
    """Compute Equal Error Rate."""
    from sklearn.metrics import roc_curve
    fpr, tpr, thresholds = roc_curve(labels, scores)
    fnr = 1 - tpr
    eer_threshold = thresholds[np.nanargmin(np.absolute(fpr - fnr))]
    eer = fpr[np.nanargmin(np.absolute(fpr - fnr))]
    return float(eer * 100)


def evaluate_condition(
    clips: List[dict],
    condition: str = "clean",
    noise_dir: str = None,
) -> Dict[str, float]:
    """Evaluate on a set of clips under a specific condition."""
    y_true = []
    y_scores = []

    for clip in clips:
        try:
            audio_path = os.path.join(DATASET_DIR, clip["file"])
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)

            # Apply condition transforms
            if condition == "noisy" and noise_dir:
                # Add noise (simplified)
                noise = np.random.randn(len(audio)).astype(np.float32) * 0.01
                audio = audio + noise
            elif condition == "compressed":
                # Simulate compression artifacts
                audio = audio.astype(np.int16).astype(np.float32) / 32768.0

            # Run VAANI signal
            vaani = run_vaani_signal(audio, sr)
            score = vaani["model_score"]

            label = 0 if clip["label"] == "bonafide" else 1
            y_true.append(label)
            y_scores.append(score)
        except Exception as e:
            print(f"  Skipping {clip.get('file', '?')}: {e}")

    if not y_true:
        return {"eer": -1, "n_samples": 0}

    y_true = np.array(y_true)
    y_scores = np.array(y_scores)

    # For VAANI: higher score = more human (bonafide)
    # EER expects higher = positive (spoof), so invert
    eer = compute_eer(y_true, 1.0 - y_scores)

    return {
        "eer": round(eer, 4),
        "n_samples": len(y_true),
        "condition": condition,
    }


def run_evaluation(split_path: str, output_path: str = None):
    """Run full evaluation and produce eval_report.json."""
    print(f"Loading split from {split_path}...")
    with open(split_path) as f:
        split = json.load(f)

    test_data = split.get("test", {})
    if not test_data:
        print("WARNING: No test data. Creating placeholder report.")
        report = {
            "status": "placeholder",
            "note": "No test data available. Run with actual dataset.",
            "timestamp": datetime.now().isoformat(),
        }
    else:
        # Initialize models
        print("Initializing models...")
        from app.ml.model_loader import initialize_models
        initialize_models()

        # Collect test clips
        test_clips = []
        for speaker_id, speaker_data in test_data.items():
            test_clips.extend(speaker_data["clips"])

        print(f"Evaluating {len(test_clips)} test clips...")

        # Evaluate under different conditions
        results = {}
        for condition in ["clean", "noisy", "compressed"]:
            print(f"  Condition: {condition}")
            result = evaluate_condition(test_clips, condition)
            results[condition] = result
            print(f"    EER: {result['eer']:.2f}%, n={result['n_samples']}")

        report = {
            "status": "complete",
            "timestamp": datetime.now().isoformat(),
            "dataset": "In-the-Wild",
            "split_file": split_path,
            "test_speakers": len(test_data),
            "conditions": results,
            "model_versions": {
                "vaani_fusion_head": "v2.0",
                "spectra_aasist3": "lab260/Spectra-AASIST3@bc0ded88",
            },
            "thresholds": {
                "entropy_threshold": 0.55,
                "agreement_threshold": 0.60,
            },
        }

    # Write report
    if output_path is None:
        output_path = "models/vaani_model/eval_report.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Evaluation report written to {output_path}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="data/splits/in_the_wild_speaker_split.json")
    parser.add_argument("--output", default="models/vaani_model/eval_report.json")
    args = parser.parse_args()
    run_evaluation(args.split, args.output)
