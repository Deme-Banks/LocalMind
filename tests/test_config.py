"""
Tests for ConfigManager
"""

import pytest
from pathlib import Path
from src.utils.config import ConfigManager


@pytest.fixture
def temp_config_path(tmp_path):
    """Create a temporary config path."""
    return tmp_path / "test_config.yaml"


def test_config_manager_initialization(temp_config_path):
    """Test that ConfigManager initializes correctly."""
    manager = ConfigManager(config_path=temp_config_path)
    assert manager is not None
    assert manager.config_path == temp_config_path


def test_get_config(temp_config_path):
    """Test getting configuration."""
    manager = ConfigManager(config_path=temp_config_path)
    config = manager.get_config()
    assert config is not None
    assert hasattr(config, 'default_model')
    assert hasattr(config, 'backends')


def test_save_config(temp_config_path):
    """Test saving configuration."""
    manager = ConfigManager(config_path=temp_config_path)
    config = manager.get_config()
    manager.save_config()
    assert temp_config_path.exists()

