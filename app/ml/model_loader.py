import torch

from app.core.device import DEVICE

# Health state of the real V1 inference pipeline.
# initialize_model() warms up the SAME singletons the analysis path uses
# (Wav2Vec2 backbone + fusion head + scaler from app.ml.inference), so the
# health endpoint reports the actual pipeline state instead of loading a
# second heavyweight model.
_model_state = {"status": "uninitialized", "error": None}


def initialize_model():
    """Warm up the real V1 inference pipeline."""
    if _model_state["status"] == "ready":
        return
    try:
        from app.ml.inference import _load_wav2vec_model, _load_fusion_model, _load_scaler

        _load_wav2vec_model()
        _load_fusion_model()
        _load_scaler()
        _model_state["status"] = "ready"
        _model_state["error"] = None
    except Exception as e:
        _model_state["status"] = "error"
        _model_state["error"] = str(e)
        print(f"⚠️ Model pipeline failed to initialize: {e}")


async def cleanup_model():
    """Release the heavyweight inference singletons."""
    from app.ml import inference as _inference

    _inference._wav2vec_model = None
    _inference._feature_extractor = None
    _inference._fusion_model = None
    _inference._scaler = None
    _model_state["status"] = "uninitialized"
    _model_state["error"] = None

    if DEVICE.type == "cuda":
        torch.cuda.empty_cache()


def get_model():
    """Return the loaded fusion model, or None when the pipeline is not ready."""
    if _model_state["status"] != "ready":
        return None
    from app.ml import inference as _inference

    return _inference._fusion_model


def get_processor():
    """Return the shared Wav2Vec2 feature extractor, or None when not ready."""
    if _model_state["status"] != "ready":
        return None
    from app.ml import inference as _inference

    return _inference._feature_extractor


def get_model_state():
    """Return the real pipeline state: 'uninitialized' | 'ready' | 'error'."""
    return _model_state["status"]


def get_model_error():
    return _model_state["error"]