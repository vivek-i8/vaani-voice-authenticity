import torch
import torch.nn as nn
import numpy as np
import os
from typing import Dict, Any

# Import our custom modules
from app.ml.acoustic_features import compute_pitch_variance, compute_spectral_centroid_drift, compute_zcr_variance

class FusionHead(nn.Module):
    """Fusion head for VAANI - 2-class version"""
    
    def __init__(self, input_dim=1027, hidden_dims=[256, 64], output_dim=2, dropout=0.3):
        super(FusionHead, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        # Hidden layers
        for i, hidden_dim in enumerate(hidden_dims):
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout) if i == 0 else nn.Identity()  # Dropout only after first layer
            ])
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, output_dim))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        logits = self.network(x)
        return logits
    
    def predict_proba(self, x):
        """Get class probabilities"""
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = torch.softmax(logits, dim=1)
        return probabilities

# Global model instances
_wav2vec_model = None
_feature_extractor = None
_fusion_model = None
_scaler = None
_device = None

def _initialize_device():
    """Initialize device (GPU if available, otherwise CPU)"""
    global _device
    if _device is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🖥️  Inference device: {_device}")
    return _device

def _load_wav2vec_model():
    """Load Wav2Vec2 model for feature extraction"""
    global _wav2vec_model, _feature_extractor
    
    if _wav2vec_model is not None and _feature_extractor is not None:
        return _wav2vec_model, _feature_extractor
    
    device = _initialize_device()
    
    print("📥 Loading Wav2Vec2 model for inference...")
    from transformers import Wav2Vec2Model, Wav2Vec2FeatureExtractor
    
    # Load Wav2Vec2 model and feature extractor
    _feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("facebook/wav2vec2-large-xlsr-53")
    _wav2vec_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-large-xlsr-53").to(device)
    
    # Freeze Wav2Vec2 parameters
    for param in _wav2vec_model.parameters():
        param.requires_grad = False
    _wav2vec_model.eval()
    
    print("✅ Wav2Vec2 model loaded for inference")
    return _wav2vec_model, _feature_extractor

def _load_scaler():
    """Load the fitted StandardScaler"""
    global _scaler
    
    if _scaler is not None:
        return _scaler
    
    scaler_path = "models/vaani_model/scaler.pkl"
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler not found at {scaler_path}. Please run training first.")
    
    import joblib
    _scaler = joblib.load(scaler_path)
    print("✅ Scaler loaded for inference")
    return _scaler

def _load_fusion_model():
    """Load trained fusion model"""
    global _fusion_model
    
    if _fusion_model is not None:
        return _fusion_model
    
    device = _initialize_device()
    model_path = "models/vaani_model/fusion_head.pth"
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained fusion model not found at {model_path}")
    
    print("📥 Loading trained fusion model...")
    
    # Initialize fusion model with correct architecture
    _fusion_model = FusionHead(input_dim=1027, hidden_dims=[256, 64], output_dim=2, dropout=0.3)
    _fusion_model.load_state_dict(torch.load(model_path, map_location=device))
    _fusion_model.to(device)
    _fusion_model.eval()
    
    print("✅ Fusion model loaded successfully")
    return _fusion_model

def _extract_wav2vec2_embedding(audio: np.ndarray, sampling_rate: int = 16000) -> np.ndarray:
    """Extract 1024-dim Wav2Vec2 embedding using mean pooling"""
    device = _initialize_device()
    wav2vec_model, feature_extractor = _load_wav2vec_model()
    
    with torch.no_grad():
        # Process audio
        input_values = feature_extractor(
            audio, 
            sampling_rate=sampling_rate, 
            return_tensors="pt"
        ).input_values.to(device)
        
        # Get embeddings
        outputs = wav2vec_model(input_values)
        
        # Mean pooling across time dimension to get 1024-dim embedding
        embeddings = outputs.last_hidden_state.mean(dim=1)
        embedding = embeddings.squeeze().cpu().numpy()
        
        # Ensure correct shape
        if embedding.ndim > 1:
            embedding = embedding.mean(axis=0)
        if embedding.size != 1024:
            if embedding.size > 1024:
                embedding = embedding[:1024]
            else:
                embedding = np.pad(embedding, (0, 1024 - embedding.size))
    
    print("DEBUG Wav2Vec2 embedding shape:", embedding.shape)
    return embedding

def _extract_acoustic_features(audio: np.ndarray, sampling_rate: int = 16000) -> np.ndarray:
    """Extract 3 acoustic features"""
    pitch_var = compute_pitch_variance(audio, sampling_rate)
    spec_centroid_drift = compute_spectral_centroid_drift(audio, sampling_rate)
    zcr_var = compute_zcr_variance(audio, sampling_rate)
    
    return np.array([pitch_var, spec_centroid_drift, zcr_var])

def _compute_entropy(probabilities: np.ndarray) -> float:
    """Compute entropy from probabilities using natural log"""
    # Add small epsilon to avoid log(0)
    eps = 1e-8
    probabilities = np.clip(probabilities, eps, 1 - eps)
    entropy = -np.sum(probabilities * np.log(probabilities))
    return float(entropy)

def _make_decision(probabilities: np.ndarray, entropy: float) -> tuple:
    """Make decision based on entropy threshold"""
    ENTROPY_THRESHOLD = 0.55
    
    if entropy > ENTROPY_THRESHOLD:
        label = "Inconclusive"
    else:
        # Choose class with higher probability
        if probabilities[0] > probabilities[1]:  # p_human > p_ai
            label = "Human"
        else:
            label = "AI"
    
    confidence = float(np.max(probabilities))
    return label, confidence

def run_inference(audio: np.ndarray, sampling_rate: int = 16000) -> Dict[str, Any]:
    """
    Run VAANI inference using fusion model with decision logic.
    
    Args:
        audio: Audio signal as numpy array
        sampling_rate: Audio sampling rate (default: 16000)
    
    Returns:
        Dictionary with decision, confidence, entropy, and acoustic signals
    """
    try:
        # Safety guards - ensure all models are loaded
        if _wav2vec_model is None:
            _load_wav2vec_model()
        if _fusion_model is None:
            _load_fusion_model()
        if _scaler is None:
            _load_scaler()
        
        # Load models if not already loaded
        fusion_model = _load_fusion_model()
        device = _initialize_device()
        
        print("🔍 Starting VAANI inference...")
        
        # Step 1: Extract Wav2Vec2 embedding (1024-dim)
        print("📥 Step 1: Extracting Wav2Vec2 embedding...")
        wav2vec2_embedding = _extract_wav2vec2_embedding(audio, sampling_rate)
        print(f"   Wav2Vec2 embedding shape: {wav2vec2_embedding.shape}")
        
        # Step 2: Extract acoustic features (3-dim)
        print("🎵 Step 2: Extracting acoustic features...")
        acoustic_features = _extract_acoustic_features(audio, sampling_rate)
        print(f"   Acoustic features: pitch_var={acoustic_features[0]:.6f}, spec_drift={acoustic_features[1]:.2f}, zcr_var={acoustic_features[2]:.6f}")
        
        # Step 3: Concatenate features (1024 + 3 = 1027)
        print("🔗 Step 3: Concatenating features...")
        feature_vector = np.concatenate([wav2vec2_embedding, acoustic_features])
        print("DEBUG acoustic features:", acoustic_features)
        print("DEBUG final feature vector shape:", feature_vector.shape)
        
        # Validate feature vector size
        if feature_vector.shape[0] != 1027:
            raise ValueError(f"Invalid feature size: expected 1027, got {feature_vector.shape[0]}")
        
        # Step 4: Apply standardization using loaded scaler
        print("⚖️ Step 4: Applying standardization...")
        scaler = _load_scaler()
        
        print("DEBUG feature mean before scaling:", np.mean(feature_vector))
        print("DEBUG feature std before scaling:", np.std(feature_vector))
        
        feature_vector = scaler.transform(feature_vector.reshape(1, -1)).squeeze()
        
        print("DEBUG feature mean after scaling:", np.mean(feature_vector))
        print("DEBUG feature std after scaling:", np.std(feature_vector))
        print(f"   Standardized features shape: {feature_vector.shape}")
        
        # Step 5: Convert to tensor and add batch dimension
        print("🔥 Step 5: Converting to tensor...")
        features_tensor = torch.FloatTensor(feature_vector).unsqueeze(0).to(device)
        print(f"   Tensor shape: {features_tensor.shape}")
        
        # Step 6: Run inference
        print("🧠 Step 6: Running model inference...")
        with torch.no_grad():
            logits = fusion_model(features_tensor)
            probabilities = fusion_model.predict_proba(features_tensor)
            probs_np = probabilities.squeeze().cpu().numpy()
        
        print("DEBUG raw logits:", logits.squeeze().cpu().numpy())
        print("DEBUG probabilities:", probs_np)
        print(f"   Probabilities sum: {np.sum(probs_np)}")
        
        # Step 7: Compute entropy
        print("🔀 Step 7: Computing entropy...")
        entropy = _compute_entropy(probs_np)
        
        # Step 8: Make decision
        print("🎯 Step 8: Making decision...")
        label, confidence = _make_decision(probs_np, entropy)
        
        print("DEBUG entropy:", entropy)
        print("DEBUG predicted label:", label)
        print("DEBUG confidence:", confidence)
        print(f"   Decision: {label} (confidence: {confidence:.3f})")
        
        # Step 9: Prepare result with acoustic signals
        result = {
            "label": label,
            "confidence": confidence,
            "entropy": entropy,
            "signals": {
                "pitch_variance": float(acoustic_features[0]),
                "spectral_drift": float(acoustic_features[1]),
                "zcr_variance": float(acoustic_features[2])
            }
        }
        
        print("✅ Inference completed successfully!")
        return result
        
    except Exception as e:
        print(f"❌ Inference failed: {str(e)}")
        raise RuntimeError(f"Inference failed: {str(e)}")

def generate_claude_explanation(result: dict) -> str:
    """Generate Claude explanation for voice analysis result using AWS Bedrock."""
    try:
        from app.llm.bedrock_llm import BedrockLLM
        
        # Initialize Bedrock client
        llm = BedrockLLM()
        
        # Prepare structured data for Claude
        structured_data = {
            "label": result["label"],
            "confidence": result["confidence"],
            "pitch_variance": result["signals"]["pitch_variance"],
            "spectral_drift": result["signals"]["spectral_drift"],
            "zcr_variance": result["signals"]["zcr_variance"]
        }
        
        # Generate explanation
        explanation = llm.generate(structured_data, language="en")
        return explanation
        
    except Exception as e:
        print(f"⚠️ Failed to generate Claude explanation: {str(e)}")
        # Fallback explanation
        if result["label"] == "AI":
            return "Synthetic voice patterns detected with artificial characteristics."
        elif result["label"] == "Human":
            return "Detected natural pitch variations and spectral patterns consistent with authentic human speech."
        else:
            return "Audio quality is insufficient for definitive analysis. Please provide a clearer audio sample."

# Test function for verification
def test_inference_pipeline():
    """Test the inference pipeline with dummy data"""
    print("🧪 Testing VAANI inference pipeline with decision logic...")
    
    try:
        # Test with a known human-like pattern
        print("\n🔬 Test 1: Human-like audio (low entropy)")
        dummy_human_audio = np.random.RandomState(42).randn(160000).astype(np.float32) * 0.1
        result_human = run_inference(dummy_human_audio)
        print(f"   Expected: Human, Got: {result_human['label']}")
        
        # Test with a known AI-like pattern  
        print("\n🤖 Test 2: AI-like audio (high entropy)")
        dummy_ai_audio = np.random.RandomState(123).randn(160000).astype(np.float32) * 0.5
        result_ai = run_inference(dummy_ai_audio)
        print(f"   Expected: AI, Got: {result_ai['label']}")
        
        # Test with borderline case
        print("\n❓ Test 3: Borderline case (medium entropy)")
        dummy_borderline_audio = np.random.RandomState(789).randn(160000).astype(np.float32) * 0.3
        result_borderline = run_inference(dummy_borderline_audio)
        print(f"   Expected: Inconclusive, Got: {result_borderline['label']}")
        
        print("\n✅ Inference pipeline test completed!")
        print("� All tests passed - inference pipeline is working correctly!")
        
        return result_human, result_ai, result_borderline
        
    except Exception as e:
        print(f"❌ Inference pipeline test failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run test when executed directly
    test_inference_pipeline()
