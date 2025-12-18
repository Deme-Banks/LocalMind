"""
Tests for ModelLoader
"""

import pytest
from unittest.mock import Mock, patch
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager


@pytest.fixture
def config_manager():
    """Create a test config manager."""
    return ConfigManager()


@pytest.fixture
def model_loader(config_manager):
    """Create a test model loader."""
    return ModelLoader(config_manager)


def test_model_loader_initialization(model_loader):
    """Test that ModelLoader initializes correctly."""
    assert model_loader is not None
    assert model_loader.config_manager is not None
    assert hasattr(model_loader, 'backends')


def test_list_available_models(model_loader):
    """Test listing available models."""
    models = model_loader.list_available_models()
    assert isinstance(models, dict)


def test_get_backend(model_loader):
    """Test getting a backend."""
    backend = model_loader.get_backend()
    # May be None if no backends are available
    assert backend is None or hasattr(backend, 'list_models')

