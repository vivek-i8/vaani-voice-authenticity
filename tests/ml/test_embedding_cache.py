"""Unit tests for EmbeddingCache."""
import os
import tempfile
import shutil
import numpy as np
import pytest

from app.ml.embedding_cache import EmbeddingCache, compute_config_hash


class TestConfigHash:
    """Test config hash computation and invalidation."""

    def test_hash_deterministic(self):
        """Same inputs produce same hash."""
        h1 = compute_config_hash(
            "facebook/wav2vec2-large-xlsr-53",
            16000,
            {"key": "value"},
            "mean_pooling",
            (3.0, 5.0),
        )
        h2 = compute_config_hash(
            "facebook/wav2vec2-large-xlsr-53",
            16000,
            {"key": "value"},
            "mean_pooling",
            (3.0, 5.0),
        )
        assert h1 == h2
        assert len(h1) == 16

    def test_hash_changes_with_params(self):
        """Different params produce different hashes."""
        h1 = compute_config_hash(
            "facebook/wav2vec2-large-xlsr-53", 16000, {}, "mean", (3.0, 5.0)
        )
        h2 = compute_config_hash(
            "facebook/wav2vec2-large-xlsr-53", 16000, {}, "mean", (2.0, 5.0)
        )
        assert h1 != h2

    def test_hash_key_order_independent(self):
        """Dict key order doesn't affect hash."""
        h1 = compute_config_hash("model", 16000, {"a": 1, "b": 2}, "mean", (3.0, 5.0))
        h2 = compute_config_hash("model", 16000, {"b": 2, "a": 1}, "mean", (3.0, 5.0))
        assert h1 == h2


def _mock_compute_fn(file_paths: list[str], dataset_dir: str, batch_size: int) -> np.ndarray:
    """Mock compute function that returns deterministic embeddings."""
    embs = []
    for p in file_paths:
        # Use filename hash for deterministic but different embeddings
        h = hash(p) % 1000
        emb = np.random.RandomState(h).randn(1024).astype(np.float32)
        embs.append(emb)
    return np.stack(embs)


class TestEmbeddingCache:
    """Test EmbeddingCache functionality."""

    @pytest.fixture
    def temp_cache_root(self):
        """Create temporary cache directory."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_cache_creation_and_load(self, temp_cache_root):
        """Test basic cache creation and loading."""
        cache = EmbeddingCache(temp_cache_root, "train", "test_hash_1234", compute_fn=_mock_compute_fn)
        file_paths = ["0.wav", "1.wav", "2.wav"]

        # First call - should compute
        embs1 = cache.get_or_compute(file_paths, ".", batch_size=2)
        assert embs1.shape == (3, 1024)
        assert cache.size == 3

        # Second call - should load from cache
        embs2 = cache.get_or_compute(file_paths, ".", batch_size=2)
        assert np.allclose(embs1, embs2)

    def test_cache_resumability(self, temp_cache_root):
        """Test cache survives partial computation."""
        cache = EmbeddingCache(temp_cache_root, "train", "test_hash_1234", compute_fn=_mock_compute_fn)
        file_paths = ["0.wav", "1.wav", "2.wav", "3.wav"]

        # Compute first two
        cache.get_or_compute(file_paths[:2], ".", batch_size=2)
        assert cache.size == 2

        # Restart with all four - should only compute missing
        embs = cache.get_or_compute(file_paths, ".", batch_size=2)
        assert embs.shape == (4, 1024)
        assert cache.size == 4

    def test_config_invalidation(self, temp_cache_root):
        """Test cache invalidated when config hash changes."""
        cache1 = EmbeddingCache(temp_cache_root, "train", "hash_v1", compute_fn=_mock_compute_fn)
        file_paths = ["0.wav", "1.wav"]

        # Compute with hash_v1
        embs1 = cache1.get_or_compute(file_paths, ".", batch_size=2)
        assert cache1.size == 2
        manifest_v1 = cache1._load_manifest()

        # New cache with different hash
        cache2 = EmbeddingCache(temp_cache_root, "train", "hash_v2", compute_fn=_mock_compute_fn)
        embs2 = cache2.get_or_compute(file_paths, ".", batch_size=2)

        # Should have recomputed - manifest should be rewritten
        manifest_v2 = cache2._load_manifest()
        # Different hash means different config_hash.txt, so manifest was recreated
        assert cache2._check_config_hash() is True
        # The manifest content should be the same (same files) but file was recreated
        assert cache2.size == 2
        # Verify config_hash.txt was updated
        with open(cache2.config_hash_path) as f:
            assert f.read().strip() == "hash_v2"

    def test_partition_isolation(self, temp_cache_root):
        """Train and validation caches are separate."""
        train_cache = EmbeddingCache(temp_cache_root, "train", "same_hash", compute_fn=_mock_compute_fn)
        val_cache = EmbeddingCache(temp_cache_root, "validation", "same_hash", compute_fn=_mock_compute_fn)

        train_cache.get_or_compute(["0.wav"], ".", batch_size=1)
        val_cache.get_or_compute(["1.wav"], ".", batch_size=1)

        assert train_cache.size == 1
        assert val_cache.size == 1
        assert train_cache.partition_dir != val_cache.partition_dir

    def test_invalid_partition_raises(self, temp_cache_root):
        """Test and reference partitions are rejected."""
        with pytest.raises(ValueError):
            EmbeddingCache(temp_cache_root, "test", "hash")
        with pytest.raises(ValueError):
            EmbeddingCache(temp_cache_root, "reference", "hash")

    def test_embedding_shape_validation(self, temp_cache_root):
        """Test that invalid embedding shapes are caught."""
        def bad_compute(file_paths, dataset_dir, batch_size):
            return np.ones((len(file_paths), 512), dtype=np.float32)  # Wrong dim

        cache = EmbeddingCache(temp_cache_root, "train", "test_hash", compute_fn=bad_compute)

        with pytest.raises(ValueError, match="Invalid embedding shape"):
            cache.get_or_compute(["0.wav"], ".", batch_size=1)

    def test_clear(self, temp_cache_root):
        """Test cache clearing."""
        cache = EmbeddingCache(temp_cache_root, "train", "test_hash", compute_fn=_mock_compute_fn)
        cache.get_or_compute(["0.wav", "1.wav"], ".", batch_size=2)
        assert cache.size == 2

        cache.clear()
        assert cache.size == 0
        assert not cache.manifest_path.exists()
        assert not cache.config_hash_path.exists()