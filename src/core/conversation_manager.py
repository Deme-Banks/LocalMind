"""
Conversation Manager - handles saving, loading, and managing chat conversations
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation storage and retrieval"""
    
    def __init__(self, conversations_dir: Optional[Path] = None):
        """
        Initialize conversation manager
        
        Args:
            conversations_dir: Directory to store conversations (default: conversations/ in project root)
        """
        if conversations_dir is None:
            # Use project root conversations directory
            conversations_dir = Path(__file__).parent.parent.parent / "conversations"
        
        self.conversations_dir = conversations_dir
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file to track all conversations
        self.index_file = self.conversations_dir / "index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure index file exists"""
        if not self.index_file.exists():
            self._save_index({})
    
    def _load_index(self) -> Dict[str, Any]:
        """Load conversation index"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading conversation index: {e}")
            return {}
    
    def _save_index(self, index: Dict[str, Any]):
        """Save conversation index"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving conversation index: {e}")
    
    def create_conversation(self, title: Optional[str] = None, model: Optional[str] = None) -> str:
        """
        Create a new conversation
        
        Args:
            title: Optional title for the conversation
            model: Model used in this conversation
        
        Returns:
            Conversation ID
        """
        conv_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conversation = {
            "id": conv_id,
            "title": title or f"New Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "model": model,
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": []
        }
        
        # Save conversation file
        conv_file = self.conversations_dir / f"{conv_id}.json"
        try:
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
        
        # Update index
        index = self._load_index()
        index[conv_id] = {
            "id": conv_id,
            "title": conversation["title"],
            "model": model,
            "created_at": timestamp,
            "updated_at": timestamp,
            "message_count": 0
        }
        self._save_index(index)
        
        return conv_id
    
    def save_message(self, conv_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Save a message to a conversation
        
        Args:
            conv_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (model, temperature, etc.)
        """
        conv_file = self.conversations_dir / f"{conv_id}.json"
        
        if not conv_file.exists():
            # Create conversation if it doesn't exist
            self.create_conversation(model=metadata.get("model") if metadata else None)
        
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
        except Exception as e:
            logger.error(f"Error loading conversation {conv_id}: {e}")
            return
        
        # Add message
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.now().isoformat()
        
        # Update title from first user message if still default
        if conversation["title"].startswith("New Conversation") and role == "user":
            # Use first 50 chars of first message as title
            title = content[:50].strip()
            if len(content) > 50:
                title += "..."
            conversation["title"] = title
        
        # Save conversation
        try:
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving message to conversation {conv_id}: {e}")
            return
        
        # Update index
        index = self._load_index()
        if conv_id in index:
            index[conv_id]["updated_at"] = conversation["updated_at"]
            index[conv_id]["message_count"] = len(conversation["messages"])
            self._save_index(index)
    
    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID
        
        Args:
            conv_id: Conversation ID
        
        Returns:
            Conversation data or None if not found
        """
        conv_file = self.conversations_dir / f"{conv_id}.json"
        
        if not conv_file.exists():
            return None
        
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading conversation {conv_id}: {e}")
            return None
    
    def list_conversations(self, limit: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all conversations
        
        Args:
            limit: Maximum number of conversations to return
            search: Search term to filter conversations
        
        Returns:
            List of conversation summaries
        """
        index = self._load_index()
        conversations = []
        
        for conv_id, conv_info in index.items():
            # Apply search filter
            if search:
                search_lower = search.lower()
                if (search_lower not in conv_info.get("title", "").lower() and
                    search_lower not in conv_id.lower()):
                    continue
            
            conversations.append(conv_info)
        
        # Sort by updated_at (most recent first)
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # Apply limit
        if limit:
            conversations = conversations[:limit]
        
        return conversations
    
    def update_conversation(self, conv_id: str, title: Optional[str] = None, model: Optional[str] = None):
        """
        Update conversation metadata
        
        Args:
            conv_id: Conversation ID
            title: New title (optional)
            model: Model name (optional)
        """
        conv_file = self.conversations_dir / f"{conv_id}.json"
        
        if not conv_file.exists():
            return False
        
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
        except Exception as e:
            logger.error(f"Error loading conversation {conv_id}: {e}")
            return False
        
        if title:
            conversation["title"] = title
        if model:
            conversation["model"] = model
        
        conversation["updated_at"] = datetime.now().isoformat()
        
        try:
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error updating conversation {conv_id}: {e}")
            return False
        
        # Update index
        index = self._load_index()
        if conv_id in index:
            if title:
                index[conv_id]["title"] = title
            if model:
                index[conv_id]["model"] = model
            index[conv_id]["updated_at"] = conversation["updated_at"]
            self._save_index(index)
        
        return True
    
    def delete_conversation(self, conv_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conv_id: Conversation ID
        
        Returns:
            True if deleted, False otherwise
        """
        conv_file = self.conversations_dir / f"{conv_id}.json"
        
        # Delete conversation file
        if conv_file.exists():
            try:
                conv_file.unlink()
            except Exception as e:
                logger.error(f"Error deleting conversation file {conv_id}: {e}")
                return False
        
        # Remove from index
        index = self._load_index()
        if conv_id in index:
            del index[conv_id]
            self._save_index(index)
        
        return True
    
    def export_conversation(self, conv_id: str, format: str = "json") -> Optional[str]:
        """
        Export a conversation to a string
        
        Args:
            conv_id: Conversation ID
            format: Export format ('json' or 'markdown' or 'text')
        
        Returns:
            Exported conversation as string, or None if error
        """
        conversation = self.get_conversation(conv_id)
        if not conversation:
            return None
        
        if format == "json":
            return json.dumps(conversation, indent=2, ensure_ascii=False)
        elif format == "markdown":
            lines = [f"# {conversation['title']}\n"]
            lines.append(f"**Model:** {conversation.get('model', 'Unknown')}\n")
            lines.append(f"**Created:** {conversation.get('created_at', 'Unknown')}\n")
            lines.append(f"**Updated:** {conversation.get('updated_at', 'Unknown')}\n")
            lines.append("\n---\n\n")
            
            for msg in conversation.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                if role == "user":
                    lines.append(f"## 👤 User ({timestamp})\n\n{content}\n\n")
                elif role == "assistant":
                    lines.append(f"## 🤖 Assistant ({timestamp})\n\n{content}\n\n")
            
            return "\n".join(lines)
        elif format == "text":
            lines = [f"{conversation['title']}"]
            lines.append(f"Model: {conversation.get('model', 'Unknown')}")
            lines.append(f"Created: {conversation.get('created_at', 'Unknown')}")
            lines.append(f"Updated: {conversation.get('updated_at', 'Unknown')}")
            lines.append("\n" + "="*50 + "\n")
            
            for msg in conversation.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                if role == "user":
                    lines.append(f"\nUser ({timestamp}):\n{content}\n")
                elif role == "assistant":
                    lines.append(f"\nAssistant ({timestamp}):\n{content}\n")
            
            return "\n".join(lines)
        
        return None
    
    def import_conversation(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Import a conversation from a dictionary
        
        Args:
            data: Conversation data dictionary
        
        Returns:
            Conversation ID if successful, None otherwise
        """
        conv_id = data.get("id") or str(uuid.uuid4())
        conv_file = self.conversations_dir / f"{conv_id}.json"
        
        # Ensure required fields
        conversation = {
            "id": conv_id,
            "title": data.get("title", f"Imported Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
            "model": data.get("model"),
            "created_at": data.get("created_at", datetime.now().isoformat()),
            "updated_at": data.get("updated_at", datetime.now().isoformat()),
            "messages": data.get("messages", [])
        }
        
        try:
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error importing conversation: {e}")
            return None
        
        # Update index
        index = self._load_index()
        index[conv_id] = {
            "id": conv_id,
            "title": conversation["title"],
            "model": conversation["model"],
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"],
            "message_count": len(conversation["messages"])
        }
        self._save_index(index)
        
        return conv_id

