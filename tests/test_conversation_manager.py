"""
Tests for ConversationManager
"""

import pytest
from pathlib import Path
from src.core.conversation_manager import ConversationManager


@pytest.fixture
def temp_conversations_dir(tmp_path):
    """Create a temporary conversations directory."""
    return tmp_path / "conversations"


@pytest.fixture
def conversation_manager(temp_conversations_dir):
    """Create a test conversation manager."""
    return ConversationManager(conversations_dir=temp_conversations_dir)


def test_conversation_manager_initialization(conversation_manager):
    """Test that ConversationManager initializes correctly."""
    assert conversation_manager is not None
    assert conversation_manager.conversations_dir.exists()


def test_create_conversation(conversation_manager):
    """Test creating a new conversation."""
    conv_id = conversation_manager.create_conversation(title="Test Conversation", model="test-model")
    assert conv_id is not None
    assert isinstance(conv_id, str)


def test_get_conversation(conversation_manager):
    """Test getting a conversation."""
    conv_id = conversation_manager.create_conversation(title="Test", model="test-model")
    conversation = conversation_manager.get_conversation(conv_id)
    assert conversation is not None
    assert conversation["id"] == conv_id
    assert conversation["title"] == "Test"


def test_save_message(conversation_manager):
    """Test saving a message to a conversation."""
    conv_id = conversation_manager.create_conversation(title="Test", model="test-model")
    conversation_manager.save_message(conv_id, "user", "Hello")
    conversation = conversation_manager.get_conversation(conv_id)
    assert len(conversation["messages"]) == 1
    assert conversation["messages"][0]["role"] == "user"
    assert conversation["messages"][0]["content"] == "Hello"


def test_list_conversations(conversation_manager):
    """Test listing conversations."""
    conv1 = conversation_manager.create_conversation(title="Conv 1", model="test-model")
    conv2 = conversation_manager.create_conversation(title="Conv 2", model="test-model")
    conversations = conversation_manager.list_conversations()
    assert len(conversations) >= 2
    ids = [c["id"] for c in conversations]
    assert conv1 in ids
    assert conv2 in ids


def test_update_conversation(conversation_manager):
    """Test updating conversation metadata."""
    conv_id = conversation_manager.create_conversation(title="Old Title", model="test-model")
    success = conversation_manager.update_conversation(conv_id, title="New Title")
    assert success is True
    conversation = conversation_manager.get_conversation(conv_id)
    assert conversation["title"] == "New Title"


def test_delete_conversation(conversation_manager):
    """Test deleting a conversation."""
    conv_id = conversation_manager.create_conversation(title="Test", model="test-model")
    success = conversation_manager.delete_conversation(conv_id)
    assert success is True
    conversation = conversation_manager.get_conversation(conv_id)
    assert conversation is None
