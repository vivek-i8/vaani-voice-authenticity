"""Generate speaker-disjoint 4-way split for In-the-Wild dataset.

Creates: data/splits/in_the_wild_speaker_split.json

The split ensures:
1. No speaker appears in more than one partition
2. Four partitions: train, validation, test, reference_index
3. reference_index speakers are excluded from train/val/test
4. Leakage assertions run and fail loudly if violated

Dataset structure (In-the-Wild from HuggingFace mueller91/In-The-Wild):
    datasets/in_the_wild/release_in_the_wild/
    ├── meta.csv          (file,speaker,label)
    ├── attribution.txt
    └── *.wav             (flat directory, files named 0.wav, 1.wav, ...)

Usage:
    python -m app.ml.create_dataset_split \
        --dataset-dir datasets/in_the_wild/release_in_the_wild \
        --output data/splits/in_the_wild_speaker_split.json
"""
import argparse
import csv
import json
import os
import random
from collections import defaultdict


def load_meta(dataset_dir: str) -> list[dict]:
    """Load meta.csv from the In-the-Wild dataset.

    Returns list of dicts with keys: file, speaker, label.
    Labels in the dataset are 'bona-fide' and 'spoof'.
    """
    meta_path = os.path.join(dataset_dir, "meta.csv")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(
            f"meta.csv not found in {dataset_dir}. "
            f"Expected the extracted In-the-Wild dataset at this path."
        )

    with open(meta_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Normalize labels: bona-fide -> bonafide (our internal convention)
    for row in rows:
        raw_label = row["label"].strip().lower()
        if raw_label in ("bona-fide", "bonafide", "real", "genuine"):
            row["label"] = "bonafide"
        elif raw_label in ("spoof", "fake", "synthetic", "ai"):
            row["label"] = "spoof"
        else:
            row["label"] = raw_label  # keep as-is for unknown

    return rows


def validate_files_exist(rows: list[dict], dataset_dir: str) -> int:
    """Check that all referenced WAV files exist. Returns count of missing."""
    missing = []
    for row in rows:
        fpath = os.path.join(dataset_dir, row["file"])
        if not os.path.exists(fpath):
            missing.append(row["file"])
    return missing


def generate_split(
    dataset_dir: str,
    output_path: str,
    reference_speakers: int = 6,
    seed: int = 42,
    min_clips_per_speaker: int = 10,
):
    """Generate the 4-way speaker-disjoint split.

    Args:
        dataset_dir: Path containing meta.csv and *.wav files
        output_path: Path to write the split JSON
        reference_speakers: Number of speakers to reserve for reference index
        seed: Random seed for reproducibility
        min_clips_per_speaker: Minimum clips a speaker must have to be included
    """
    random.seed(seed)

    print(f"Loading metadata from {dataset_dir}/meta.csv ...")
    rows = load_meta(dataset_dir)
    print(f"  Total clips in meta.csv: {len(rows)}")

    # Verify files exist
    missing = validate_files_exist(rows, dataset_dir)
    if missing:
        print(f"  WARNING: {len(missing)} files missing from disk")
        if len(missing) <= 5:
            print(f"    Missing: {missing}")
    else:
        print(f"  All {len(rows)} WAV files verified on disk")

    # Group by speaker
    speakers: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        speakers[row["speaker"]].append({
            "file": row["file"],
            "label": row["label"],
        })

    print(f"\n  Unique speakers: {len(speakers)}")
    for spk, clips in sorted(speakers.items(), key=lambda x: -len(x[1])):
        n_bf = sum(1 for c in clips if c["label"] == "bonafide")
        n_sp = sum(1 for c in clips if c["label"] == "spoof")
        print(f"    {spk}: {len(clips)} clips (bonafide={n_bf}, spoof={n_sp})")

    # Filter by minimum clips
    eligible = {
        sid: clips for sid, clips in speakers.items()
        if len(clips) >= min_clips_per_speaker
    }
    excluded = {sid: clips for sid, clips in speakers.items()
                if len(clips) < min_clips_per_speaker}

    print(f"\n  Eligible speakers (>= {min_clips_per_speaker} clips): {len(eligible)}")
    if excluded:
        print(f"  Excluded speakers (< {min_clips_per_speaker} clips): {len(excluded)}")
        for sid, clips in sorted(excluded.items()):
            print(f"    {sid}: {len(clips)} clips")

    # Deterministic shuffle
    speaker_ids = list(eligible.keys())
    random.shuffle(speaker_ids)

    # Assign: first N speakers -> reference_index
    reference = speaker_ids[:reference_speakers]
    remaining = speaker_ids[reference_speakers:]

    # Split remaining: 70% train, 15% val, 15% test
    n = len(remaining)
    train_end = int(n * 0.70)
    val_end = train_end + int(n * 0.15)

    train_speakers = remaining[:train_end]
    val_speakers = remaining[train_end:val_end]
    test_speakers = remaining[val_end:]

    split = {
        "metadata": {
            "dataset": "In-the-Wild",
            "source": "https://huggingface.co/datasets/mueller91/In-The-Wild",
            "license": "cc-by-sa-4.0",
            "seed": seed,
            "reference_speakers_count": reference_speakers,
            "total_speakers": len(speaker_ids),
            "total_clips": len(rows),
            "eligible_speakers": len(eligible),
            "train_speakers": len(train_speakers),
            "val_speakers": len(val_speakers),
            "test_speakers": len(test_speakers),
            "reference_speakers_count_actual": len(reference),
            "min_clips_per_speaker": min_clips_per_speaker,
            "label_convention": "bonafide/spoof (normalized from bona-fide/spoof)",
        },
        "train": {
            sid: {
                "speaker": sid,
                "clips": eligible[sid],
            }
            for sid in train_speakers
        },
        "validation": {
            sid: {
                "speaker": sid,
                "clips": eligible[sid],
            }
            for sid in val_speakers
        },
        "test": {
            sid: {
                "speaker": sid,
                "clips": eligible[sid],
            }
            for sid in test_speakers
        },
        "reference_index": {
            sid: {
                "speaker": sid,
                "clips": eligible[sid],
            }
            for sid in reference
        },
    }

    # === Leakage assertions ===
    print("\n=== Leakage / Disjointness Assertions ===")
    assert_no_leakage(split)

    # === Print partition statistics ===
    print("\n=== Partition Statistics ===")
    total_speakers_accounted = 0
    total_clips_accounted = 0

    for partition_name in ["train", "validation", "test", "reference_index"]:
        partition = split[partition_name]
        n_speakers = len(partition)
        all_clips = []
        for sid, data in partition.items():
            all_clips.extend(data["clips"])

        n_clips = len(all_clips)
        n_bonafide = sum(1 for c in all_clips if c["label"] == "bonafide")
        n_spoof = sum(1 for c in all_clips if c["label"] == "spoof")

        total_speakers_accounted += n_speakers
        total_clips_accounted += n_clips

        print(f"\n  {partition_name.upper()}:")
        print(f"    Speakers: {n_speakers}")
        print(f"    Clips:    {n_clips} (bonafide={n_bonafide}, spoof={n_spoof})")
        if n_clips > 0:
            print(f"    Ratio:    {n_bonafide/n_clips:.1%} bonafide, {n_spoof/n_clips:.1%} spoof")

    # Exclude speakers (below min_clips threshold)
    excluded_clips = sum(len(clips) for clips in excluded.values())
    total_speakers_accounted += len(excluded)
    total_clips_accounted += excluded_clips

    print(f"\n  EXCLUDED (below {min_clips_per_speaker} clips):")
    print(f"    Speakers: {len(excluded)}")
    print(f"    Clips:    {excluded_clips}")

    print(f"\n=== Totals ===")
    print(f"  Speakers accounted: {total_speakers_accounted} / {len(speakers)}")
    print(f"  Clips accounted:    {total_clips_accounted} / {len(rows)}")

    # Write split
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(split, f, indent=2)

    print(f"\nSplit written to {output_path}")
    return split


def assert_no_leakage(split: dict):
    """Verify no speaker appears in more than one partition. Fails loudly."""
    all_speakers: dict[str, str] = {}
    partitions = ["train", "validation", "test", "reference_index"]

    for partition_name in partitions:
        partition = split[partition_name]
        for speaker_id in partition:
            if speaker_id in all_speakers:
                raise AssertionError(
                    f"LEAKAGE DETECTED: Speaker '{speaker_id}' appears in both "
                    f"'{all_speakers[speaker_id]}' and '{partition_name}'"
                )
            all_speakers[speaker_id] = partition_name

    # Verify completeness
    total_in_split = sum(len(split[p]) for p in partitions)
    print(f"  [PASS] No speaker appears in more than one partition")
    print(f"  [PASS] {total_in_split} speakers assigned across 4 partitions (no duplicates)")

    # Cross-partition clip overlap check
    all_clip_files: dict[str, str] = {}
    for partition_name in partitions:
        partition = split[partition_name]
        for sid, data in partition.items():
            for clip in data["clips"]:
                fname = clip["file"]
                if fname in all_clip_files:
                    raise AssertionError(
                        f"CLIP LEAKAGE: File '{fname}' appears in both "
                        f"'{all_clip_files[fname]}' and '{partition_name}'"
                    )
                all_clip_files[fname] = partition_name

    total_clips = sum(
        len(clip)
        for p in partitions
        for sid, data in split[p].items()
        for clip in [data["clips"]]
    )
    print(f"  [PASS] No clip appears in more than one partition")
    print(f"  [PASS] {len(all_clip_files)} unique clips across all partitions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate speaker-disjoint 4-way split")
    parser.add_argument(
        "--dataset-dir",
        default="datasets/in_the_wild/release_in_the_wild",
        help="Directory containing meta.csv and *.wav files",
    )
    parser.add_argument(
        "--output",
        default="data/splits/in_the_wild_speaker_split.json",
    )
    parser.add_argument("--reference-speakers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-clips", type=int, default=10)
    args = parser.parse_args()
    generate_split(
        args.dataset_dir,
        args.output,
        args.reference_speakers,
        args.seed,
        args.min_clips,
    )
