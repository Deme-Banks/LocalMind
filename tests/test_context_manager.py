"""
Tests for ContextManager
"""

import pytest
from src.core.context_manager import ContextManager, Message


@pytest.fixture
def context_manager():
    """Create a test context manager."""
    return ContextManager()


def test_context_manager_initialization(context_manager):
    """Test that ContextManager initializes correctly."""
    assert context_manager is not None


def test_get_model_context_size(context_manager):
    """Test getting context size for a model."""
    size = context_manager.get_model_context_size("gpt-4")
    assert size > 0
    assert isinstance(size, int)


def test_count_tokens(context_manager):
    """Test token counting."""
    text = "Hello, world! This is a test."
    count = context_manager.count_tokens(text)
    assert count > 0
    assert isinstance(count, int)


def test_build_context(context_manager):
    """Test building context from messages."""
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there!"),
        Message(role="user", content="How are you?")
    ]
    context = context_manager.build_context(messages, "gpt-4", max_tokens=1000)
    assert context is not None
    assert len(context) > 0


def test_format_messages_for_backend(context_manager):
    """Test formatting messages for backend."""
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi!")
    ]
    formatted = context_manager.format_messages_for_backend(messages, "openai")
    assert formatted is not None
    assert isinstance(formatted, list)
