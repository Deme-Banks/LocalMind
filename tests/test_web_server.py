"""
Tests for WebServer
"""

import pytest
from unittest.mock import Mock, patch
from src.web.server import WebServer
from src.utils.config import ConfigManager


@pytest.fixture
def config_manager():
    """Create a test config manager."""
    return ConfigManager()


@pytest.fixture
def web_server(config_manager):
    """Create a test web server."""
    return WebServer(config_manager, host="127.0.0.1", port=5001)


def test_web_server_initialization(web_server):
    """Test that WebServer initializes correctly."""
    assert web_server is not None
    assert web_server.app is not None
    assert web_server.config_manager is not None
    assert web_server.model_loader is not None


def test_error_response_helper(web_server):
    """Test the error response helper."""
    response, status_code = web_server._error_response("Test error", status_code=400, error_type="validation")
    assert status_code == 400
    assert response["status"] == "error"
    assert response["message"] == "Test error"
    assert response["error_type"] == "validation"


def test_success_response_helper(web_server):
    """Test the success response helper."""
    response = web_server._success_response({"test": "data"}, message="Success")
    assert response["status"] == "ok"
    assert response["message"] == "Success"
    assert response["test"] == "data"

