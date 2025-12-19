"""
Migration Tools - handles migration from other tools and LocalMind version upgrades
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import shutil

logger = logging.getLogger(__name__)


class MigrationTool:
    """Handles migrations from other tools and version upgrades"""
    
    def __init__(self, config_manager, conversation_manager, model_registry):
        """
        Initialize migration tool
        
        Args:
            config_manager: ConfigManager instance
            conversation_manager: ConversationManager instance
            model_registry: ModelRegistry instance
        """
        self.config_manager = config_manager
        self.conversation_manager = conversation_manager
        self.model_registry = model_registry
    
    def detect_migration_sources(self) -> List[Dict[str, Any]]:
        """
        Detect available migration sources (other AI tools)
        
        Returns:
            List of detected migration sources with metadata
        """
        sources = []
        
        # Check for common AI tool data locations
        home = Path.home()
        
        # Check for ChatGPT exports (common locations)
        chatgpt_paths = [
            home / "Downloads" / "chatgpt_export.json",
            home / "Downloads" / "chatgpt_conversations.json",
            home / "Documents" / "ChatGPT" / "conversations.json",
        ]
        
        for path in chatgpt_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if self._is_chatgpt_format(data):
                            sources.append({
                                "type": "chatgpt",
                                "name": "ChatGPT Export",
                                "path": str(path),
                                "conversation_count": len(data) if isinstance(data, list) else 1,
                                "detected_at": datetime.now().isoformat()
                            })
                except Exception as e:
                    logger.debug(f"Error checking {path}: {e}")
        
        # Check for Claude/Anthropic exports
        claude_paths = [
            home / "Downloads" / "claude_export.json",
            home / "Downloads" / "anthropic_export.json",
        ]
        
        for path in claude_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if self._is_claude_format(data):
                            sources.append({
                                "type": "claude",
                                "name": "Claude/Anthropic Export",
                                "path": str(path),
                                "conversation_count": len(data.get("conversations", [])) if isinstance(data, dict) else 1,
                                "detected_at": datetime.now().isoformat()
                            })
                except Exception as e:
                    logger.debug(f"Error checking {path}: {e}")
        
        # Check for Ollama history (if migrating from another Ollama setup)
        ollama_history = home / ".ollama" / "history"
        if ollama_history.exists():
            sources.append({
                "type": "ollama_history",
                "name": "Ollama Chat History",
                "path": str(ollama_history),
                "detected_at": datetime.now().isoformat()
            })
        
        return sources
    
    def _is_chatgpt_format(self, data: Any) -> bool:
        """Check if data is in ChatGPT export format"""
        if isinstance(data, list):
            return len(data) > 0 and isinstance(data[0], dict) and "title" in data[0]
        return False
    
    def _is_claude_format(self, data: Any) -> bool:
        """Check if data is in Claude/Anthropic format"""
        if isinstance(data, dict):
            return "conversations" in data or "messages" in data
        return False
    
    def migrate_from_source(self, source_type: str, source_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Migrate data from a detected source
        
        Args:
            source_type: Type of source (chatgpt, claude, ollama_history, etc.)
            source_path: Path to source data
            options: Migration options (preserve_dates, merge_existing, etc.)
            
        Returns:
            Migration results with statistics
        """
        options = options or {}
        results = {
            "success": False,
            "conversations_migrated": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            if source_type == "chatgpt":
                results = self._migrate_chatgpt(source_path, options)
            elif source_type == "claude":
                results = self._migrate_claude(source_path, options)
            elif source_type == "ollama_history":
                results = self._migrate_ollama_history(source_path, options)
            else:
                results["errors"].append(f"Unknown source type: {source_type}")
        except Exception as e:
            logger.error(f"Error migrating from {source_type}: {e}", exc_info=True)
            results["errors"].append(str(e))
        
        results["success"] = len(results["errors"]) == 0
        return results
    
    def _migrate_chatgpt(self, source_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from ChatGPT export format"""
        results = {
            "conversations_migrated": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                results["errors"].append("Invalid ChatGPT export format")
                return results
            
            for conv_data in data:
                try:
                    # Extract conversation data
                    title = conv_data.get("title", "Imported ChatGPT Conversation")
                    messages = conv_data.get("mapping", {})
                    
                    # Convert ChatGPT format to LocalMind format
                    localmind_messages = []
                    for msg_id, msg_data in messages.items():
                        if not isinstance(msg_data, dict):
                            continue
                        
                        message = msg_data.get("message")
                        if not message:
                            continue
                        
                        role = message.get("author", {}).get("role", "user")
                        if role == "user":
                            role = "user"
                        elif role == "assistant":
                            role = "assistant"
                        else:
                            continue
                        
                        content = message.get("content", {}).get("parts", [])
                        if content and isinstance(content, list):
                            text = "\n".join([str(part) for part in content if isinstance(part, str)])
                        else:
                            text = str(content) if content else ""
                        
                        if text:
                            localmind_messages.append({
                                "role": role,
                                "content": text,
                                "timestamp": message.get("create_time")
                            })
                    
                    if localmind_messages:
                        # Save conversation
                        conv_id = self.conversation_manager.save_conversation(
                            title=title,
                            messages=localmind_messages,
                            model="Unknown (ChatGPT)"
                        )
                        results["conversations_migrated"] += 1
                except Exception as e:
                    results["warnings"].append(f"Error migrating conversation: {e}")
                    logger.warning(f"Error migrating ChatGPT conversation: {e}")
        
        except Exception as e:
            results["errors"].append(f"Error reading ChatGPT export: {e}")
        
        return results
    
    def _migrate_claude(self, source_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from Claude/Anthropic export format"""
        results = {
            "conversations_migrated": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different Claude export formats
            conversations = []
            if isinstance(data, list):
                conversations = data
            elif isinstance(data, dict):
                conversations = data.get("conversations", [data])
            
            for conv_data in conversations:
                try:
                    # Extract messages
                    messages = conv_data.get("messages", [])
                    if not messages:
                        continue
                    
                    # Convert to LocalMind format
                    localmind_messages = []
                    for msg in messages:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        
                        # Handle Anthropic content format (can be string or array)
                        if isinstance(content, list):
                            text_parts = []
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                            content = "\n".join(text_parts)
                        
                        localmind_messages.append({
                            "role": role,
                            "content": str(content),
                            "timestamp": msg.get("timestamp")
                        })
                    
                    if localmind_messages:
                        title = conv_data.get("title", "Imported Claude Conversation")
                        conv_id = self.conversation_manager.save_conversation(
                            title=title,
                            messages=localmind_messages,
                            model="Unknown (Claude)"
                        )
                        results["conversations_migrated"] += 1
                except Exception as e:
                    results["warnings"].append(f"Error migrating conversation: {e}")
                    logger.warning(f"Error migrating Claude conversation: {e}")
        
        except Exception as e:
            results["errors"].append(f"Error reading Claude export: {e}")
        
        return results
    
    def _migrate_ollama_history(self, source_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from Ollama chat history"""
        results = {
            "conversations_migrated": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            history_path = Path(source_path)
            if history_path.is_file():
                # Single history file
                with open(history_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    results = self._process_ollama_history(history_data, options)
            elif history_path.is_dir():
                # Directory of history files
                for hist_file in history_path.glob("*.json"):
                    try:
                        with open(hist_file, 'r', encoding='utf-8') as f:
                            history_data = json.load(f)
                            sub_results = self._process_ollama_history(history_data, options)
                            results["conversations_migrated"] += sub_results["conversations_migrated"]
                            results["warnings"].extend(sub_results["warnings"])
                    except Exception as e:
                        results["warnings"].append(f"Error processing {hist_file.name}: {e}")
        except Exception as e:
            results["errors"].append(f"Error reading Ollama history: {e}")
        
        return results
    
    def _process_ollama_history(self, history_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Process Ollama history data"""
        results = {
            "conversations_migrated": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Ollama history format varies, try to extract conversations
            if isinstance(history_data, list):
                # List of conversations
                for conv in history_data:
                    if isinstance(conv, dict) and "messages" in conv:
                        messages = conv.get("messages", [])
                        title = conv.get("title", "Imported Ollama Conversation")
                        model = conv.get("model", "Unknown")
                        
                        conv_id = self.conversation_manager.save_conversation(
                            title=title,
                            messages=messages,
                            model=model
                        )
                        results["conversations_migrated"] += 1
            elif isinstance(history_data, dict):
                # Single conversation or nested structure
                if "messages" in history_data:
                    messages = history_data.get("messages", [])
                    title = history_data.get("title", "Imported Ollama Conversation")
                    model = history_data.get("model", "Unknown")
                    
                    conv_id = self.conversation_manager.save_conversation(
                        title=title,
                        messages=messages,
                        model=model
                    )
                    results["conversations_migrated"] += 1
        except Exception as e:
            results["errors"].append(f"Error processing Ollama history: {e}")
        
        return results
    
    def upgrade_config_version(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Upgrade configuration from one version to another
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            Upgrade results
        """
        results = {
            "success": False,
            "upgraded": False,
            "changes": [],
            "errors": []
        }
        
        try:
            config = self.config_manager.get_config()
            
            # Version-specific upgrade logic
            if from_version < "2.0" and to_version >= "2.0":
                # Upgrade to v2.0 format
                results["changes"].append("Upgraded to v2.0 configuration format")
                # Add any v2.0 specific changes here
            
            # Save upgraded config
            self.config_manager.save_config()
            results["upgraded"] = True
            results["success"] = True
        
        except Exception as e:
            logger.error(f"Error upgrading config: {e}", exc_info=True)
            results["errors"].append(str(e))
        
        return results
    
    def validate_migration(self, source_type: str, source_path: str) -> Dict[str, Any]:
        """
        Validate a migration source before migrating
        
        Args:
            source_type: Type of source
            source_path: Path to source data
            
        Returns:
            Validation results
        """
        validation = {
            "valid": False,
            "conversation_count": 0,
            "format": None,
            "errors": [],
            "warnings": []
        }
        
        try:
            path = Path(source_path)
            if not path.exists():
                validation["errors"].append(f"Source path does not exist: {source_path}")
                return validation
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if source_type == "chatgpt":
                if self._is_chatgpt_format(data):
                    validation["valid"] = True
                    validation["format"] = "chatgpt"
                    validation["conversation_count"] = len(data) if isinstance(data, list) else 1
                else:
                    validation["errors"].append("Invalid ChatGPT export format")
            elif source_type == "claude":
                if self._is_claude_format(data):
                    validation["valid"] = True
                    validation["format"] = "claude"
                    if isinstance(data, dict):
                        validation["conversation_count"] = len(data.get("conversations", []))
                    else:
                        validation["conversation_count"] = 1
                else:
                    validation["errors"].append("Invalid Claude export format")
            else:
                validation["warnings"].append(f"Unknown source type: {source_type}")
        
        except json.JSONDecodeError:
            validation["errors"].append("Invalid JSON format")
        except Exception as e:
            validation["errors"].append(f"Error validating source: {e}")
        
        return validation

