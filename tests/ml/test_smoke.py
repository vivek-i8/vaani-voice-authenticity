"""Smoke tests for the corrected V2 inference pipeline.

Verifies:
- FusionHead forward pass with correct tensor shapes
- predict_proba produces valid probabilities
- Scaler integration: fit -> transform -> predict
- Retraining flow: fit scaler on train, transform, train, save, reload
- Architecture compatibility between training and inference
"""
import os
import tempfile
import numpy as np
import pytest
import torch
import joblib
from sklearn.preprocessing import StandardScaler

from app.ml.fusion_head import FusionHead


class TestFusionHeadArchitecture:
    """Verify FusionHead accepts concatenated 1027-dim input."""

    def test_forward_pass_shape(self):
        model = FusionHead(input_dim=1027, num_classes=2)
        x = torch.randn(1, 1027)
        logits = model(x)
        assert logits.shape == (1, 2), f"Expected (1, 2), got {logits.shape}"

    def test_batch_forward(self):
        model = FusionHead(input_dim=1027, num_classes=2)
        x = torch.randn(8, 1027)
        logits = model(x)
        assert logits.shape == (8, 2)

    def test_predict_proba_sums_to_one(self):
        model = FusionHead(input_dim=1027, num_classes=2)
        x = torch.randn(4, 1027)
        probs = model.predict_proba(x)
        assert probs.shape == (4, 2)
        sums = probs.sum(dim=1)
        assert torch.allclose(sums, torch.ones(4), atol=1e-5), (
            f"Probabilities should sum to 1.0, got {sums}"
        )

    def test_predict_proba_non_negative(self):
        model = FusionHead(input_dim=1027, num_classes=2)
        x = torch.randn(4, 1027)
        probs = model.predict_proba(x)
        assert (probs >= 0).all(), "Probabilities must be non-negative"

    def test_logits_to_probs_conversion(self):
        """Verify softmax produces same result as manual calculation."""
        model = FusionHead(input_dim=1027, num_classes=2)
        model.eval()  # Disable dropout for deterministic comparison
        x = torch.randn(1, 1027)
        logits = model(x)
        probs = model.predict_proba(x)
        manual_probs = torch.softmax(logits, dim=1)
        assert torch.allclose(probs, manual_probs, atol=1e-6)


class TestScalerIntegration:
    """Verify scaler fit -> transform -> predict pipeline matches inference.py."""

    def test_scaler_fit_and_transform(self):
        """Simulate: fit scaler on train features, transform, predict."""
        # Simulate training features (1027-dim: 1024 wav2vec + 3 acoustic)
        train_features = np.random.randn(50, 1027).astype(np.float32)
        scaler = StandardScaler()
        scaler.fit(train_features)

        # Transform a sample
        sample = np.random.randn(1, 1027).astype(np.float32)
        transformed = scaler.transform(sample)

        assert transformed.shape == (1, 1027)
        # After StandardScaler, mean should be ~0 and std ~1 on training data
        train_transformed = scaler.transform(train_features)
        assert abs(train_transformed.mean()) < 0.1
        assert abs(train_transformed.std() - 1.0) < 0.1

    def test_scaler_roundtrip_with_model(self):
        """Full pipeline: fit scaler, save, load, transform, predict."""
        # Fit scaler on synthetic training data
        train_features = np.random.randn(50, 1027).astype(np.float32)
        scaler = StandardScaler()
        scaler.fit(train_features)

        # Save and reload scaler
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            scaler_path = f.name
        try:
            joblib.dump(scaler, scaler_path)
            loaded_scaler = joblib.load(scaler_path)

            # Transform a sample
            sample = np.random.randn(1, 1027).astype(np.float32)
            transformed = loaded_scaler.transform(sample).squeeze()
            features_tensor = torch.FloatTensor(transformed).unsqueeze(0)

            # Predict through model
            model = FusionHead(input_dim=1027, num_classes=2)
            probs = model.predict_proba(features_tensor)
            assert probs.shape == (1, 2)
            assert abs(probs.sum().item() - 1.0) < 1e-5
        finally:
            os.unlink(scaler_path)


class TestArchitectureCompatibility:
    """Verify training and inference use identical architecture."""

    def test_state_dict_key_consistency(self):
        """Keys from a trained model must match what model_loader expects."""
        model = FusionHead(input_dim=1027, num_classes=2)
        state_dict = model.state_dict()

        # Expected keys from nn.Sequential with name "network"
        expected_prefixes = ["network.0.", "network.2.", "network.3.", "network.5.", "network.6.", "network.7."]
        for key in state_dict.keys():
            assert key.startswith("network."), (
                f"Unexpected key '{key}' — should start with 'network.'"
            )

    def test_save_and_reload(self):
        """Save model state dict, reload into fresh instance, verify same output."""
        model = FusionHead(input_dim=1027, num_classes=2)
        x = torch.randn(1, 1027)

        # Get prediction before save
        model.eval()
        with torch.no_grad():
            probs_before = model.predict_proba(x).numpy()

        # Save and reload
        with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
            model_path = f.name
        try:
            torch.save(model.state_dict(), model_path)

            model2 = FusionHead(input_dim=1027, num_classes=2)
            model2.load_state_dict(torch.load(model_path, weights_only=True))
            model2.eval()
            with torch.no_grad():
                probs_after = model2.predict_proba(x).numpy()

            assert np.allclose(probs_before, probs_after, atol=1e-6), (
                "Reloaded model should produce identical output"
            )
        finally:
            os.unlink(model_path)


class TestMinimalTraining:
    """Verify the training loop actually updates model weights."""

    def test_training_reduces_loss(self):
        """A few training steps should reduce loss on synthetic data."""
        torch.manual_seed(42)
        np.random.seed(42)

        model = FusionHead(input_dim=1027, num_classes=2)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        criterion = torch.nn.CrossEntropyLoss()

        # Generate separable synthetic data
        X = np.random.randn(64, 1027).astype(np.float32)
        y = np.array([0] * 32 + [1] * 32)  # First 32 = class 0, next 32 = class 1
        # Make classes separable by shifting class 1 features
        X[32:] += 2.0

        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.LongTensor(y)

        # Record initial loss
        model.eval()
        with torch.no_grad():
            initial_loss = criterion(model(X_tensor), y_tensor).item()

        # Train for 10 steps
        model.train()
        for _ in range(10):
            optimizer.zero_grad()
            logits = model(X_tensor)
            loss = criterion(logits, y_tensor)
            loss.backward()
            optimizer.step()

        # Loss should decrease
        model.eval()
        with torch.no_grad():
            final_loss = criterion(model(X_tensor), y_tensor).item()

        assert final_loss < initial_loss, (
            f"Training should reduce loss: {initial_loss:.4f} -> {final_loss:.4f}"
        )
