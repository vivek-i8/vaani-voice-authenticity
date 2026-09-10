"""GPU benchmark / pilot for VAANI V2 embedding extraction.

Compute-strategy gate (Source of Truth, Section 5 amendment; Master Plan,
Phase 3A): runs a small balanced pilot (300-500 clips) through the resumable
embedding cache on the local CUDA device and MEASURES real performance before
any large extraction or training is approved.

Measured:
- device actually used, effective batch size (incl. OOM fallback)
- clips/sec (end-to-end: disk decode + preprocess + GPU forward)
- peak VRAM (allocated + reserved)
- cache bytes on disk + projected size for larger runs
- time split between audio loading and GPU forward (bottleneck analysis)

Derived:
- estimated extraction time for 6K / 8K / 10K / full TRAIN (18,013) and full
  VALIDATION (5,140)
- recommended initial training-subset size

This script NEVER extracts the full TRAIN partition and never touches TEST or
REFERENCE-INDEX. It writes only its own pilot embeddings into the existing
resumable train cache (reused by later subset training).

Usage:
    python -m app.ml.benchmark_gpu --num-clips 400 --batch-size 16 \
        --split data/splits/in_the_wild_speaker_split.json
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from app.ml.embedding_cache import EmbeddingCache, EXTRACTION_STATS, get_feature_extractor_config_hash
from app.ml.subset_selection import select_balanced_subset, subset_stats
from app.core.device import DEVICE

REPORT_PATH = Path("models/vaani_model/benchmark_report.json")

# Candidate initial-training tiers (clips). The benchmark decides which tier
# is practical; 6K-8K is the expected range but not an assumption.
TRAIN_TIERS = [6000, 8000, 10000]

# Extraction-time budget (seconds) for the initial subset on this laptop.
INITIAL_EXTRACTION_BUDGET_S = 30 * 60


def _fmt_duration(seconds: float) -> str:
    if seconds < 90:
        return f"{seconds:.0f}s"
    minutes = seconds / 60
    if minutes < 90:
        return f"{minutes:.1f} min"
    return f"{minutes / 60:.2f} h"


def run_benchmark(
    num_clips: int,
    batch_size: int,
    split_path: str,
    dataset_dir: str,
) -> dict:
    print(f"Device: {DEVICE}", end="")
    if DEVICE.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        total_vram_gib = props.total_memory / 1024**3
        print(f" ({props.name}, {total_vram_gib:.1f} GiB VRAM)")
    else:
        print(" — WARNING: no CUDA device; numbers will not reflect the GPU target")

    with open(split_path) as f:
        split = json.load(f)
    partition = split.get("train", {})
    full_stats = subset_stats(partition)

    # Deterministic balanced pilot subset
    pilot = select_balanced_subset(partition, num_clips)
    pilot_files = [
        c["file"]
        for speaker_data in pilot.values()
        for c in sorted(speaker_data["clips"], key=lambda c: str(c["file"]))
    ]
    stats = subset_stats(pilot)
    print(
        f"Pilot subset: {stats['clips']} clips "
        f"({stats['bonafide']} bonafide / {stats['spoof']} spoof) "
        f"from {stats['speakers']}/{full_stats['speakers']} TRAIN speakers"
    )

    config_hash = get_feature_extractor_config_hash()
    print(f"Embedding config hash: {config_hash}")
    cache = EmbeddingCache(partition="train", config_hash=config_hash)
    already_cached = sum(1 for f in pilot_files if f in cache._load_manifest())

    # Warmup: first few clips absorb lazy model load / kernel autotune.
    warmup_n = min(8, len(pilot_files))
    warmup_files, timed_files = pilot_files[:warmup_n], pilot_files[warmup_n:]
    print(f"Warmup: {warmup_n} clips (untimed)...")
    cache.get_or_compute(warmup_files, dataset_dir, batch_size=batch_size)

    if DEVICE.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    EXTRACTION_STATS["load_seconds"] = 0.0
    EXTRACTION_STATS["forward_seconds"] = 0.0

    print(f"Benchmarking {len(timed_files)} clips at initial batch_size={batch_size}...")
    t0 = time.perf_counter()
    embs = cache.get_or_compute(timed_files, dataset_dir, batch_size=batch_size)
    wall_seconds = time.perf_counter() - t0

    if DEVICE.type == "cuda":
        torch.cuda.synchronize()

    assert embs.shape == (len(timed_files), 1024), (
        f"unexpected embedding shape {embs.shape}"
    )
    clips_per_sec = len(timed_files) / wall_seconds
    load_s = EXTRACTION_STATS["load_seconds"]
    fwd_s = EXTRACTION_STATS["forward_seconds"]

    peak_alloc = peak_reserved = None
    if DEVICE.type == "cuda":
        peak_alloc = torch.cuda.max_memory_allocated() / 1024**3
        peak_reserved = torch.cuda.max_memory_reserved() / 1024**3

    cache_bytes = cache.disk_bytes()
    n_cached_now = cache.size
    avg_bytes_per_clip = cache_bytes / n_cached_now if n_cached_now else 0
    per_clip_s = wall_seconds / len(timed_files)

    estimates = {}
    for label, n in [
        ("train_6000", 6000),
        ("train_8000", 8000),
        ("train_10000", 10000),
        ("train_full_18013", full_stats["clips"]),
        ("validation_full_5140", subset_stats(split["validation"])["clips"]),
    ]:
        est = max(0.0, n - already_cached - len(timed_files)) * per_clip_s
        estimates[label] = {
            "clips": n,
            "estimated_extraction_seconds": round(est, 1),
            "projected_cache_mb": round(n * avg_bytes_per_clip / 1024**2, 1),
        }

    # Recommendation: largest tier whose remaining-extraction estimate fits
    # within the budget; fall back to the smallest tier otherwise.
    feasible = [
        t
        for t in TRAIN_TIERS
        if estimates[f"train_{t}"]["estimated_extraction_seconds"]
        <= INITIAL_EXTRACTION_BUDGET_S
    ]
    recommended_tier = max(feasible) if feasible else min(TRAIN_TIERS)

    report = {
        "timestamp": datetime.now().isoformat(),
        "device": str(DEVICE),
        "gpu_name": torch.cuda.get_device_name(0) if DEVICE.type == "cuda" else None,
        "compute_dtype": "float16-autocast" if DEVICE.type == "cuda" else "float32",
        "requested_batch_size": batch_size,
        "effective_batch_size": cache.last_effective_batch_size,
        "oom_fallback_triggered": cache.last_effective_batch_size != batch_size,
        "pilot_clips_requested": num_clips,
        "pilot_clips_timed": len(timed_files),
        "pilot_already_cached": already_cached,
        "wall_seconds": round(wall_seconds, 2),
        "clips_per_sec": round(clips_per_sec, 2),
        "per_clip_seconds": round(per_clip_s, 4),
        "audio_load_seconds": round(load_s, 2),
        "gpu_forward_seconds": round(fwd_s, 2),
        "peak_vram_allocated_gib": round(peak_alloc, 3) if peak_alloc else None,
        "peak_vram_reserved_gib": round(peak_reserved, 3) if peak_reserved else None,
        "cache_total_mb": round(cache_bytes / 1024**2, 2),
        "cache_clip_count": n_cached_now,
        "avg_kb_per_clip": round(avg_bytes_per_clip / 1024, 1),
        "embedding_config_hash": config_hash,
        "estimates": estimates,
        "recommended_initial_train_subset": {
            "tier": recommended_tier,
            "rationale": (
                f"Largest candidate tier with estimated extraction "
                f"{_fmt_duration(estimates[f'train_{recommended_tier}']['estimated_extraction_seconds'])} "
                f"within the {_fmt_duration(INITIAL_EXTRACTION_BUDGET_S)} budget"
                if feasible
                else "No tier fits the budget; smallest tier chosen for the first staged run"
            ),
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    return report


def print_report(r: dict) -> None:
    print("\n=== VAANI V2 GPU Benchmark Report ===")
    print(f"Device:              {r['device']}" + (f" ({r['gpu_name']})" if r["gpu_name"] else ""))
    print(f"Compute dtype:       {r['compute_dtype']}")
    print(
        f"Batch size:          requested={r['requested_batch_size']} "
        f"effective={r['effective_batch_size']}"
        + (" (OOM fallback triggered)" if r["oom_fallback_triggered"] else "")
    )
    print(f"Pilot clips (timed): {r['pilot_clips_timed']} ({r['pilot_already_cached']} already cached)")
    print(f"Clips/sec:           {r['clips_per_sec']}")
    print(f"Per clip:            {r['per_clip_seconds']*1000:.1f} ms")
    if r["peak_vram_allocated_gib"] is not None:
        print(
            f"Peak VRAM:           {r['peak_vram_allocated_gib']} GiB allocated / "
            f"{r['peak_vram_reserved_gib']} GiB reserved"
        )
    print(f"Cache size:          {r['cache_total_mb']} MB over {r['cache_clip_count']} clips "
          f"(~{r['avg_kb_per_clip']} KB/clip)")
    total_split = r["audio_load_seconds"] + r["gpu_forward_seconds"]
    if total_split > 0:
        print(
            f"Bottleneck split:    audio load {r['audio_load_seconds']:.1f}s "
            f"({100*r['audio_load_seconds']/total_split:.0f}%) vs "
            f"GPU forward {r['gpu_forward_seconds']:.1f}s "
            f"({100*r['gpu_forward_seconds']/total_split:.0f}%)"
        )
    print("\nEstimated embedding extraction (remaining clips):")
    for label, e in r["estimates"].items():
        print(f"  {label:<22} {e['clips']:>6} clips -> {_fmt_duration(e['estimated_extraction_seconds']):>8} "
              f"| ~{e['projected_cache_mb']} MB cache")
    rec = r["recommended_initial_train_subset"]
    print(f"\nRecommended initial TRAIN subset: {rec['tier']} clips")
    print(f"Rationale: {rec['rationale']}")
    print(f"\nFull report written to {REPORT_PATH}")
    print("STOP: no full-partition extraction or training has been started.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VAANI V2 GPU benchmark/pilot")
    parser.add_argument("--num-clips", type=int, default=400)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--split", default="data/splits/in_the_wild_speaker_split.json"
    )
    parser.add_argument(
        "--dataset-dir", default="datasets/in_the_wild/release_in_the_wild"
    )
    args = parser.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)

    report = run_benchmark(
        num_clips=args.num_clips,
        batch_size=args.batch_size,
        split_path=args.split,
        dataset_dir=args.dataset_dir,
    )
    print_report(report)
