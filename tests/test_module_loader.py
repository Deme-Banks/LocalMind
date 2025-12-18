"""
Unit tests for ModuleLoader
"""

import pytest
from pathlib import Path
from src.core.module_loader import ModuleLoader
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager


@pytest.fixture
def config_manager():
    """Create a ConfigManager instance for testing"""
    return ConfigManager()


@pytest.fixture
def model_loader(config_manager):
    """Create a ModelLoader instance for testing"""
    return ModelLoader(config_manager)


@pytest.fixture
def module_loader(config_manager, model_loader):
    """Create a ModuleLoader instance for testing"""
    return ModuleLoader()


def test_list_modules(module_loader):
    """Test listing available modules"""
    modules = module_loader.list_modules()
    
    assert isinstance(modules, list)
    assert len(modules) > 0
    
    # Check module structure
    for module_info in modules:
        assert "name" in module_info
        assert "description" in module_info
        assert isinstance(module_info["name"], str)
        assert isinstance(module_info["description"], str)


def test_get_module(module_loader):
    """Test getting a specific module"""
    modules = module_loader.list_modules()
    
    if len(modules) > 0:
        module_name = modules[0]["name"]
        module = module_loader.get_module(module_name)
        
        assert module is not None
        assert hasattr(module, "process")
        assert hasattr(module, "get_info")


def test_get_nonexistent_module(module_loader):
    """Test getting a non-existent module"""
    module = module_loader.get_module("nonexistent-module")
    assert module is None


def test_process_input_with_modules(module_loader):
    """Test processing input with modules"""
    # Test with a simple prompt
    result = module_loader.process_prompt("Hello, world!")
    
    # Should return a result (may be None if no module handles it)
    assert result is None or isinstance(result, dict)


def test_module_info_structure(module_loader):
    """Test that module info has correct structure"""
    modules = module_loader.list_modules()
    
    for module_info in modules:
        # Check required fields
        assert "name" in module_info
        assert "description" in module_info
        
        # Get the actual module
        module = module_loader.get_module(module_info["name"])
        if module:
            info = module.get_info()
            assert "name" in info
            assert "description" in info

