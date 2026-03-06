import torch
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor

from app.core.config import settings
from app.core.device import DEVICE

model = None
processor = None
id2label = None

def initialize_model():
    global model, processor, id2label
    
    if model is not None:
        return
    
    model = AutoModelForAudioClassification.from_pretrained(settings.model_name)
    
    # Conditional device handling for GPU/CPU safety
    if DEVICE.type == "cuda":
        model = model.to(DEVICE)
    else:
        model = model.to(DEVICE)
    
    model.eval()
    
    processor = AutoFeatureExtractor.from_pretrained(settings.model_name)
    id2label = model.config.id2label
    
async def cleanup_model():
    global model, processor, id2label
    
    if model is not None:
        del model
        model = None
    
    if processor is not None:
        del processor
        processor = None
    
    if id2label is not None:
        del id2label
        id2label = None
    
    torch.cuda.empty_cache()

def get_model():
    if model is None:
        return None
    return model

def get_processor():
    if processor is None:
        return None
    return processor

def get_id2label():
    if id2label is None:
        return None
    return id2label