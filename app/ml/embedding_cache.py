"""Resumable, config-hashed Wav2Vec2 embedding cache for VAANI V2 training.

Cache design:
- Partition-aware: separate train/validation directories (never test/reference)
- Config-hashed: SHA256 of all parameters affecting embedding output,
  including compute precision (FP16 autocast on CUDA vs FP32 on CPU)
- Resumable: per-clip .npy files + manifest; the manifest is persisted
  incrementally after every processed batch, so an interrupted run keeps
  everything it already extracted
- Memory-efficient: streams writes, no full array in RAM
- Batched GPU extraction: torch.inference_mode(), FP16 autocast where safe
  (embeddings are cast back to float32 before caching), automatic OOM batch
  fallback 16 -> 8 -> 4 -> 2 -> 1

Compute-strategy note (Source of Truth, Section 5 amendment): this cache is
the only path to training embeddings. Large extractions must be justified by
app/ml/benchmark_gpu.py measurements first.
"""

import hashlib
import json
import os
import logging
import time
from pathlib import Path
from typing import Callable, List

import numpy as np
import torch

from app.core.device import DEVICE

logger = logging.getLogger(__name__)

CACHE_ROOT = Path("models/vaani_model/embeddings")

# Cumulative time spent in audio loading vs GPU forward pass. Used by the
# benchmark to identify the actual bottleneck (disk/decode vs GPU).
EXTRACTION_STATS = {"load_seconds": 0.0, "forward_seconds": 0.0}

WAV2VEC2_MODEL_NAME = "facebook/wav2vec2-large-xlsr-53"
SAMPLE_RATE = 16000
MAX_CLIP_SECONDS = 5.0

# Lazy singleton so batched extraction does not reload the frozen backbone
# from disk for every chunk.
_BACKBONE_CACHE: dict = {}


def _get_wav2vec2():
    """Load (once) and return (feature_extractor, frozen eval-mode Wav2Vec2Model)."""
    if "model" not in _BACKBONE_CACHE:
        from transformers import Wav2Vec2Model, Wav2Vec2FeatureExtractor

        feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
            WAV2VEC2_MODEL_NAME
        )
        wav2vec_model = Wav2Vec2Model.from_pretrained(WAV2VEC2_MODEL_NAME).to(DEVICE)
        for param in wav2vec_model.parameters():
            param.requires_grad = False
        wav2vec_model.eval()
        _BACKBONE_CACHE["extractor"] = feature_extractor
        _BACKBONE_CACHE["model"] = wav2vec_model
    return _BACKBONE_CACHE["extractor"], _BACKBONE_CACHE["model"]


def _compute_dtype_for_device(device: torch.device) -> str:
    """Precision actually used for GPU forward passes on this device."""
    return "float16" if device.type == "cuda" else "float32"


def compute_config_hash(
    wav2vec2_model_name: str,
    sample_rate: int,
    feature_extractor_config: dict,
    pooling_method: str,
    audio_duration_range: tuple[float, float],
    compute_dtype: str = "float32",
) -> str:
    """Compute deterministic SHA256 hash of embedding configuration.

    Includes compute precision: cached embeddings produced under FP16 autocast
    are not bit-compatible with FP32 ones, so a precision change invalidates.

    Returns:
        16-character hex string for cache directory naming.
    """
    config = {
        "wav2vec2_model_name": wav2vec2_model_name,
        "sample_rate": sample_rate,
        "feature_extractor_config": feature_extractor_config,
        "pooling_method": pooling_method,
        "audio_duration_range": audio_duration_range,
        "compute_dtype": compute_dtype,
    }
    # Sort keys for deterministic serialization
    config_json = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(config_json.encode()).hexdigest()[:16]


def get_feature_extractor_config_hash() -> str:
    """Get config hash from the actual feature extractor used in production."""
    from transformers import Wav2Vec2FeatureExtractor

    extractor = Wav2Vec2FeatureExtractor.from_pretrained(WAV2VEC2_MODEL_NAME)
    return compute_config_hash(
        wav2vec2_model_name=WAV2VEC2_MODEL_NAME,
        sample_rate=SAMPLE_RATE,
        feature_extractor_config=extractor.to_dict(),
        pooling_method="mean_pooling_last_hidden_state",
        audio_duration_range=(3.0, 5.0),
        compute_dtype=_compute_dtype_for_device(DEVICE),
    )


class EmbeddingCache:
    """Manages cached Wav2Vec2 embeddings for a specific partition and config."""

    def __init__(
        self,
        cache_root: str | Path = CACHE_ROOT,
        partition: str = "train",
        config_hash: str | None = None,
        compute_fn: Callable[[List[str], str, int], np.ndarray] | None = None,
    ):
        """Initialize cache for a partition.

        Args:
            cache_root: Root directory for all embeddings
            partition: One of "train", "validation" (never "test" or "reference")
            config_hash: 16-char config hash. If None, computed from default config.
            compute_fn: Optional custom extraction function. If None, uses default Wav2Vec2 extraction.
        """
        if partition not in ("train", "validation"):
            raise ValueError(
                f"Partition must be 'train' or 'validation', got '{partition}'"
            )

        self.partition = partition
        self.cache_root = Path(cache_root)
        self.partition_dir = self.cache_root / partition
        self.config_hash = config_hash or get_feature_extractor_config_hash()
        self._compute_fn = compute_fn or self._default_extract_embeddings_batched

        self.manifest_path = self.partition_dir / "manifest.json"
        self.config_hash_path = self.partition_dir / "config_hash.txt"

        # Effective batch size used by the most recent get_or_compute call
        # (reflects OOM fallbacks).
        self.last_effective_batch_size: int | None = None

        # Ensure directory exists
        self.partition_dir.mkdir(parents=True, exist_ok=True)

    def _load_manifest(self) -> dict[str, str]:
        """Load manifest mapping filename -> embedding filename."""
        if self.manifest_path.exists():
            with open(self.manifest_path) as f:
                return json.load(f)
        return {}

    def _save_manifest(self, manifest: dict[str, str]) -> None:
        """Save manifest atomically."""
        tmp_path = self.manifest_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(manifest, f)
        tmp_path.replace(self.manifest_path)

    def _save_config_hash(self) -> None:
        """Save config hash for invalidation checking."""
        with open(self.config_hash_path, "w") as f:
            f.write(self.config_hash)

    def _check_config_hash(self) -> bool:
        """Verify cached config matches current config."""
        if not self.config_hash_path.exists():
            return False
        with open(self.config_hash_path) as f:
            return f.read().strip() == self.config_hash

    def _embedding_path(self, clip_filename: str) -> Path:
        """Get embedding file path for a clip."""
        # Sanitize filename for filesystem safety
        safe_name = clip_filename.replace("/", "_").replace("\\", "_")
        return self.partition_dir / f"emb_{safe_name}.npy"

    @staticmethod
    def _default_extract_embeddings_batched(
        file_paths: List[str],
        dataset_dir: str,
        batch_size: int,
    ) -> np.ndarray:
        """Default embedding extraction using Wav2Vec2 GPU inference.

        Uses torch.inference_mode() and FP16 autocast on CUDA (cast back to
        float32 before mean pooling/caching). Caller handles per-chunk OOM
        fallback; this function processes exactly one chunk per call when
        invoked via get_or_compute's batching loop.

        Args:
            file_paths: List of relative filenames (e.g., "0.wav")
            dataset_dir: Base directory containing WAV files
            batch_size: Batch size for GPU inference

        Returns:
            Array of shape (N, 1024) float32
        """
        global EXTRACTION_STATS

        import librosa

        feature_extractor, wav2vec_model = _get_wav2vec2()

        use_fp16 = DEVICE.type == "cuda"

        embeddings = []

        for i in range(0, len(file_paths), batch_size):
            batch_paths = file_paths[i : i + batch_size]
            batch_audio = []

            t0 = time.perf_counter()
            for rel_path in batch_paths:
                full_path = os.path.join(dataset_dir, rel_path)
                audio, _ = librosa.load(full_path, sr=SAMPLE_RATE, mono=True)

                # Truncate to max clip duration
                max_samples = int(MAX_CLIP_SECONDS * SAMPLE_RATE)
                if len(audio) > max_samples:
                    audio = audio[:max_samples]

                batch_audio.append(audio)

            # Pad batch to same length for batched inference
            max_len = max(len(a) for a in batch_audio)
            padded = np.zeros((len(batch_audio), max_len), dtype=np.float32)
            for j, a in enumerate(batch_audio):
                padded[j, : len(a)] = a

            load_seconds = time.perf_counter() - t0

            t1 = time.perf_counter()
            with torch.inference_mode():
                inputs = feature_extractor(
                    list(padded), sampling_rate=SAMPLE_RATE, return_tensors="pt", padding=True
                )
                inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
                if use_fp16:
                    # Inference-only FP16: ~2x less VRAM for activations,
                    # faster forward on tensor cores. Embeddings are cast
                    # back to float32 before pooling so cached values keep
                    # full float32 container precision.
                    with torch.autocast(
                        device_type="cuda", dtype=torch.float16, enabled=True
                    ):
                        outputs = wav2vec_model(**inputs)
                    hidden = outputs.last_hidden_state.float()
                else:
                    outputs = wav2vec_model(**inputs)
                    hidden = outputs.last_hidden_state
                # Mean-pool over the time axis in float32
                batch_embs = hidden.mean(dim=1).cpu().numpy()
            forward_seconds = time.perf_counter() - t1

            EXTRACTION_STATS["load_seconds"] += load_seconds
            EXTRACTION_STATS["forward_seconds"] += forward_seconds

            # batch_embs shape: (batch_size, 1024)
            if batch_embs.ndim == 3:
                batch_embs = batch_embs.mean(axis=1)

            embeddings.append(batch_embs.astype(np.float32))

        return np.vstack(embeddings).astype(np.float32)

    def get_or_compute(
        self,
        file_paths: List[str],
        dataset_dir: str,
        batch_size: int = 16,
    ) -> np.ndarray:
        """Get embeddings for files, computing only missing ones.

        Extraction runs in chunks of `batch_size`; each chunk's embeddings are
        written and the manifest persisted immediately, so an interrupted run
        resumes where it stopped. On CUDA OOM the batch size falls back
        16 -> 8 -> 4 -> 2 -> 1 automatically (applies to all remaining chunks).

        Args:
            file_paths: List of relative filenames from split (e.g., "0.wav")
            dataset_dir: Base directory containing WAV files
            batch_size: Initial batch size (auto-fallback on OOM)

        Returns:
            Array of shape (N, 1024) float32 in same order as file_paths
        """
        # Check config hash - invalidate if changed
        if not self._check_config_hash():
            logger.info(
                f"Config hash mismatch for {self.partition}, invalidating cache"
            )
            # Clear old cache
            for f in self.partition_dir.glob("emb_*.npy"):
                f.unlink()
            self.manifest_path.unlink(missing_ok=True)

        self._save_config_hash()

        manifest = self._load_manifest()
        missing_indices = []
        missing_paths = []

        for idx, rel_path in enumerate(file_paths):
            if rel_path not in manifest:
                missing_indices.append(idx)
                missing_paths.append(rel_path)

        if missing_paths:
            logger.info(
                f"Computing {len(missing_paths)}/{len(file_paths)} missing embeddings for {self.partition}"
            )

            current_batch_size = batch_size
            pos = 0

            while pos < len(missing_paths):
                chunk = missing_paths[pos : pos + current_batch_size]
                try:
                    computed_embs = self._compute_fn(
                        chunk, dataset_dir, current_batch_size
                    )
                except torch.cuda.OutOfMemoryError:
                    if current_batch_size == 1:
                        raise
                    next_bs = current_batch_size // 2
                    logger.warning(
                        f"OOM at batch_size={current_batch_size}, falling back to {next_bs}"
                    )
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    current_batch_size = next_bs
                    continue  # retry the same chunk at the smaller size

                # Persist each chunk immediately (resumable mid-run)
                for i, rel_path in enumerate(chunk):
                    emb_path = self._embedding_path(rel_path)
                    np.save(emb_path, computed_embs[i])
                    manifest[rel_path] = emb_path.name
                self._save_manifest(manifest)

                pos += len(chunk)

            logger.info(
                f"{self.partition}: finished {len(missing_paths)} clips "
                f"(effective batch_size={current_batch_size})"
            )

        self.last_effective_batch_size = current_batch_size if missing_paths else None

        # Load all embeddings in order
        all_embs = []
        for rel_path in file_paths:
            emb_name = manifest[rel_path]
            emb_path = self.partition_dir / emb_name
            emb = np.load(emb_path)
            if emb.shape != (1024,):
                raise ValueError(
                    f"Invalid embedding shape for {rel_path}: {emb.shape}, expected (1024,)"
                )
            all_embs.append(emb)

        return np.stack(all_embs).astype(np.float32)

    def clear(self) -> None:
        """Clear all cached embeddings for this partition."""
        for f in self.partition_dir.glob("emb_*.npy"):
            f.unlink()
        self.manifest_path.unlink(missing_ok=True)
        self.config_hash_path.unlink(missing_ok=True)
        logger.info(f"Cleared {self.partition} embedding cache")

    @property
    def size(self) -> int:
        """Number of cached embeddings."""
        return len(self._load_manifest())

    def disk_bytes(self) -> int:
        """Total bytes of cached .npy files for this partition."""
        return sum(
            f.stat().st_size for f in self.partition_dir.glob("emb_*.npy")
        )
