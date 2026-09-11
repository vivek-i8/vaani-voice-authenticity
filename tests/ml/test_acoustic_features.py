"""V1 test: acoustic feature extraction sanity on synthetic signals."""
import numpy as np

from app.ml.acoustic_features import (
    compute_pitch_variance,
    compute_spectral_centroid_drift,
    compute_zcr_variance,
)


def _sine(freq_hz=220.0, seconds=1.0, sr=16000):
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    return (0.3 * np.sin(2 * np.pi * freq_hz * t)).astype(np.float32)


def test_features_are_finite_floats_on_sine_wave():
    audio = _sine()
    pitch_var = compute_pitch_variance(audio, 16000)
    spec_drift = compute_spectral_centroid_drift(audio, 16000)
    zcr_var = compute_zcr_variance(audio, 16000)

    for value in (pitch_var, spec_drift, zcr_var):
        assert isinstance(value, float)
        assert np.isfinite(value)
        assert value >= 0.0


def test_silence_returns_zero_features():
    silence = np.zeros(16000, dtype=np.float32)
    assert compute_pitch_variance(silence, 16000) == 0.0
    assert compute_spectral_centroid_drift(silence, 16000) == 0.0
    assert compute_zcr_variance(silence, 16000) == 0.0


def test_steady_sine_has_low_pitch_variance():
    audio = _sine(220.0)
    assert compute_pitch_variance(audio, 16000) < 100.0
