"""
Integration tests for backends
"""

import pytest
from src.backends.base import BaseBackend
from src.backends.ollama import OllamaBackend
from src.utils.config import ConfigManager


@pytest.fixture
def config_manager():
    """Create a ConfigManager instance for testing"""
    return ConfigManager()


def test_ollama_backend_initialization(config_manager):
    """Test Ollama backend initialization"""
    config = config_manager.get_config()
    ollama_config = config.backends.get("ollama", {})
    
    if ollama_config and ollama_config.enabled:
        backend = OllamaBackend(ollama_config.settings)
        
        assert backend is not None
        assert isinstance(backend, BaseBackend)
        assert hasattr(backend, "is_available")
        assert hasattr(backend, "list_models")
        assert hasattr(backend, "generate")


def test_ollama_backend_is_available(config_manager):
    """Test checking if Ollama is available"""
    config = config_manager.get_config()
    ollama_config = config.backends.get("ollama", {})
    
    if ollama_config and ollama_config.enabled:
        backend = OllamaBackend(ollama_config.settings)
        
        # This will check if Ollama is running
        available = backend.is_available()
        assert isinstance(available, bool)


def test_ollama_backend_list_models(config_manager):
    """Test listing Ollama models"""
    config = config_manager.get_config()
    ollama_config = config.backends.get("ollama", {})
    
    if ollama_config and ollama_config.enabled:
        backend = OllamaBackend(ollama_config.settings)
        
        if backend.is_available():
            models = backend.list_models()
            assert isinstance(models, list)
            # All items should be strings
            assert all(isinstance(model, str) for model in models)


def test_ollama_backend_get_backend_info(config_manager):
    """Test getting Ollama backend info"""
    config = config_manager.get_config()
    ollama_config = config.backends.get("ollama", {})
    
    if ollama_config and ollama_config.enabled:
        backend = OllamaBackend(ollama_config.settings)
        
        info = backend.get_backend_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "type" in info
        assert info["name"] == "ollama"
        assert info["type"] == "local"


def test_base_backend_interface():
    """Test that BaseBackend defines required methods"""
    # Check that BaseBackend has required abstract methods
    assert hasattr(BaseBackend, "is_available")
    assert hasattr(BaseBackend, "list_models")
    assert hasattr(BaseBackend, "generate")
    assert hasattr(BaseBackend, "generate_stream")
    assert hasattr(BaseBackend, "get_backend_info")

