import torch
import os
import logging

from app.core.device import DEVICE

logger = logging.getLogger(__name__)

# Model status tracking
_wav2vec_model = None
_feature_extractor = None
_fusion_model = None
_scaler = None
_spectra_model = None

_model_status = {
    "wav2vec2": False,
    "fusion_head": False,
    "scaler": False,
    "spectra_aasist3": False,
}


def initialize_models():
    """Initialize all VAANI pipeline models at startup.

    Loads:
    1. Wav2Vec2 backbone (for VAANI feature extraction)
    2. Trained fusion head
    3. Fitted scaler
    4. Spectra-AASIST3 (independent anti-spoofing signal)

    Reports status via logging.
    """
    global _wav2vec_model, _feature_extractor, _fusion_model, _scaler, _spectra_model

    logger.info("Initializing VAANI pipeline models...")

    # Load Wav2Vec2 backbone
    try:
        from transformers import Wav2Vec2Model, Wav2Vec2FeatureExtractor

        _feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
            "facebook/wav2vec2-large-xlsr-53"
        )
        _wav2vec_model = Wav2Vec2Model.from_pretrained(
            "facebook/wav2vec2-large-xlsr-53"
        ).to(DEVICE)

        # Freeze Wav2Vec2 parameters
        for param in _wav2vec_model.parameters():
            param.requires_grad = False
        _wav2vec_model.eval()

        _model_status["wav2vec2"] = True
        logger.info("Wav2Vec2 backbone loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Wav2Vec2 backbone: {e}")
        _model_status["wav2vec2"] = False

    # Load fusion head
    try:
        from app.ml.fusion_head import FusionHead

        model_path = "models/vaani_model/fusion_head.pth"
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Fusion head not found at {model_path}. "
                "Please run training first."
            )

        _fusion_model = FusionHead(
            input_dim=1027, num_classes=2
        )
        _fusion_model.load_state_dict(
            torch.load(model_path, map_location=DEVICE, weights_only=True)
        )
        _fusion_model.to(DEVICE)
        _fusion_model.eval()

        _model_status["fusion_head"] = True
        logger.info("Fusion head loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load fusion head: {e}")
        _model_status["fusion_head"] = False

    # Load scaler
    try:
        import joblib

        scaler_path = "models/vaani_model/scaler.pkl"
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(
                f"Scaler not found at {scaler_path}. "
                "Please run training first."
            )

        _scaler = joblib.load(scaler_path)
        _model_status["scaler"] = True
        logger.info("Scaler loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load scaler: {e}")
        _model_status["scaler"] = False

    # Load Spectra-AASIST3 (independent anti-spoofing signal)
    try:
        from app.ml.vendor.spectra_aasist3 import SpectraAASIST3Wrapper

        _spectra_model = SpectraAASIST3Wrapper()
        _spectra_model.load(device=str(DEVICE))

        _model_status["spectra_aasist3"] = True
        logger.info("Spectra-AASIST3 loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Spectra-AASIST3: {e}")
        _spectra_model = None
        _model_status["spectra_aasist3"] = False
        logger.warning(
            "Running in degraded mode: VAANI-only signal (no ensemble)"
        )

    # Log overall status
    all_loaded = all(_model_status.values())
    if all_loaded:
        logger.info("All VAANI pipeline models initialized successfully")
    else:
        failed = [k for k, v in _model_status.items() if not v]
        logger.warning(f"Some models failed to load: {failed}")


async def cleanup_models():
    """Clean up all loaded models at shutdown."""
    global _wav2vec_model, _feature_extractor, _fusion_model, _scaler, _spectra_model

    logger.info("Cleaning up VAANI pipeline models...")

    # Clean up Spectra-AASIST3
    if _spectra_model is not None:
        try:
            _spectra_model.unload()
        except Exception as e:
            logger.warning(f"Error unloading Spectra-AASIST3: {e}")
        _spectra_model = None

    # Clean up other models
    for name, ref in [
        ("wav2vec2", "_wav2vec_model"),
        ("feature_extractor", "_feature_extractor"),
        ("fusion_head", "_fusion_model"),
        ("scaler", "_scaler"),
    ]:
        if globals()[ref] is not None:
            del globals()[ref]
            globals()[ref] = None
            logger.info(f"Cleaned up {name}")

    torch.cuda.empty_cache()


def get_wav2vec_model():
    """Get the loaded Wav2Vec2 model."""
    return _wav2vec_model


def get_feature_extractor():
    """Get the loaded feature extractor."""
    return _feature_extractor


def get_fusion_model():
    """Get the loaded fusion head model."""
    return _fusion_model


def get_scaler():
    """Get the loaded scaler."""
    return _scaler


def get_spectra_model():
    """Get the loaded Spectra-AASIST3 wrapper."""
    return _spectra_model


def get_model_status():
    """Return the current status of all models.

    Returns a dict suitable for the /api/health endpoint.
    """
    all_loaded = all(_model_status.values())
    return {
        "status": "ok" if all_loaded else "partial",
        "models": dict(_model_status),
        "device": str(DEVICE),
    }
