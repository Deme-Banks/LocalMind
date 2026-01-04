"""
Shared Context Manager - Allows chat and video features to share information
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SharedContextManager:
    """Manages shared context between chat and video features"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize shared context manager
        
        Args:
            storage_path: Path to store shared context (default: shared_context.json in project root)
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "shared_context.json"
        
        self.storage_path = storage_path
        self.context: Dict[str, Any] = self._load_context()
    
    def _load_context(self) -> Dict[str, Any]:
        """Load shared context from file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading shared context: {e}")
                return self._default_context()
        return self._default_context()
    
    def _default_context(self) -> Dict[str, Any]:
        """Get default context structure"""
        return {
            "chat_to_video": [],  # Chat prompts that can be used for video
            "video_to_chat": [],  # Video prompts that can be referenced in chat
            "shared_prompts": [],  # Prompts shared between features
            "cross_references": []  # References between chat and video
        }
    
    def _save_context(self):
        """Save shared context to file"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving shared context: {e}")
    
    def add_chat_prompt(self, prompt: str, conversation_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Add a chat prompt that can be used for video generation
        
        Args:
            prompt: Chat prompt text
            conversation_id: Optional conversation ID
            metadata: Optional metadata
        """
        entry = {
            "prompt": prompt,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.context["chat_to_video"].append(entry)
        # Keep only last 100
        self.context["chat_to_video"] = self.context["chat_to_video"][-100:]
        self._save_context()
    
    def add_video_prompt(self, prompt: str, video_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Add a video prompt that can be referenced in chat
        
        Args:
            prompt: Video prompt text
            video_id: Optional video ID
            metadata: Optional metadata
        """
        entry = {
            "prompt": prompt,
            "video_id": video_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.context["video_to_chat"].append(entry)
        # Keep only last 100
        self.context["video_to_chat"] = self.context["video_to_chat"][-100:]
        self._save_context()
    
    def link_chat_to_video(self, conversation_id: str, video_id: str, description: Optional[str] = None):
        """
        Create a link between a chat conversation and a video
        
        Args:
            conversation_id: Chat conversation ID
            video_id: Video ID
            description: Optional description of the link
        """
        link = {
            "conversation_id": conversation_id,
            "video_id": video_id,
            "timestamp": datetime.now().isoformat(),
            "description": description
        }
        self.context["cross_references"].append(link)
        # Keep only last 200
        self.context["cross_references"] = self.context["cross_references"][-200:]
        self._save_context()
    
    def get_chat_prompts_for_video(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat prompts that can be used for video generation"""
        return self.context["chat_to_video"][-limit:]
    
    def get_video_prompts_for_chat(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent video prompts that can be referenced in chat"""
        return self.context["video_to_chat"][-limit:]
    
    def get_related_videos(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get videos related to a conversation"""
        return [
            ref for ref in self.context["cross_references"]
            if ref.get("conversation_id") == conversation_id
        ]
    
    def get_related_conversations(self, video_id: str) -> List[Dict[str, Any]]:
        """Get conversations related to a video"""
        return [
            ref for ref in self.context["cross_references"]
            if ref.get("video_id") == video_id
        ]
    
    def search_prompts(self, query: str, limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search prompts across both chat and video
        
        Args:
            query: Search query
            limit: Maximum results per category
        
        Returns:
            Dictionary with 'chat' and 'video' lists
        """
        query_lower = query.lower()
        
        chat_results = [
            entry for entry in self.context["chat_to_video"]
            if query_lower in entry.get("prompt", "").lower()
        ][-limit:]
        
        video_results = [
            entry for entry in self.context["video_to_chat"]
            if query_lower in entry.get("prompt", "").lower()
        ][-limit:]
        
        return {
            "chat": chat_results,
            "video": video_results
        }

