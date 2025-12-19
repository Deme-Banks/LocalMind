"""
Plugin Manager - manages third-party plugins/extensions for LocalMind
"""

import json
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import shutil
import zipfile
import tempfile

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages third-party plugins"""
    
    def __init__(self, plugins_dir: Optional[Path] = None, config_file: Optional[Path] = None):
        """
        Initialize plugin manager
        
        Args:
            plugins_dir: Directory for third-party plugins (default: plugins/ in project root)
            config_file: Path to plugins configuration file
        """
        project_root = Path(__file__).parent.parent.parent
        
        if plugins_dir is None:
            plugins_dir = project_root / "plugins"
        
        if config_file is None:
            config_file = project_root / "plugins.json"
        
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = config_file
        self.plugins: Dict[str, Dict[str, Any]] = self._load_plugins_config()
        self.loaded_plugins: Dict[str, Any] = {}
    
    def _load_plugins_config(self) -> Dict[str, Dict[str, Any]]:
        """Load plugins configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading plugins config: {e}")
                return {}
        return {}
    
    def _save_plugins_config(self):
        """Save plugins configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugins, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving plugins config: {e}")
    
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        Discover plugins in the plugins directory
        
        Returns:
            List of discovered plugins with metadata
        """
        discovered = []
        
        if not self.plugins_dir.exists():
            return discovered
        
        # Look for plugin directories
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            plugin_id = plugin_dir.name
            
            # Check for plugin.json manifest
            manifest_file = plugin_dir / "plugin.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    
                    plugin_info = {
                        "id": plugin_id,
                        "name": manifest.get("name", plugin_id),
                        "version": manifest.get("version", "1.0.0"),
                        "description": manifest.get("description", ""),
                        "author": manifest.get("author", ""),
                        "entry_point": manifest.get("entry_point", "plugin.py"),
                        "enabled": self.plugins.get(plugin_id, {}).get("enabled", True),
                        "installed": True,
                        "path": str(plugin_dir),
                        "manifest": manifest
                    }
                    
                    discovered.append(plugin_info)
                except Exception as e:
                    logger.warning(f"Error reading manifest for {plugin_id}: {e}")
        
        return discovered
    
    def install_plugin(self, plugin_path: Path, plugin_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Install a plugin from a file or directory
        
        Args:
            plugin_path: Path to plugin file (zip) or directory
            plugin_id: Optional plugin ID (auto-detected if not provided)
            
        Returns:
            Installation result
        """
        result = {
            "success": False,
            "plugin_id": None,
            "message": "",
            "errors": []
        }
        
        try:
            # Handle ZIP file
            if plugin_path.suffix == ".zip":
                return self._install_from_zip(plugin_path, plugin_id)
            
            # Handle directory
            if plugin_path.is_dir():
                return self._install_from_directory(plugin_path, plugin_id)
            
            result["errors"].append("Invalid plugin format. Expected .zip file or directory.")
            return result
        
        except Exception as e:
            logger.error(f"Error installing plugin: {e}", exc_info=True)
            result["errors"].append(str(e))
            return result
    
    def _install_from_zip(self, zip_path: Path, plugin_id: Optional[str] = None) -> Dict[str, Any]:
        """Install plugin from ZIP file"""
        result = {
            "success": False,
            "plugin_id": None,
            "message": "",
            "errors": []
        }
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Extract manifest first
                if "plugin.json" not in zipf.namelist():
                    result["errors"].append("plugin.json not found in ZIP file")
                    return result
                
                # Read manifest
                manifest_data = zipf.read("plugin.json")
                manifest = json.loads(manifest_data.decode('utf-8'))
                
                # Determine plugin ID
                if not plugin_id:
                    plugin_id = manifest.get("id") or manifest.get("name", zip_path.stem)
                
                # Create plugin directory
                plugin_dir = self.plugins_dir / plugin_id
                plugin_dir.mkdir(parents=True, exist_ok=True)
                
                # Extract all files
                zipf.extractall(plugin_dir)
                
                # Register plugin
                self.plugins[plugin_id] = {
                    "name": manifest.get("name", plugin_id),
                    "version": manifest.get("version", "1.0.0"),
                    "enabled": True,
                    "installed_at": datetime.now().isoformat(),
                    "path": str(plugin_dir)
                }
                
                self._save_plugins_config()
                
                result["success"] = True
                result["plugin_id"] = plugin_id
                result["message"] = f"Plugin '{plugin_id}' installed successfully"
                
                return result
        
        except Exception as e:
            logger.error(f"Error installing from ZIP: {e}", exc_info=True)
            result["errors"].append(str(e))
            return result
    
    def _install_from_directory(self, source_dir: Path, plugin_id: Optional[str] = None) -> Dict[str, Any]:
        """Install plugin from directory"""
        result = {
            "success": False,
            "plugin_id": None,
            "message": "",
            "errors": []
        }
        
        try:
            # Check for manifest
            manifest_file = source_dir / "plugin.json"
            if not manifest_file.exists():
                result["errors"].append("plugin.json not found")
                return result
            
            # Read manifest
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Determine plugin ID
            if not plugin_id:
                plugin_id = manifest.get("id") or manifest.get("name", source_dir.name)
            
            # Create plugin directory
            plugin_dir = self.plugins_dir / plugin_id
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            for item in source_dir.iterdir():
                if item.name == "__pycache__" or item.name.endswith(".pyc"):
                    continue
                if item.is_file():
                    shutil.copy2(item, plugin_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, plugin_dir / item.name, dirs_exist_ok=True)
            
            # Register plugin
            self.plugins[plugin_id] = {
                "name": manifest.get("name", plugin_id),
                "version": manifest.get("version", "1.0.0"),
                "enabled": True,
                "installed_at": datetime.now().isoformat(),
                "path": str(plugin_dir)
            }
            
            self._save_plugins_config()
            
            result["success"] = True
            result["plugin_id"] = plugin_id
            result["message"] = f"Plugin '{plugin_id}' installed successfully"
            
            return result
        
        except Exception as e:
            logger.error(f"Error installing from directory: {e}", exc_info=True)
            result["errors"].append(str(e))
            return result
    
    def uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """
        Uninstall a plugin
        
        Args:
            plugin_id: Plugin ID to uninstall
            
        Returns:
            Uninstallation result
        """
        result = {
            "success": False,
            "message": "",
            "errors": []
        }
        
        try:
            if plugin_id not in self.plugins:
                result["errors"].append(f"Plugin '{plugin_id}' not found")
                return result
            
            # Unload plugin if loaded
            if plugin_id in self.loaded_plugins:
                del self.loaded_plugins[plugin_id]
            
            # Remove plugin directory
            plugin_dir = self.plugins_dir / plugin_id
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
            
            # Remove from config
            del self.plugins[plugin_id]
            self._save_plugins_config()
            
            result["success"] = True
            result["message"] = f"Plugin '{plugin_id}' uninstalled successfully"
            
            return result
        
        except Exception as e:
            logger.error(f"Error uninstalling plugin: {e}", exc_info=True)
            result["errors"].append(str(e))
            return result
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = True
            self._save_plugins_config()
            return True
        return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = False
            self._save_plugins_config()
            # Unload if loaded
            if plugin_id in self.loaded_plugins:
                del self.loaded_plugins[plugin_id]
            return True
        return False
    
    def load_plugin(self, plugin_id: str) -> Optional[Any]:
        """
        Load a plugin module
        
        Args:
            plugin_id: Plugin ID to load
            
        Returns:
            Loaded plugin module or None
        """
        if plugin_id in self.loaded_plugins:
            return self.loaded_plugins[plugin_id]
        
        if plugin_id not in self.plugins:
            logger.warning(f"Plugin '{plugin_id}' not found")
            return None
        
        plugin_info = self.plugins[plugin_id]
        if not plugin_info.get("enabled", True):
            logger.warning(f"Plugin '{plugin_id}' is disabled")
            return None
        
        try:
            plugin_dir = Path(plugin_info["path"])
            manifest_file = plugin_dir / "plugin.json"
            
            if not manifest_file.exists():
                logger.error(f"Manifest not found for plugin '{plugin_id}'")
                return None
            
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            entry_point = manifest.get("entry_point", "plugin.py")
            entry_file = plugin_dir / entry_point
            
            if not entry_file.exists():
                logger.error(f"Entry point '{entry_point}' not found for plugin '{plugin_id}'")
                return None
            
            # Load module
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_id}", entry_file)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load plugin '{plugin_id}'")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.loaded_plugins[plugin_id] = module
            
            logger.info(f"Plugin '{plugin_id}' loaded successfully")
            return module
        
        except Exception as e:
            logger.error(f"Error loading plugin '{plugin_id}': {e}", exc_info=True)
            return None
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin information"""
        if plugin_id not in self.plugins:
            return None
        
        plugin_info = self.plugins[plugin_id].copy()
        plugin_dir = Path(plugin_info["path"])
        
        # Load manifest if available
        manifest_file = plugin_dir / "plugin.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                plugin_info["manifest"] = manifest
            except Exception:
                pass
        
        return plugin_info
    
    def list_plugins(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all plugins
        
        Args:
            enabled_only: Only return enabled plugins
            
        Returns:
            List of plugin information
        """
        plugins = []
        
        # Get discovered plugins
        discovered = self.discover_plugins()
        
        for plugin_info in discovered:
            if enabled_only and not plugin_info.get("enabled", True):
                continue
            plugins.append(plugin_info)
        
        return plugins

