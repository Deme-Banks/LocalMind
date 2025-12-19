"""
Configuration Backup and Restore - handles backing up and restoring LocalMind configuration
"""

import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import zipfile
import tempfile

logger = logging.getLogger(__name__)


class ConfigBackup:
    """Manages configuration backup and restore"""
    
    def __init__(self, config_manager, conversations_dir: Optional[Path] = None, models_dir: Optional[Path] = None):
        """
        Initialize config backup manager
        
        Args:
            config_manager: ConfigManager instance
            conversations_dir: Directory containing conversations (default: conversations/ in project root)
            models_dir: Directory containing models registry (default: models/ in project root)
        """
        self.config_manager = config_manager
        
        # Determine paths
        project_root = Path(__file__).parent.parent.parent
        self.conversations_dir = conversations_dir or (project_root / "conversations")
        self.models_dir = models_dir or (project_root / "models")
        self.config_path = config_manager.config_path
        
    def create_backup(self, include_conversations: bool = False, include_models: bool = False) -> Dict[str, Any]:
        """
        Create a backup of configuration
        
        Args:
            include_conversations: Whether to include conversations in backup
            include_models: Whether to include model registry in backup
            
        Returns:
            Dictionary with backup data
        """
        backup_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "config": None,
            "conversations": None,
            "model_registry": None
        }
        
        # Backup configuration
        try:
            config = self.config_manager.get_config()
            if config:
                # Convert to dict and handle Path objects
                config_dict = config.dict()
                backup_data["config"] = config_dict
        except Exception as e:
            logger.error(f"Error backing up config: {e}")
            raise
        
        # Backup conversations if requested
        if include_conversations:
            try:
                conversations_data = self._backup_conversations()
                backup_data["conversations"] = conversations_data
            except Exception as e:
                logger.warning(f"Error backing up conversations: {e}")
        
        # Backup model registry if requested
        if include_models:
            try:
                model_registry_data = self._backup_model_registry()
                backup_data["model_registry"] = model_registry_data
            except Exception as e:
                logger.warning(f"Error backing up model registry: {e}")
        
        return backup_data
    
    def _backup_conversations(self) -> Dict[str, Any]:
        """Backup conversations directory"""
        conversations_data = {
            "index": None,
            "conversations": {}
        }
        
        # Backup index file
        index_file = self.conversations_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    conversations_data["index"] = json.load(f)
            except Exception as e:
                logger.warning(f"Error reading conversation index: {e}")
        
        # Backup individual conversations
        if self.conversations_dir.exists():
            for conv_file in self.conversations_dir.glob("*.json"):
                if conv_file.name == "index.json":
                    continue
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        conversations_data["conversations"][conv_file.name] = json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading conversation {conv_file.name}: {e}")
        
        return conversations_data
    
    def _backup_model_registry(self) -> Optional[Dict[str, Any]]:
        """Backup model registry"""
        registry_file = self.models_dir / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading model registry: {e}")
        return None
    
    def export_backup(self, output_path: Path, include_conversations: bool = False, include_models: bool = False) -> Path:
        """
        Export backup to a file
        
        Args:
            output_path: Path to save backup file
            include_conversations: Whether to include conversations
            include_models: Whether to include model registry
            
        Returns:
            Path to created backup file
        """
        backup_data = self.create_backup(
            include_conversations=include_conversations,
            include_models=include_models
        )
        
        # Determine file extension
        if output_path.suffix.lower() == '.zip':
            # Create ZIP archive
            return self._export_zip_backup(backup_data, output_path, include_conversations, include_models)
        else:
            # Export as JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            return output_path
    
    def _export_zip_backup(self, backup_data: Dict[str, Any], output_path: Path, include_conversations: bool, include_models: bool) -> Path:
        """Export backup as ZIP archive"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add main backup data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                json.dump(backup_data, tmp, indent=2, ensure_ascii=False)
                tmp_path = Path(tmp.name)
            
            zipf.write(tmp_path, 'backup.json')
            tmp_path.unlink()
            
            # Add conversations if included
            if include_conversations and backup_data.get("conversations"):
                for conv_name, conv_data in backup_data["conversations"].items():
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                        json.dump(conv_data, tmp, indent=2, ensure_ascii=False)
                        tmp_path = Path(tmp.name)
                    zipf.write(tmp_path, f'conversations/{conv_name}')
                    tmp_path.unlink()
        
        return output_path
    
    def restore_backup(self, backup_data: Dict[str, Any], restore_conversations: bool = False, restore_models: bool = False) -> Dict[str, Any]:
        """
        Restore configuration from backup
        
        Args:
            backup_data: Backup data dictionary
            restore_conversations: Whether to restore conversations
            restore_models: Whether to restore model registry
            
        Returns:
            Dictionary with restore results
        """
        results = {
            "config": False,
            "conversations": False,
            "model_registry": False,
            "errors": []
        }
        
        # Restore configuration
        if backup_data.get("config"):
            try:
                # Load config from backup
                config_dict = backup_data["config"]
                
                # Convert storage_path string back to Path if needed
                if "storage_path" in config_dict and isinstance(config_dict["storage_path"], str):
                    config_dict["storage_path"] = Path(config_dict["storage_path"])
                
                # Create config object and save
                from ..utils.config import LocalMindConfig
                restored_config = LocalMindConfig(**config_dict)
                self.config_manager.config = restored_config
                self.config_manager.save_config()
                
                results["config"] = True
            except Exception as e:
                error_msg = f"Error restoring config: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Restore conversations if requested
        if restore_conversations and backup_data.get("conversations"):
            try:
                self._restore_conversations(backup_data["conversations"])
                results["conversations"] = True
            except Exception as e:
                error_msg = f"Error restoring conversations: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Restore model registry if requested
        if restore_models and backup_data.get("model_registry"):
            try:
                self._restore_model_registry(backup_data["model_registry"])
                results["model_registry"] = True
            except Exception as e:
                error_msg = f"Error restoring model registry: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    def _restore_conversations(self, conversations_data: Dict[str, Any]):
        """Restore conversations from backup"""
        # Ensure conversations directory exists
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # Restore index
        if conversations_data.get("index"):
            index_file = self.conversations_dir / "index.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(conversations_data["index"], f, indent=2, ensure_ascii=False)
        
        # Restore individual conversations
        if conversations_data.get("conversations"):
            for conv_name, conv_data in conversations_data["conversations"].items():
                conv_file = self.conversations_dir / conv_name
                with open(conv_file, 'w', encoding='utf-8') as f:
                    json.dump(conv_data, f, indent=2, ensure_ascii=False)
    
    def _restore_model_registry(self, registry_data: Dict[str, Any]):
        """Restore model registry from backup"""
        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        registry_file = self.models_dir / "registry.json"
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, indent=2, ensure_ascii=False)
    
    def import_backup_file(self, backup_path: Path) -> Dict[str, Any]:
        """
        Import backup from file
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Backup data dictionary
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        if backup_path.suffix.lower() == '.zip':
            return self._import_zip_backup(backup_path)
        else:
            # Import from JSON
            with open(backup_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def _import_zip_backup(self, zip_path: Path) -> Dict[str, Any]:
        """Import backup from ZIP archive"""
        backup_data = {}
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Extract main backup file
            if 'backup.json' in zipf.namelist():
                with zipf.open('backup.json') as f:
                    backup_data = json.load(f)
            
            # Extract conversations if present
            conversations = {}
            for name in zipf.namelist():
                if name.startswith('conversations/') and name.endswith('.json'):
                    conv_name = name.split('/')[-1]
                    with zipf.open(name) as f:
                        conversations[conv_name] = json.load(f)
            
            if conversations:
                if "conversations" not in backup_data:
                    backup_data["conversations"] = {}
                backup_data["conversations"]["conversations"] = conversations
        
        return backup_data

