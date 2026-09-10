"""Reference evidence retrieval using brute-force cosine similarity.

No vector database needed -- brute-force over a few hundred embeddings
is effectively instant.

Constants:
- MIN_REFERENCE_SIMILARITY = 0.5 (Section 11 of Source of Truth)
- Top-K = 3 nearest neighbors
"""
import os
import numpy as np
import torch
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

MIN_REFERENCE_SIMILARITY = 0.5
TOP_K = 3


class ReferenceIndex:
    """Load and query the reference evidence index."""

    def __init__(self, index_path: str = "models/vaani_model/reference_index.npz"):
        self.index_path = index_path
        self._embeddings = None
        self._labels = None
        self._source_ids = None
        self._speaker_ids = None
        self._loaded = False

    def load(self):
        """Load the reference index from disk."""
        if not os.path.exists(self.index_path):
            logger.warning(f"Reference index not found at {self.index_path}")
            self._loaded = False
            return

        try:
            data = np.load(self.index_path, allow_pickle=True)
            self._embeddings = data.get("embeddings", np.array([]))
            self._labels = data.get("labels", np.array([]))
            self._source_ids = data.get("source_ids", np.array([]))
            self._speaker_ids = data.get("speaker_ids", np.array([]))
            self._loaded = len(self._embeddings) > 0
            logger.info(f"Reference index loaded: {len(self._embeddings)} entries")
        except Exception as e:
            logger.error(f"Failed to load reference index: {e}")
            self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def size(self) -> int:
        if not self._loaded:
            return 0
        return len(self._embeddings)

    def retrieve(
        self, query_embedding: np.ndarray, top_k: int = TOP_K
    ) -> List[Dict[str, any]]:
        """Retrieve top-K nearest neighbors by cosine similarity.

        Args:
            query_embedding: L2-normalized query embedding (1024-dim)
            top_k: Number of results to return

        Returns:
            List of dicts with label, similarity, source, speaker_id
        """
        if not self._loaded:
            return []

        # L2 normalize query
        query = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)

        # Cosine similarity (embeddings are L2-normalized, so dot product = cosine)
        similarities = np.dot(self._embeddings, query)

        # Get top-K indices
        if len(similarities) <= top_k:
            top_indices = np.argsort(similarities)[::-1]
        else:
            top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            sim = float(similarities[idx])
            if sim < MIN_REFERENCE_SIMILARITY:
                continue
            results.append({
                "label": str(self._labels[idx]),
                "similarity": round(sim, 4),
                "source": "In-the-Wild",
                "source_id": str(self._source_ids[idx]),
                "speaker_id": str(self._speaker_ids[idx]),
            })

        return results


def retrieve_references(
    query_embedding: np.ndarray,
    index_path: str = "models/vaani_model/reference_index.npz",
    top_k: int = TOP_K,
) -> Dict[str, any]:
    """Convenience function to retrieve reference examples.

    Returns:
        Dict with 'examples' list and 'note' string
    """
    index = ReferenceIndex(index_path)
    index.load()

    if not index.is_loaded:
        return {
            "examples": [],
            "note": "Reference index unavailable",
            "available": False,
        }

    examples = index.retrieve(query_embedding, top_k)

    if not examples:
        return {
            "examples": [],
            "note": "No strong comparable examples found",
            "available": True,
        }

    return {
        "examples": examples,
        "note": f"Compared against {index.size} reference clips from In-the-Wild dataset",
        "available": True,
    }
