"""
Tests for ModelRegistry
"""

import pytest
from pathlib import Path
from src.core.model_registry import ModelRegistry


@pytest.fixture
def temp_registry_path(tmp_path):
    """Create a temporary registry path."""
    return tmp_path / "registry.json"


@pytest.fixture
def model_registry(temp_registry_path):
    """Create a test model registry."""
    return ModelRegistry(registry_path=temp_registry_path)


def test_model_registry_initialization(model_registry):
    """Test that ModelRegistry initializes correctly."""
    assert model_registry is not None
    assert model_registry.registry_path.exists() or model_registry.registry_path.parent.exists()


def test_get_available_models(model_registry):
    """Test getting available models for a backend."""
    models = model_registry.get_available_models("ollama")
    assert isinstance(models, list)
    # Should have at least some models
    assert len(models) > 0


def test_register_model(model_registry):
    """Test registering a model."""
    metadata = {
        "size": "1GB",
        "description": "Test model",
        "tags": ["test"]
    }
    model_registry.register_model("test-backend", "test-model", metadata)
    # Check that model was registered
    backend_models = model_registry.registry.get("backends", {}).get("test-backend", {}).get("models", {})
    assert "test-model" in backend_models
    assert backend_models["test-model"]["size"] == "1GB"
