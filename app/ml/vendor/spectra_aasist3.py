"""Spectra-AASIST3 wrapper for VAANI V2.

Vendored wrapper that loads the model from HuggingFace Hub and provides
a clean inference interface for the VAANI pipeline.

Source: https://huggingface.co/lab260/Spectra-AASIST3
License: Apache-2.0
Pinned commit: bc0ded888080ddad493177bb53aa6f5b95219d7c

Usage:
    from app.ml.vendor.spectra_aasist3 import SpectraAASIST3Wrapper
    wrapper = SpectraAASIST3Wrapper()
    wrapper.load()
    score = wrapper.score(audio_array, sample_rate=16000)
    # score > 0 = more bona fide (human), score < 0 = more spoof (AI)
    wrapper.unload()
"""
import logging
import numpy as np
import torch
from typing import Optional

logger = logging.getLogger(__name__)

# Constants matching the official wrapper
MODEL_REPO = "lab260/Spectra-AASIST3"
EXPECTED_SAMPLE_RATE = 16000
WINDOW_SAMPLES = 64600  # ~4.04 seconds at 16kHz
PREEMPHASIS_COEFF = 0.97


def _preemphasis(audio: np.ndarray, coeff: float = PREEMPHASIS_COEFF) -> np.ndarray:
    """Apply preemphasis filter to audio signal."""
    return np.append(audio[0], audio[1:] - coeff * audio[:-1])


def _window_audio(audio: np.ndarray, target_length: int = WINDOW_SAMPLES) -> np.ndarray:
    """Window audio to target length, tile-repeating if shorter."""
    if len(audio) >= target_length:
        return audio[:target_length]
    # Tile-repeat if shorter
    repeats = (target_length // len(audio)) + 1
    tiled = np.tile(audio, repeats)
    return tiled[:target_length]


class SpectraAASIST3Wrapper:
    """Wrapper around SpectraAASIST3 for VAANI inference.

    Handles model loading from HuggingFace Hub, preprocessing,
    and score computation.
    """

    def __init__(self):
        self._model = None
        self._device = None
        self._loaded = False

    def load(self, device: Optional[str] = None):
        """Load the model from HuggingFace Hub.

        Args:
            device: Target device ('cpu', 'cuda', etc.). If None, auto-detect.
        """
        if self._loaded:
            logger.info("Spectra-AASIST3 already loaded")
            return

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self._device = torch.device(device)

        logger.info(f"Loading Spectra-AASIST3 on {self._device}...")

        try:
            from app.ml.vendor.spectra_aasist3_net import SpectraAASIST3

            self._model = SpectraAASIST3.from_pretrained(MODEL_REPO)
            self._model.to(self._device)
            self._model.eval()
            self._loaded = True
            logger.info("Spectra-AASIST3 loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Spectra-AASIST3: {e}")
            self._model = None
            self._loaded = False
            raise

    def unload(self):
        """Unload the model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None
        self._loaded = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Spectra-AASIST3 unloaded")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def score(self, audio: np.ndarray, sample_rate: int = EXPECTED_SAMPLE_RATE) -> float:
        """Score a single audio clip.

        Args:
            audio: Audio signal as numpy array (float32, mono)
            sample_rate: Expected 16000 Hz

        Returns:
            Score where higher = more bona fide (human).
            Positive scores generally indicate human, negative indicate AI/spoof.
        """
        if not self._loaded or self._model is None:
            raise RuntimeError("Spectra-AASIST3 model not loaded")

        # Validate input
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Apply preprocessing
        audio = _preemphasis(audio)
        audio = _window_audio(audio, WINDOW_SAMPLES)

        # Convert to tensor
        audio_tensor = torch.from_numpy(audio).unsqueeze(0).to(self._device)

        # Run inference
        with torch.no_grad():
            logits = self._model(audio_tensor)
            # Index 1 = bona fide (higher = more human)
            score = logits[0, 1].item()

        return score
