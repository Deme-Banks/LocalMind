"""
Web server for LocalMind
Provides REST API and web interface
"""

import os
import json
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file
from flask_cors import CORS
import logging

from ..core.model_loader import ModelLoader
from ..core.model_registry import ModelRegistry
from ..core.conversation_manager import ConversationManager
from ..core.context_manager import ContextManager
from ..core.module_loader import ModuleLoader
from ..core.batch_processor import BatchProcessor, BatchRequest
from ..core.usage_tracker import UsageTracker
from ..core.resource_monitor import ResourceMonitor
from ..core.resource_cleanup import ResourceCleanup
from ..core.ensemble import EnsembleProcessor
from ..core.model_router import ModelRouter
from ..core.conversation_importer import ConversationImporter
from ..core.config_backup import ConfigBackup
from ..core.migration_tools import MigrationTool
from ..core.webhook_manager import WebhookManager, WebhookEvent
from ..core.plugin_manager import PluginManager
from ..core.streaming_enhancer import StreamingEnhancer, TokenVisualizer
from ..utils.config import ConfigManager
from ..utils.logger import setup_logger

logger = setup_logger()


class WebServer:
    """Web server for LocalMind"""
    
    def __init__(self, config_manager: ConfigManager, host: str = "0.0.0.0", port: int = 5000):
        """
        Initialize web server
        
        Args:
            config_manager: Configuration manager
            host: Host to bind to (0.0.0.0 for all interfaces)
            port: Port to listen on
        """
        self.config_manager = config_manager
        self.model_loader = ModelLoader(config_manager)
        self.model_registry = ModelRegistry()
        self.conversation_manager = ConversationManager()
        self.context_manager = ContextManager()
        self.module_loader = ModuleLoader()
        self.usage_tracker = UsageTracker()
        self.resource_monitor = ResourceMonitor()
        self.resource_cleanup = ResourceCleanup()
        self.ensemble_processor = EnsembleProcessor()
        self.model_router = ModelRouter()
        self.conversation_importer = ConversationImporter()
        self.config_backup = ConfigBackup(
            config_manager=self.config_manager,
            conversations_dir=self.conversation_manager.conversations_dir,
            models_dir=self.model_registry.registry_path.parent
        )
        self.migration_tool = MigrationTool(
            config_manager=self.config_manager,
            conversation_manager=self.conversation_manager,
            model_registry=self.model_registry
        )
        self.webhook_manager = WebhookManager()
        self.plugin_manager = PluginManager()
        self.streaming_enhancer = StreamingEnhancer()
        self.token_visualizer = TokenVisualizer()
        self.host = host
        self.port = port
        
        # Create Flask app
        self.app = Flask(
            __name__,
            template_folder=Path(__file__).parent / "templates",
            static_folder=Path(__file__).parent / "static"
        )
        CORS(self.app)
        
        # Setup routes
        self._setup_routes()
        
        # Track download progress
        self.download_progress: Dict[str, Dict[str, Any]] = {}
        
        # Track current conversation per session (simple in-memory store)
        # In production, use Flask sessions
        self.current_conversations: Dict[str, str] = {}
    
    def _get_api_setup_url(self, backend_name: str) -> str:
        """Get API setup URL for a backend"""
        urls = {
            "openai": "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com/",
            "google": "https://makersuite.google.com/app/apikey",
            "mistral-ai": "https://console.mistral.ai/",
            "cohere": "https://dashboard.cohere.com/api-keys",
            "groq": "https://console.groq.com/keys"
        }
        return urls.get(backend_name, "")
    
    def _get_backend_display_name(self, backend_name: str) -> str:
        """Get display name for a backend"""
        names = {
            "openai": "OpenAI (ChatGPT)",
            "anthropic": "Anthropic (Claude)",
            "google": "Google (Gemini)",
            "mistral-ai": "Mistral AI",
            "cohere": "Cohere",
            "groq": "Groq (Fast Inference)",
            "ollama": "Ollama (Local)"
        }
        return names.get(backend_name, backend_name.capitalize())
    
    def _error_response(self, message: str, status_code: int = 500, error_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        """
        Create a standardized error response
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_type: Optional error type (e.g., 'validation', 'not_found', 'server_error')
            details: Optional additional error details
            
        Returns:
            Tuple of (JSON response dict, status code)
        """
        response = {
            "status": "error",
            "message": message
        }
        if error_type:
            response["error_type"] = error_type
        if details:
            response["details"] = details
        return response, status_code
    
    def _success_response(self, data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a standardized success response
        
        Args:
            data: Optional data to include
            message: Optional success message
            
        Returns:
            JSON response dict
        """
        response = {"status": "ok"}
        if message:
            response["message"] = message
        if data:
            response.update(data)
        return response
    
    def _setup_routes(self):
        """Setup all routes"""
        
        @self.app.route("/")
        def index():
            """Serve main page"""
            return render_template("index.html")
        
        @self.app.route("/configure")
        def configure_page():
            """Serve API configuration page"""
            return render_template("configure.html")
        
        @self.app.route("/api/changelog", methods=["GET"])
        def api_changelog():
            """Get changelog content"""
            try:
                changelog_path = Path(__file__).parent.parent.parent / "CHANGELOG.md"
                if changelog_path.exists():
                    with open(changelog_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return jsonify({
                        "status": "ok",
                        "changelog": content
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Changelog not found"
                    }), 404
            except Exception as e:
                logger.error(f"Error reading changelog: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/config/backup", methods=["POST"])
        def api_backup_config() -> Tuple[Dict[str, Any], int]:
            """Create a backup of configuration"""
            try:
                data = request.get_json() or {}
                include_conversations = data.get("include_conversations", False)
                include_models = data.get("include_models", False)
                format_type = data.get("format", "json")  # json or download
                
                # Create backup
                backup_data = self.config_backup.create_backup(
                    include_conversations=include_conversations,
                    include_models=include_models
                )
                
                # Return backup data or save to file
                if format_type == "download":
                    # Create temporary file
                    import tempfile
                    if include_conversations or include_models:
                        suffix = ".zip"
                    else:
                        suffix = ".json"
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as tmp:
                        tmp_path = Path(tmp.name)
                    
                    # Export backup
                    self.config_backup.export_backup(
                        tmp_path,
                        include_conversations=include_conversations,
                        include_models=include_models
                    )
                    
                    # Return file path for download
                    return jsonify(self._success_response({
                        "backup_file": tmp_path.name,
                        "download_url": f"/api/config/backup/download/{tmp_path.name}",
                        "backup_info": {
                            "created_at": backup_data.get("created_at"),
                            "includes_conversations": include_conversations,
                            "includes_models": include_models
                        }
                    }))
                else:
                    # Return backup data directly
                    return jsonify(self._success_response(backup_data))
            except Exception as e:
                logger.error(f"Error creating backup: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/config/backup/download/<filename>", methods=["GET"])
        def api_download_backup(filename: str):
            """Download backup file"""
            try:
                import tempfile
                tmp_dir = Path(tempfile.gettempdir())
                backup_path = tmp_dir / filename
                
                if not backup_path.exists():
                    return jsonify(self._error_response("Backup file not found", status_code=404, error_type="not_found")), 404
                
                return send_file(
                    str(backup_path),
                    as_attachment=True,
                    download_name=f"localmind_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{backup_path.suffix}"
                )
            except Exception as e:
                logger.error(f"Error downloading backup: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/config/restore", methods=["POST"])
        def api_restore_config() -> Tuple[Dict[str, Any], int]:
            """Restore configuration from backup"""
            try:
                # Check if it's a file upload or JSON data
                if 'file' in request.files:
                    # File upload
                    file = request.files['file']
                    if file.filename == '':
                        return jsonify(self._error_response("No file selected", status_code=400, error_type="validation"))
                    
                    # Save uploaded file temporarily
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                        file.save(tmp.name)
                        tmp_path = Path(tmp.name)
                    
                    try:
                        # Import backup
                        backup_data = self.config_backup.import_backup_file(tmp_path)
                    finally:
                        # Clean up temp file
                        tmp_path.unlink()
                else:
                    # JSON data in request body
                    data = request.get_json()
                    if not data:
                        return jsonify(self._error_response("No backup data provided", status_code=400, error_type="validation"))
                    backup_data = data
                
                # Get restore options
                restore_conversations = request.form.get('restore_conversations', 'false').lower() == 'true' or \
                                      (request.get_json() or {}).get('restore_conversations', False)
                restore_models = request.form.get('restore_models', 'false').lower() == 'true' or \
                               (request.get_json() or {}).get('restore_models', False)
                
                # Restore backup
                results = self.config_backup.restore_backup(
                    backup_data,
                    restore_conversations=restore_conversations,
                    restore_models=restore_models
                )
                
                if results["errors"]:
                    return jsonify(self._success_response({
                        "message": "Restore completed with some errors",
                        "results": results
                    }))
                else:
                    return jsonify(self._success_response({
                        "message": "Configuration restored successfully",
                        "results": results
                    }))
            except Exception as e:
                logger.error(f"Error restoring backup: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        # Webhook Management Endpoints
        @self.app.route("/api/webhooks", methods=["GET"])
        def api_list_webhooks() -> Tuple[Dict[str, Any], int]:
            """List all webhooks"""
            try:
                enabled_only = request.args.get("enabled_only", "false").lower() == "true"
                webhooks = self.webhook_manager.list_webhooks(enabled_only=enabled_only)
                return jsonify(self._success_response({
                    "webhooks": webhooks,
                    "count": len(webhooks)
                }))
            except Exception as e:
                logger.error(f"Error listing webhooks: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/webhooks", methods=["POST"])
        def api_create_webhook() -> Tuple[Dict[str, Any], int]:
            """Create a new webhook"""
            try:
                data = request.get_json()
                url = data.get("url")
                events = data.get("events", [])
                secret = data.get("secret")
                enabled = data.get("enabled", True)
                description = data.get("description")
                
                if not url:
                    return jsonify(self._error_response("URL required", status_code=400, error_type="validation"))
                
                if not events:
                    return jsonify(self._error_response("At least one event required", status_code=400, error_type="validation"))
                
                webhook_id = self.webhook_manager.add_webhook(
                    url=url,
                    events=events,
                    secret=secret,
                    enabled=enabled,
                    description=description
                )
                
                return jsonify(self._success_response({
                    "webhook_id": webhook_id,
                    "message": "Webhook created successfully"
                }))
            except Exception as e:
                logger.error(f"Error creating webhook: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/webhooks/<webhook_id>", methods=["GET"])
        def api_get_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
            """Get webhook by ID"""
            try:
                webhook = self.webhook_manager.get_webhook(webhook_id)
                if not webhook:
                    return jsonify(self._error_response("Webhook not found", status_code=404, error_type="not_found"))
                return jsonify(self._success_response(webhook))
            except Exception as e:
                logger.error(f"Error getting webhook: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/webhooks/<webhook_id>", methods=["PUT"])
        def api_update_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
            """Update webhook"""
            try:
                data = request.get_json()
                updated = self.webhook_manager.update_webhook(webhook_id, **data)
                
                if not updated:
                    return jsonify(self._error_response("Webhook not found", status_code=404, error_type="not_found"))
                
                return jsonify(self._success_response({"message": "Webhook updated successfully"}))
            except Exception as e:
                logger.error(f"Error updating webhook: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/webhooks/<webhook_id>", methods=["DELETE"])
        def api_delete_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
            """Delete webhook"""
            try:
                removed = self.webhook_manager.remove_webhook(webhook_id)
                
                if not removed:
                    return jsonify(self._error_response("Webhook not found", status_code=404, error_type="not_found"))
                
                return jsonify(self._success_response({"message": "Webhook deleted successfully"}))
            except Exception as e:
                logger.error(f"Error deleting webhook: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/webhooks/<webhook_id>/test", methods=["POST"])
        def api_test_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
            """Test webhook"""
            try:
                result = self.webhook_manager.test_webhook(webhook_id)
                
                if not result.get("success"):
                    return jsonify(self._error_response(result.get("error", "Test failed"), status_code=400, error_type="test_failed"))
                
                return jsonify(self._success_response(result))
            except Exception as e:
                logger.error(f"Error testing webhook: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/webhooks/events", methods=["GET"])
        def api_list_webhook_events() -> Tuple[Dict[str, Any], int]:
            """List available webhook event types"""
            try:
                events = [event.value for event in WebhookEvent]
                return jsonify(self._success_response({
                    "events": events,
                    "descriptions": {
                        "chat.message": "Triggered when a chat message is sent",
                        "chat.complete": "Triggered when a chat response is completed",
                        "conversation.created": "Triggered when a conversation is created",
                        "conversation.updated": "Triggered when a conversation is updated",
                        "conversation.deleted": "Triggered when a conversation is deleted",
                        "model.selected": "Triggered when a model is selected",
                        "model.downloaded": "Triggered when a model is downloaded",
                        "error.occurred": "Triggered when an error occurs",
                        "budget.exceeded": "Triggered when budget is exceeded",
                        "system.startup": "Triggered on system startup",
                        "system.shutdown": "Triggered on system shutdown"
                    }
                }))
            except Exception as e:
                logger.error(f"Error listing webhook events: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        # Plugin Management Endpoints
        @self.app.route("/api/plugins", methods=["GET"])
        def api_list_plugins() -> Tuple[Dict[str, Any], int]:
            """List all plugins"""
            try:
                enabled_only = request.args.get("enabled_only", "false").lower() == "true"
                plugins = self.plugin_manager.list_plugins(enabled_only=enabled_only)
                return jsonify(self._success_response({
                    "plugins": plugins,
                    "count": len(plugins)
                }))
            except Exception as e:
                logger.error(f"Error listing plugins: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/plugins/<plugin_id>", methods=["GET"])
        def api_get_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
            """Get plugin information"""
            try:
                plugin_info = self.plugin_manager.get_plugin_info(plugin_id)
                if not plugin_info:
                    return jsonify(self._error_response("Plugin not found", status_code=404, error_type="not_found"))
                return jsonify(self._success_response(plugin_info))
            except Exception as e:
                logger.error(f"Error getting plugin: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/plugins", methods=["POST"])
        def api_install_plugin() -> Tuple[Dict[str, Any], int]:
            """Install a plugin"""
            try:
                # Check if it's a file upload
                if 'file' in request.files:
                    file = request.files['file']
                    if file.filename == '':
                        return jsonify(self._error_response("No file selected", status_code=400, error_type="validation"))
                    
                    # Save uploaded file temporarily
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                        file.save(tmp.name)
                        tmp_path = Path(tmp.name)
                    
                    try:
                        plugin_id = request.form.get('plugin_id')
                        result = self.plugin_manager.install_plugin(tmp_path, plugin_id)
                    finally:
                        # Clean up temp file
                        tmp_path.unlink()
                else:
                    # JSON data with path
                    data = request.get_json()
                    if not data:
                        return jsonify(self._error_response("No data provided", status_code=400, error_type="validation"))
                    
                    plugin_path = Path(data.get("path"))
                    plugin_id = data.get("plugin_id")
                    
                    if not plugin_path.exists():
                        return jsonify(self._error_response("Plugin path does not exist", status_code=400, error_type="validation"))
                    
                    result = self.plugin_manager.install_plugin(plugin_path, plugin_id)
                
                if result["success"]:
                    return jsonify(self._success_response({
                        "message": result["message"],
                        "plugin_id": result["plugin_id"]
                    }))
                else:
                    return jsonify(self._error_response(
                        f"Installation failed: {', '.join(result['errors'])}",
                        status_code=400,
                        error_type="installation_error"
                    ))
            except Exception as e:
                logger.error(f"Error installing plugin: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/plugins/<plugin_id>", methods=["DELETE"])
        def api_uninstall_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
            """Uninstall a plugin"""
            try:
                result = self.plugin_manager.uninstall_plugin(plugin_id)
                
                if result["success"]:
                    return jsonify(self._success_response({"message": result["message"]}))
                else:
                    return jsonify(self._error_response(
                        f"Uninstallation failed: {', '.join(result['errors'])}",
                        status_code=400,
                        error_type="uninstallation_error"
                    ))
            except Exception as e:
                logger.error(f"Error uninstalling plugin: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/plugins/<plugin_id>/enable", methods=["POST"])
        def api_enable_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
            """Enable a plugin"""
            try:
                success = self.plugin_manager.enable_plugin(plugin_id)
                if success:
                    return jsonify(self._success_response({"message": f"Plugin '{plugin_id}' enabled"}))
                else:
                    return jsonify(self._error_response("Plugin not found", status_code=404, error_type="not_found"))
            except Exception as e:
                logger.error(f"Error enabling plugin: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/plugins/<plugin_id>/disable", methods=["POST"])
        def api_disable_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
            """Disable a plugin"""
            try:
                success = self.plugin_manager.disable_plugin(plugin_id)
                if success:
                    return jsonify(self._success_response({"message": f"Plugin '{plugin_id}' disabled"}))
                else:
                    return jsonify(self._error_response("Plugin not found", status_code=404, error_type="not_found"))
            except Exception as e:
                logger.error(f"Error disabling plugin: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/plugins/<plugin_id>/load", methods=["POST"])
        def api_load_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
            """Load a plugin module"""
            try:
                module = self.plugin_manager.load_plugin(plugin_id)
                if module:
                    return jsonify(self._success_response({
                        "message": f"Plugin '{plugin_id}' loaded successfully",
                        "module": module.__name__ if hasattr(module, '__name__') else str(module)
                    }))
                else:
                    return jsonify(self._error_response("Failed to load plugin", status_code=400, error_type="load_error"))
            except Exception as e:
                logger.error(f"Error loading plugin: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/config/unrestricted-mode", methods=["GET"])
        def api_get_unrestricted_mode() -> Tuple[Dict[str, Any], int]:
            """Get unrestricted mode setting"""
            try:
                config = self.config_manager.get_config()
                unrestricted_mode = getattr(config, 'unrestricted_mode', True)
                disable_safety_filters = getattr(config, 'disable_safety_filters', True)
                
                return jsonify(self._success_response({
                    "unrestricted_mode": unrestricted_mode,
                    "disable_safety_filters": disable_safety_filters
                }))
            except Exception as e:
                logger.error(f"Error getting unrestricted mode: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/config/unrestricted-mode", methods=["POST"])
        def api_set_unrestricted_mode() -> Tuple[Dict[str, Any], int]:
            """Set unrestricted mode setting"""
            try:
                data = request.get_json()
                if data is None:
                    return jsonify(self._error_response("No data provided", status_code=400, error_type="validation"))
                
                unrestricted_mode = data.get("unrestricted_mode", True)
                disable_safety_filters = data.get("disable_safety_filters", unrestricted_mode)
                
                config = self.config_manager.get_config()
                config.unrestricted_mode = unrestricted_mode
                config.disable_safety_filters = disable_safety_filters
                
                self.config_manager.config = config
                self.config_manager.save_config()
                
                return jsonify(self._success_response({
                    "unrestricted_mode": unrestricted_mode,
                    "disable_safety_filters": disable_safety_filters
                }, message="Unrestricted mode updated successfully"))
            except Exception as e:
                logger.error(f"Error setting unrestricted mode: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/config/providers", methods=["GET"])
        def api_get_providers():
            """Get list of providers and their configuration status"""
            try:
                config = self.config_manager.get_config()
                providers = []
                
                provider_info = {
                    "openai": {
                        "display_name": "OpenAI (ChatGPT)",
                        "setup_url": "https://platform.openai.com/api-keys",
                        "env_var": "OPENAI_API_KEY"
                    },
                    "anthropic": {
                        "display_name": "Anthropic (Claude)",
                        "setup_url": "https://console.anthropic.com/",
                        "env_var": "ANTHROPIC_API_KEY"
                    },
                    "google": {
                        "display_name": "Google (Gemini)",
                        "setup_url": "https://makersuite.google.com/app/apikey",
                        "env_var": "GOOGLE_API_KEY"
                    },
                    "mistral-ai": {
                        "display_name": "Mistral AI",
                        "setup_url": "https://console.mistral.ai/",
                        "env_var": "MISTRAL_AI_API_KEY"
                    },
                    "cohere": {
                        "display_name": "Cohere",
                        "setup_url": "https://dashboard.cohere.com/api-keys",
                        "env_var": "COHERE_API_KEY"
                    },
                    "groq": {
                        "display_name": "Groq (Fast Inference)",
                        "setup_url": "https://console.groq.com/keys",
                        "env_var": "GROQ_API_KEY"
                    }
                }
                
                for name, info in provider_info.items():
                    backend_config = config.backends.get(name)
                    api_key = os.getenv(info["env_var"]) or (backend_config.settings.get("api_key", "") if backend_config else "")
                    
                    providers.append({
                        "name": name,
                        "display_name": info["display_name"],
                        "setup_url": info["setup_url"],
                        "enabled": backend_config.enabled if backend_config else False,
                        "api_key": api_key if api_key else None,
                        "has_api_key": bool(api_key)
                    })
                
                return jsonify({
                    "status": "ok",
                    "providers": providers
                })
            except Exception as e:
                logger.error(f"Error getting providers: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/config/providers", methods=["POST"])
        def api_save_provider():
            """Save provider configuration"""
            try:
                data = request.get_json()
                provider_name = data.get("provider")
                api_key = data.get("api_key", "").strip()
                enabled = data.get("enabled", False)
                
                if not provider_name:
                    return jsonify({"status": "error", "message": "Provider name required"}), 400
                
                config = self.config_manager.get_config()
                
                if provider_name not in config.backends:
                    from ..utils.config import BackendConfig
                    type_map = {
                        "openai": "openai",
                        "anthropic": "anthropic",
                        "google": "google",
                        "mistral-ai": "mistral-ai",
                        "cohere": "cohere",
                        "groq": "groq"
                    }
                    config.backends[provider_name] = BackendConfig(
                        type=type_map.get(provider_name, provider_name),
                        enabled=False,
                        settings={}
                    )
                
                backend_config = config.backends[provider_name]
                
                if api_key:
                    backend_config.settings["api_key"] = api_key
                
                backend_config.enabled = enabled
                
                self.config_manager.config = config
                self.config_manager.save_config()
                
                return jsonify({
                    "status": "ok",
                    "message": f"{provider_name} configuration saved"
                })
            except Exception as e:
                logger.error(f"Error saving provider: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/status", methods=["GET"])
        def api_status():
            """Get system status"""
            try:
                import platform
                import sys
                
                backends_status = {}
                for backend_name, backend in self.model_loader.backends.items():
                    backends_status[backend_name] = {
                        "available": backend.is_available(),
                        "models": backend.list_models()
                    }
                
                # Get modules status
                modules_status = self.module_loader.list_modules()
                
                # Get system information
                system_info = {
                    "platform": platform.system(),
                    "platform_version": platform.version(),
                    "python_version": sys.version.split()[0],
                    "architecture": platform.machine(),
                    "processor": platform.processor() if platform.system() != "Windows" else "N/A"
                }
                
                return jsonify({
                    "status": "ok",
                    "backends": backends_status,
                    "modules": modules_status,
                    "default_model": self.config_manager.get_config().default_model,
                    "system": system_info
                })
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/modules", methods=["GET"])
        def api_list_modules() -> Tuple[Dict[str, Any], int]:
            """List all available modules."""
            try:
                modules = self.module_loader.list_modules()
                return jsonify({
                    "status": "ok",
                    "modules": modules
                })
            except Exception as e:
                logger.error(f"Error listing modules: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/models", methods=["GET"])
        def api_models():
            """List all available models"""
            try:
                models = self.model_loader.list_available_models()
                return jsonify({
                    "status": "ok",
                    "models": models
                })
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/models/available", methods=["GET"])
        def api_available_models():
            """Get list of models available to download, organized by backend"""
            try:
                backend_name = request.args.get("backend", None)
                
                result = {
                    "status": "ok",
                    "backends": {}
                }
                
                # Get models for each configured backend
                for name, backend in self.model_loader.backends.items():
                    if backend_name and name != backend_name:
                        continue
                    
                    try:
                        available_models = self.model_registry.get_available_models(name, backend)
                        backend_info = backend.get_backend_info() if hasattr(backend, 'get_backend_info') else {}
                        
                        result["backends"][name] = {
                            "info": backend_info,
                            "models": available_models,
                            "installed": backend.list_models() if backend.is_available() else []
                        }
                    except Exception as e:
                        logger.error(f"Error getting models for backend {name}: {e}")
                        result["backends"][name] = {
                            "info": {},
                            "models": [],
                            "installed": [],
                            "error": str(e)
                        }
                
                # Also show backends that are available but not currently enabled
                config = self.config_manager.get_config()
                for name, backend_config in config.backends.items():
                    if backend_name and name != backend_name:
                        continue
                    if name in result["backends"]:
                        continue  # Already added
                    
                    # Get models for this backend even if not enabled
                    try:
                        available_models = self.model_registry.get_available_models(name, None)
                        result["backends"][name] = {
                            "info": {
                                "name": name,
                                "type": backend_config.type,
                                "enabled": backend_config.enabled,
                                "available": False
                            },
                            "models": available_models,
                            "installed": []
                        }
                    except Exception:
                        pass
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error getting available models: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/download", methods=["POST"])
        def api_download_model():
            """Download a model via the specified backend"""
            try:
                data = request.get_json()
                model_name = data.get("model")
                backend_name = data.get("backend", "ollama")  # Default to ollama for backward compatibility
                
                if not model_name:
                    return jsonify({"status": "error", "message": "Model name required"}), 400
                
                # Get the specified backend
                backend = self.model_loader.backends.get(backend_name)
                
                # For API-based backends, provide better error messages
                if backend_name in ["openai", "anthropic", "google", "mistral-ai", "cohere", "groq"]:
                    if not backend:
                        # Backend not initialized - check config
                        config = self.config_manager.get_config()
                        backend_config = config.backends.get(backend_name)
                        
                        if not backend_config:
                            return jsonify({
                                "status": "error",
                                "message": f"{backend_name} backend is not configured. Please add it to your config file.",
                                "requires_config": True
                            }), 400
                        
                        if not backend_config.enabled:
                            return jsonify({
                                "status": "error",
                                "message": f"{backend_name} backend is disabled. Please enable it in your config file.",
                                "requires_enable": True
                            }), 400
                        
                        # Backend is enabled but not available - likely missing API key
                        api_key_env = f"{backend_name.upper().replace('-', '_')}_API_KEY"
                        return jsonify({
                            "status": "error",
                            "message": f"{backend_name} API key not configured. Please set the {api_key_env} environment variable or configure it in settings.",
                            "requires_api_key": True,
                            "env_var": api_key_env,
                            "setup_url": self._get_api_setup_url(backend_name)
                        }), 400
                    
                    if not backend.is_available():
                        api_key_env = f"{backend_name.upper().replace('-', '_')}_API_KEY"
                        return jsonify({
                            "status": "error",
                            "message": f"{backend_name} API key is invalid or not configured. Please check your {api_key_env} environment variable.",
                            "requires_api_key": True,
                            "env_var": api_key_env,
                            "setup_url": self._get_api_setup_url(backend_name)
                        }), 400
                
                # For other backends (like Ollama)
                if not backend:
                    return jsonify({
                        "status": "error",
                        "message": f"{backend_name} backend is not configured or not available. Please check your configuration."
                    }), 503
                
                if not backend.is_available():
                    return jsonify({
                        "status": "error",
                        "message": f"{backend_name} backend is not available. Please ensure the service is running and configured correctly."
                    }), 503
                
                # Check if backend supports downloads/setup
                if not hasattr(backend, 'download_model'):
                    return jsonify({
                        "status": "error",
                        "message": f"{backend_name} backend does not support model setup"
                    }), 400
                
                # Check if model is already installed
                installed_models = backend.list_models()
                if model_name in installed_models:
                    return jsonify({
                        "status": "info",
                        "message": f"Model {model_name} is already installed"
                    }), 200
                
                # Start download in background thread
                download_id = f"download_{backend_name}_{model_name}_{threading.get_ident()}_{int(time.time())}"
                self.download_progress[download_id] = {
                    "backend": backend_name,
                    "model": model_name,
                    "status": "downloading",
                    "progress": 0,
                    "message": f"Starting download of {model_name} via {backend_name}..."
                }
                
                def download_thread():
                    try:
                        # Use backend's download method if available
                        if backend_name == "ollama":
                            # Special handling for Ollama
                            import os
                            import subprocess
                            import sys
                            import re
                            
                            # Set up environment for UTF-8
                            env = os.environ.copy()
                            env['PYTHONIOENCODING'] = 'utf-8'
                            
                            # Windows-specific: set console code page to UTF-8
                            if sys.platform == 'win32':
                                try:
                                    import ctypes
                                    kernel32 = ctypes.windll.kernel32
                                    kernel32.SetConsoleOutputCP(65001)  # UTF-8
                                except Exception:
                                    pass
                            
                            # Run ollama pull command
                            process = subprocess.Popen(
                                ["ollama", "pull", model_name],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                bufsize=1,
                                env=env,
                                universal_newlines=False
                            )
                            
                            # Read output line by line
                            buffer = b''
                            for byte in iter(lambda: process.stdout.read(1), b''):
                                if byte:
                                    buffer += byte
                                    # Process line when we hit newline
                                    if b'\n' in buffer or b'\r' in buffer:
                                        try:
                                            # Decode with error handling
                                            line = buffer.decode('utf-8', errors='replace').strip()
                                            buffer = b''
                                            
                                            if not line:
                                                continue
                                            
                                            line_lower = line.lower()
                                            
                                            # Update message (limit length to avoid issues)
                                            self.download_progress[download_id]["message"] = line[:200]
                                            
                                            # Extract progress percentage
                                            if "%" in line:
                                                try:
                                                    percent_match = re.search(r'(\d+)%', line)
                                                    if percent_match:
                                                        percent = int(percent_match.group(1))
                                                        self.download_progress[download_id]["progress"] = min(percent, 99)
                                                except Exception:
                                                    pass
                                            
                                            # Check for completion indicators
                                            if any(word in line_lower for word in ["success", "complete", "pulled", "verifying"]):
                                                if "pulling" not in line_lower and "downloading" not in line_lower:
                                                    self.download_progress[download_id]["progress"] = 99
                                        except Exception as e:
                                            logger.warning(f"Error processing download line: {e}")
                                            buffer = b''
                                            continue
                            
                            # Process any remaining buffer
                            if buffer:
                                try:
                                    line = buffer.decode('utf-8', errors='replace').strip()
                                    if line:
                                        self.download_progress[download_id]["message"] = line[:200]
                                except Exception:
                                    pass
                            
                            process.wait()
                        
                        if process.returncode == 0:
                            self.download_progress[download_id]["status"] = "completed"
                            self.download_progress[download_id]["progress"] = 100
                            self.download_progress[download_id]["message"] = f"Successfully downloaded {model_name}"
                            
                            # Register model in registry
                            try:
                                model_info = next(
                                    (m for m in self.model_registry.get_available_models(backend_name, backend) 
                                     if m["name"] == model_name),
                                    None
                                )
                                if model_info:
                                    self.model_registry.register_model(backend_name, model_name, {
                                        "size": model_info.get("size", "Unknown"),
                                        "description": model_info.get("description", ""),
                                        "tags": model_info.get("tags", [])
                                    })
                            except Exception as e:
                                logger.warning(f"Failed to register model: {e}")
                        else:
                            # Use backend's download_model method for API backends
                            download_result = backend.download_model(model_name)
                            if download_result.get("status") == "error":
                                self.download_progress[download_id]["status"] = "error"
                                self.download_progress[download_id]["message"] = download_result.get("error", "Setup failed")
                            else:
                                # API backends are immediately available
                                self.download_progress[download_id]["status"] = "completed"
                                self.download_progress[download_id]["progress"] = 100
                                self.download_progress[download_id]["message"] = download_result.get("message", f"{model_name} is ready to use")
                    except Exception as e:
                        logger.error(f"Download thread error: {e}", exc_info=True)
                        self.download_progress[download_id]["status"] = "error"
                        self.download_progress[download_id]["message"] = f"Download error: {str(e)}"
                
                thread = threading.Thread(target=download_thread, daemon=True)
                thread.start()
                
                return jsonify({
                    "status": "ok",
                    "download_id": download_id,
                    "message": f"Download started for {model_name}"
                })
            except Exception as e:
                logger.error(f"Error downloading model: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/models/download/<download_id>", methods=["GET"])
        def api_download_status(download_id: str) -> Tuple[Dict[str, Any], int]:
            """Get download progress for a model download."""
            progress = self.download_progress.get(download_id)
            if not progress:
                return jsonify(self._error_response("Download not found", status_code=404, error_type="not_found"))
            
            return jsonify({
                "status": "ok",
                "progress": progress
            })
        
        @self.app.route("/api/models/delete", methods=["POST"])
        def api_delete_model() -> Tuple[Dict[str, Any], int]:
            """Delete a model from the specified backend."""
            try:
                data = request.get_json()
                model_name = data.get("model")
                backend_name = data.get("backend", "ollama")
                
                if not model_name:
                    return jsonify(self._error_response("Model name required", status_code=400, error_type="validation"))
                
                # Get the specified backend
                backend = self.model_loader.backends.get(backend_name)
                if not backend:
                    return jsonify(self._error_response(
                        f"Backend '{backend_name}' not available",
                        status_code=404,
                        error_type="not_found"
                    ))
                
                # Check if backend supports deletion
                if not hasattr(backend, 'delete_model'):
                    return jsonify(self._error_response(
                        f"Backend '{backend_name}' does not support model deletion",
                        status_code=400,
                        error_type="validation"
                    ))
                
                # Delete the model
                result = backend.delete_model(model_name)
                
                if result.get("status") == "ok":
                    # Remove from registry if it exists
                    try:
                        self.model_registry.registry.get("backends", {}).get(backend_name, {}).get("models", {}).pop(model_name, None)
                        self.model_registry._save_registry()
                    except Exception:
                        pass  # Registry update is optional
                    
                    return jsonify(self._success_response({
                        "message": result.get("message", f"Model '{model_name}' deleted successfully"),
                        "model": model_name
                    }))
                else:
                    return jsonify(self._error_response(
                        result.get("error", "Failed to delete model"),
                        status_code=500,
                        error_type="server_error"
                    ))
            except Exception as e:
                logger.error(f"Error deleting model: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/check-update", methods=["POST"])
        def api_check_model_update() -> Tuple[Dict[str, Any], int]:
            """Check for updates for a specific model."""
            try:
                data = request.get_json()
                model_name = data.get("model")
                backend_name = data.get("backend", "ollama")
                
                if not model_name:
                    return jsonify(self._error_response("Model name required", status_code=400, error_type="validation"))
                
                # Get the specified backend
                backend = self.model_loader.backends.get(backend_name)
                
                # Check for updates
                update_info = self.model_registry.check_model_updates(
                    backend_name=backend_name,
                    model_name=model_name,
                    backend_instance=backend
                )
                
                return jsonify(self._success_response(update_info))
            except Exception as e:
                logger.error(f"Error checking model update: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/check-all-updates", methods=["POST"])
        def api_check_all_updates() -> Tuple[Dict[str, Any], int]:
            """Check for updates for all installed models in a backend."""
            try:
                data = request.get_json()
                backend_name = data.get("backend", "ollama")
                
                # Get the specified backend
                backend = self.model_loader.backends.get(backend_name)
                if not backend:
                    return jsonify(self._error_response(
                        f"Backend '{backend_name}' not available",
                        status_code=404,
                        error_type="not_found"
                    ))
                
                # Get installed models
                installed_models = backend.list_models()
                
                # Check updates for all models
                updates = self.model_registry.check_all_updates(
                    backend_name=backend_name,
                    installed_models=installed_models,
                    backend_instance=backend
                )
                
                return jsonify(self._success_response({
                    "backend": backend_name,
                    "updates": updates,
                    "total_models": len(installed_models),
                    "models_with_updates": sum(1 for u in updates.values() if u.get("has_update", False))
                }))
            except Exception as e:
                logger.error(f"Error checking all updates: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/conversations", methods=["GET"])
        def api_list_conversations():
            """List all conversations"""
            try:
                search = request.args.get("search", None)
                limit = request.args.get("limit", type=int)
                conversations = self.conversation_manager.list_conversations(limit=limit, search=search)
                return jsonify({
                    "status": "ok",
                    "conversations": conversations
                })
            except Exception as e:
                logger.error(f"Error listing conversations: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/conversations", methods=["POST"])
        def api_create_conversation():
            """Create a new conversation"""
            try:
                data = request.get_json() or {}
                title = data.get("title")
                model = data.get("model")
                conv_id = self.conversation_manager.create_conversation(title=title, model=model)
                return jsonify({
                    "status": "ok",
                    "conversation_id": conv_id
                })
            except Exception as e:
                logger.error(f"Error creating conversation: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/conversations/<conv_id>", methods=["GET"])
        def api_get_conversation(conv_id):
            """Get a conversation by ID"""
            try:
                conversation = self.conversation_manager.get_conversation(conv_id)
                if not conversation:
                    return jsonify(self._error_response("Conversation not found", status_code=404, error_type="not_found"))
                return jsonify({
                    "status": "ok",
                    "conversation": conversation
                })
            except Exception as e:
                logger.error(f"Error getting conversation: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/conversations/<conv_id>", methods=["PUT"])
        def api_update_conversation(conv_id):
            """Update conversation metadata"""
            try:
                data = request.get_json() or {}
                title = data.get("title")
                model = data.get("model")
                success = self.conversation_manager.update_conversation(conv_id, title=title, model=model)
                if not success:
                    return jsonify(self._error_response("Conversation not found", status_code=404, error_type="not_found"))
                return jsonify(self._success_response())
            except Exception as e:
                logger.error(f"Error updating conversation: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/conversations/<conv_id>", methods=["DELETE"])
        def api_delete_conversation(conv_id):
            """Delete a conversation"""
            try:
                success = self.conversation_manager.delete_conversation(conv_id)
                if not success:
                    return jsonify(self._error_response("Conversation not found", status_code=404, error_type="not_found"))
                
                # Trigger webhook
                self.webhook_manager.trigger_webhook(
                    WebhookEvent.CONVERSATION_DELETED,
                    {"conversation_id": conv_id}
                )
                
                return jsonify(self._success_response())
            except Exception as e:
                logger.error(f"Error deleting conversation: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/conversations/<conv_id>/export", methods=["GET"])
        def api_export_conversation(conv_id):
            """Export a conversation"""
            try:
                format_type = request.args.get("format", "json")
                exported = self.conversation_manager.export_conversation(conv_id, format=format_type)
                if not exported:
                    return jsonify(self._error_response("Conversation not found", status_code=404, error_type="not_found"))
                return Response(
                    exported,
                    mimetype="application/json" if format_type == "json" else "text/plain",
                    headers={
                        "Content-Disposition": f"attachment; filename=conversation_{conv_id}.{format_type}"
                    }
                )
            except Exception as e:
                logger.error(f"Error exporting conversation: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/conversations/import", methods=["POST"])
        def api_import_conversation() -> Tuple[Dict[str, Any], int]:
            """Import a conversation from a file or string"""
            try:
                # Check if it's a file upload or JSON data
                if 'file' in request.files:
                    # File upload
                    file = request.files['file']
                    if file.filename == '':
                        return jsonify(self._error_response("No file selected", status_code=400, error_type="validation"))
                    
                    # Read file content
                    content = file.read().decode('utf-8')
                    format_hint = request.form.get('format', 'auto')  # Optional format hint
                    
                    # Import using conversation importer
                    imported_data = self.conversation_importer.import_from_string(
                        content, 
                        format_hint
                    )
                else:
                    # JSON data in request body
                    data = request.get_json()
                    if not data:
                        return jsonify(self._error_response("No data provided", status_code=400, error_type="validation"))
                    
                    content = data.get('content')
                    format_hint = data.get('format', 'json')
                    
                    if not content:
                        return jsonify(self._error_response("No content provided", status_code=400, error_type="validation"))
                    
                    # Import using conversation importer
                    imported_data = self.conversation_importer.import_from_string(
                        content,
                        format_hint
                    )
                
                # Convert to LocalMind format
                localmind_data = self.conversation_importer.convert_to_localmind_format(imported_data)
                if 'format_hint' in locals():
                    localmind_data['metadata']['source_format'] = format_hint
                else:
                    localmind_data['metadata']['source_format'] = 'auto'
                
                # Save as conversation
                conv_id = self.conversation_manager.save_conversation(
                    title=localmind_data.get('title', 'Imported Conversation'),
                    messages=localmind_data.get('messages', []),
                    model=localmind_data.get('model', 'Unknown')
                )
                
                return jsonify(self._success_response({
                    "conversation_id": conv_id,
                    "message": "Conversation imported successfully",
                    "imported_data": {
                        "model": localmind_data.get('model'),
                        "message_count": len(localmind_data.get('messages', [])),
                        "format": localmind_data.get('metadata', {}).get('source_format', 'unknown')
                    }
                }))
            except ValueError as e:
                return jsonify(self._error_response(str(e), status_code=400, error_type="validation"))
            except Exception as e:
                logger.error(f"Error importing conversation: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        def _get_backend_for_model(model: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
            """
            Determine backend name and type for a model
            
            Returns:
                Tuple of (backend_name, backend_type) or (None, None) if not found
            """
            if not model:
                return None, None
            
            # Check each backend for the model
            for backend_name, backend in self.model_loader.backends.items():
                try:
                    if model in backend.list_models():
                        backend_type = backend.get_backend_info().get("type", backend_name)
                        return backend_name, backend_type
                except Exception:
                    continue
            
            # Try to infer from model name patterns
            model_lower = model.lower()
            if any(prefix in model_lower for prefix in ["gpt", "openai"]):
                return "openai", "openai"
            elif any(prefix in model_lower for prefix in ["claude", "anthropic"]):
                return "anthropic", "anthropic"
            elif any(prefix in model_lower for prefix in ["gemini", "google"]):
                return "google", "google"
            elif any(prefix in model_lower for prefix in ["mistral"]):
                return "mistral-ai", "mistral-ai"
            elif any(prefix in model_lower for prefix in ["command", "cohere"]):
                return "cohere", "cohere"
            elif any(prefix in model_lower for prefix in ["groq", "llama-3", "mixtral"]):
                # Check if it's groq format
                if "-" in model and any(x in model for x in ["70b", "8b"]):
                    return "groq", "groq"
            
            # Default to ollama for local models
            return "ollama", "ollama"
        
        @self.app.route("/api/chat", methods=["POST"])
        def api_chat():
            """Chat with a model"""
            import time
            start_time = time.time()
            
            try:
                data = request.get_json()
                prompt = data.get("prompt")
                model = data.get("model")
                system_prompt = data.get("system_prompt")
                temperature = data.get("temperature", 0.7)
                stream = data.get("stream", False)
                conv_id = data.get("conversation_id")
                
                # Get unrestricted mode setting from config or request
                config = self.config_manager.get_config()
                # Allow override from request
                request_unrestricted = data.get("unrestricted_mode")
                if request_unrestricted is not None:
                    unrestricted_mode = request_unrestricted
                    disable_safety_filters = request_unrestricted
                else:
                    unrestricted_mode = getattr(config, 'unrestricted_mode', True)
                    disable_safety_filters = getattr(config, 'disable_safety_filters', True)
                
                if not prompt:
                    return jsonify({"status": "error", "message": "Prompt required"}), 400
                
                # Create conversation if not provided
                if not conv_id:
                    conv_id = self.conversation_manager.create_conversation(model=model)
                
                # Load conversation history for context
                conversation = self.conversation_manager.get_conversation(conv_id)
                conversation_messages = []
                if conversation:
                    conversation_messages = conversation.get("messages", [])
                
                # Convert to Message objects
                from ..core.context_manager import Message
                history_messages = self.context_manager.get_conversation_history(conversation_messages)
                
                # Add current user message
                current_user_message = Message(role="user", content=prompt)
                history_messages.append(current_user_message)
                
                # Try to find a module to handle this prompt (before building context)
                module_response = None
                preferred_module = data.get("module")  # Allow specifying module
                
                try:
                    module_response = self.module_loader.process_prompt(
                        prompt,
                        model_loader=self.model_loader,
                        context={
                            "model": model,
                            "messages": conversation_messages,
                            "conversation_id": conv_id
                        },
                        preferred_module=preferred_module,
                        model=model,
                        temperature=temperature
                    )
                except Exception as e:
                    logger.warning(f"Module processing failed: {e}")
                    module_response = None
                
                # If module handled it successfully, use module response
                if module_response and module_response.success and module_response.content:
                    # Save assistant message from module
                    self.conversation_manager.save_message(
                        conv_id,
                        "assistant",
                        module_response.content,
                        metadata={
                            "model": model,
                            "temperature": temperature,
                            "module": module_response.metadata.get("module")
                        }
                    )
                    
                    if stream:
                        # For streaming, we'll need to stream the module response
                        # For now, return as non-streaming
                        return jsonify({
                            "status": "ok",
                            "response": module_response.content,
                            "model": model,
                            "metadata": {
                                **module_response.metadata,
                                "module_used": True
                            },
                            "conversation_id": conv_id
                        })
                    else:
                        return jsonify({
                            "status": "ok",
                            "response": module_response.content,
                            "model": model,
                            "metadata": {
                                **module_response.metadata,
                                "module_used": True
                            },
                            "conversation_id": conv_id
                        })
                
                # Otherwise, use standard AI generation
                # Build context with compression/summarization
                processed_messages, context_metadata = self.context_manager.build_context(
                    history_messages,
                    model=model,
                    system_prompt=system_prompt
                )
                
                # Determine backend type
                backend_name, backend_type = _get_backend_for_model(model)
                if not backend_type:
                    backend_type = "ollama"  # Default
                
                # Format messages for backend
                if backend_type in ["openai", "anthropic", "google", "mistral-ai", "cohere", "groq"]:
                    # API backends use message format
                    formatted_messages = self.context_manager.format_messages_for_backend(
                        processed_messages, backend_type
                    )
                    # For API backends, we'll need to update the backend calls
                    # For now, build a prompt string
                    prompt_text = "\n".join([f"{m['role']}: {m['content']}" for m in formatted_messages if m.get('role') != 'system'])
                    if system_prompt:
                        # System prompt handled separately for API backends
                        pass
                else:
                    # Ollama uses prompt string
                    prompt_text = self.context_manager.format_messages_for_backend(
                        processed_messages, "ollama"
                    )
                
                # Save user message
                self.conversation_manager.save_message(
                    conv_id,
                    "user",
                    prompt,
                    metadata={"model": model, "temperature": temperature, "system_prompt": system_prompt}
                )
                
                # Trigger chat message webhook
                self.webhook_manager.trigger_webhook(
                    WebhookEvent.CHAT_MESSAGE,
                    {
                        "conversation_id": conv_id,
                        "role": "user",
                        "model": model,
                        "prompt": prompt
                    }
                )
                
                if stream:
                    # Streaming response using Ollama's streaming API directly
                    def generate():
                        import requests
                        
                        # Get Ollama backend
                        ollama_backend = self.model_loader.backends.get("ollama")
                        if not ollama_backend:
                            yield f"data: {json.dumps({'error': 'Ollama backend not available'})}\n\n"
                            return
                        
                        # Use Ollama's streaming API directly
                        url = f"{ollama_backend.base_url}/api/generate"
                        payload = {
                            "model": model or self.config_manager.get_config().default_model,
                            "prompt": prompt_text,  # Use context-aware prompt
                            "stream": True,
                            "options": {
                                "temperature": temperature,
                            }
                        }
                        
                        # Extract system prompt from processed messages if present
                        final_system_prompt = system_prompt
                        for msg in processed_messages:
                            if msg.role == "system" and "[Previous conversation summary:" in msg.content:
                                # Combine system prompts
                                if final_system_prompt:
                                    final_system_prompt = f"{final_system_prompt}\n\n{msg.content}"
                                else:
                                    final_system_prompt = msg.content
                        
                        if final_system_prompt:
                            payload["system"] = final_system_prompt
                        
                        full_response = ""
                        try:
                            with requests.post(url, json=payload, stream=True, timeout=ollama_backend.timeout) as r:
                                r.raise_for_status()
                                for line in r.iter_lines():
                                    if line:
                                        try:
                                            data = json.loads(line)
                                            if "response" in data:
                                                chunk = data['response']
                                                full_response += chunk
                                                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                                            if data.get("done", False):
                                                # Save assistant message
                                                self.conversation_manager.save_message(
                                                    conv_id,
                                                    "assistant",
                                                    full_response,
                                                    metadata={"model": model, "temperature": temperature}
                                                )
                                                
                                                # Trigger webhook
                                                self.webhook_manager.trigger_webhook(
                                                    WebhookEvent.CHAT_COMPLETE,
                                                    {
                                                        "conversation_id": conv_id,
                                                        "model": model,
                                                        "prompt": prompt,
                                                        "response_length": len(full_response)
                                                    }
                                                )
                                                
                                                yield f"data: {json.dumps({'done': True, 'conversation_id': conv_id})}\n\n"
                                                break
                                        except json.JSONDecodeError:
                                            continue
                        except Exception as e:
                            yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    
                    return Response(
                        stream_with_context(generate()),
                        mimetype="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no"
                        }
                    )
                else:
                    # Non-streaming response
                    # Extract system prompt from processed messages if present
                    final_system_prompt = system_prompt
                    for msg in processed_messages:
                        if msg.role == "system" and "[Previous conversation summary:" in msg.content:
                            # Combine system prompts
                            if final_system_prompt:
                                final_system_prompt = f"{final_system_prompt}\n\n{msg.content}"
                            else:
                                final_system_prompt = msg.content
                    
                    response = self.model_loader.generate(
                        prompt=prompt_text,  # Use context-aware prompt
                        model=model,
                        system_prompt=final_system_prompt,
                        temperature=temperature,
                        disable_safety_filters=disable_safety_filters
                    )
                    
                    # Save assistant message
                    self.conversation_manager.save_message(
                        conv_id,
                        "assistant",
                        response.text,
                        metadata={"model": response.model, "temperature": temperature}
                    )
                    
                    # Trigger webhooks
                    self.webhook_manager.trigger_webhook(
                        WebhookEvent.CHAT_COMPLETE,
                        {
                            "conversation_id": conv_id,
                            "model": model,
                            "prompt": prompt,
                            "response_length": len(response.text)
                        }
                    )
                    
                    # Track usage
                    response_time = time.time() - start_time
                    metadata = response.metadata or {}
                    prompt_tokens = metadata.get("prompt_tokens", 0)
                    completion_tokens = metadata.get("completion_tokens", 0)
                    
                    # Record usage
                    self.usage_tracker.record_usage(
                        backend=backend_name or "unknown",
                        model=model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        response_time=response_time,
                        success=True
                    )
                    
                    # Calculate performance metrics
                    elapsed_time = time.time() - start_time
                    response_length = len(response.text)
                    tokens_per_second = response_length / elapsed_time if elapsed_time > 0 else 0
                    
                    # Add context metadata to response
                    response_metadata = response.metadata.copy()
                    response_metadata.update(context_metadata)
                    response_metadata.update({
                        "response_time": round(elapsed_time, 2),
                        "response_length": response_length,
                        "tokens_per_second": round(tokens_per_second, 2)
                    })
                    
                    return jsonify({
                        "status": "ok",
                        "response": response.text,
                        "model": response.model,
                        "metadata": response_metadata,
                        "conversation_id": conv_id
                    })
            except Exception as e:
                logger.error(f"Error in chat: {e}", exc_info=True)
                
                # Track failed usage
                response_time = time.time() - start_time
                backend_name, _ = _get_backend_for_model(model)
                self.usage_tracker.record_usage(
                    backend=backend_name or "unknown",
                    model=model or "unknown",
                    prompt_tokens=0,
                    completion_tokens=0,
                    response_time=response_time,
                    success=False,
                    error=str(e)
                )
                
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/usage/statistics", methods=["GET"])
        def api_usage_statistics() -> Tuple[Dict[str, Any], int]:
            """Get usage statistics"""
            try:
                backend = request.args.get("backend")
                model = request.args.get("model")
                days = request.args.get("days", type=int)
                
                stats = self.usage_tracker.get_statistics(
                    backend=backend,
                    model=model,
                    days=days
                )
                
                return jsonify(self._success_response(stats))
            except Exception as e:
                logger.error(f"Error getting usage statistics: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/usage/budget", methods=["GET"])
        def api_get_budget() -> Tuple[Dict[str, Any], int]:
            """Get budget status"""
            try:
                status = self.usage_tracker.get_budget_status()
                return jsonify(self._success_response(status))
            except Exception as e:
                logger.error(f"Error getting budget status: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/usage/budget", methods=["POST"])
        def api_set_budget() -> Tuple[Dict[str, Any], int]:
            """Set budget settings"""
            try:
                data = request.get_json() or {}
                
                self.usage_tracker.set_budget(
                    daily_budget=data.get("daily_budget"),
                    monthly_budget=data.get("monthly_budget"),
                    alert_threshold=data.get("alert_threshold"),
                    alerts_enabled=data.get("alerts_enabled")
                )
                
                return jsonify(self._success_response({
                    "message": "Budget settings updated",
                    "budget": self.usage_tracker.get_budget_status()
                }))
            except Exception as e:
                logger.error(f"Error setting budget: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/resources", methods=["GET"])
        def api_resources() -> Tuple[Dict[str, Any], int]:
            """Get system resource usage"""
            try:
                resource_type = request.args.get("type", "all")
                
                if resource_type == "cpu":
                    data = self.resource_monitor.get_cpu_usage()
                elif resource_type == "memory":
                    data = self.resource_monitor.get_memory_usage()
                elif resource_type == "gpu":
                    data = self.resource_monitor.get_gpu_usage()
                elif resource_type == "disk":
                    data = self.resource_monitor.get_disk_usage()
                elif resource_type == "summary":
                    data = self.resource_monitor.get_resource_summary()
                else:
                    data = self.resource_monitor.get_system_info()
                
                return jsonify(self._success_response(data))
            except Exception as e:
                logger.error(f"Error getting resource usage: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/status", methods=["GET"])
        def api_models_status() -> Tuple[Dict[str, Any], int]:
            """Get status for all loaded models"""
            try:
                model_name = request.args.get("model")
                
                if model_name:
                    status = self.model_loader.get_model_status(model_name)
                    return jsonify(self._success_response(status))
                else:
                    all_status = self.model_loader.get_all_models_status()
                    return jsonify(self._success_response({
                        "models": all_status,
                        "count": len(all_status)
                    }))
            except Exception as e:
                logger.error(f"Error getting model status: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/unload", methods=["POST"])
        def api_unload_model() -> Tuple[Dict[str, Any], int]:
            """Unload a model from memory"""
            try:
                data = request.get_json() or {}
                model_name = data.get("model")
                backend_name = data.get("backend")
                
                if not model_name:
                    return jsonify(self._error_response("Model name required", status_code=400, error_type="validation"))
                
                success = self.model_loader.unload_model(model_name, backend_name)
                
                if success:
                    return jsonify(self._success_response({
                        "message": f"Model '{model_name}' unloaded successfully",
                        "model": model_name
                    }))
                else:
                    return jsonify(self._error_response(
                        f"Failed to unload model '{model_name}'",
                        status_code=500,
                        error_type="server_error"
                    ))
            except Exception as e:
                logger.error(f"Error unloading model: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/unload-all", methods=["POST"])
        def api_unload_all_models() -> Tuple[Dict[str, Any], int]:
            """Unload all loaded models"""
            try:
                results = self.model_loader.model_manager.force_unload_all()
                
                success_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                return jsonify(self._success_response({
                    "message": f"Unloaded {success_count}/{total_count} models",
                    "results": results,
                    "success_count": success_count,
                    "total_count": total_count
                }))
            except Exception as e:
                logger.error(f"Error unloading all models: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/cleanup/stats", methods=["GET"])
        def api_cleanup_stats() -> Tuple[Dict[str, Any], int]:
            """Get cleanup statistics"""
            try:
                stats = self.resource_cleanup.get_cleanup_stats()
                return jsonify(self._success_response(stats))
            except Exception as e:
                logger.error(f"Error getting cleanup stats: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/cleanup/run", methods=["POST"])
        def api_run_cleanup() -> Tuple[Dict[str, Any], int]:
            """Run resource cleanup"""
            try:
                data = request.get_json() or {}
                
                cleanup_type = data.get("type", "all")
                
                if cleanup_type == "cache":
                    results = self.resource_cleanup.cleanup_cache(
                        max_age_days=data.get("max_age_days", 7),
                        max_size_mb=data.get("max_size_mb")
                    )
                elif cleanup_type == "conversations":
                    results = self.resource_cleanup.cleanup_conversations(
                        max_age_days=data.get("max_age_days"),
                        keep_recent=data.get("keep_recent", 50),
                        max_size_mb=data.get("max_size_mb")
                    )
                elif cleanup_type == "temp":
                    results = self.resource_cleanup.cleanup_temp_files(
                        max_age_hours=data.get("max_age_hours", 24)
                    )
                elif cleanup_type == "logs":
                    results = self.resource_cleanup.cleanup_logs(
                        max_age_days=data.get("max_age_days", 30),
                        max_size_mb=data.get("max_size_mb")
                    )
                else:
                    # Run all cleanup
                    results = self.resource_cleanup.cleanup_all(
                        cache_max_age_days=data.get("cache_max_age_days", 7),
                        cache_max_size_mb=data.get("cache_max_size_mb"),
                        conversations_max_age_days=data.get("conversations_max_age_days"),
                        conversations_keep_recent=data.get("conversations_keep_recent", 50),
                        conversations_max_size_mb=data.get("conversations_max_size_mb"),
                        temp_max_age_hours=data.get("temp_max_age_hours", 24),
                        logs_max_age_days=data.get("logs_max_age_days", 30),
                        logs_max_size_mb=data.get("logs_max_size_mb")
                    )
                
                # Format bytes for display
                total_bytes = results.get("total_bytes_freed", results.get("bytes_freed", 0))
                total_mb = total_bytes / (1024 * 1024)
                
                return jsonify(self._success_response({
                    "message": f"Cleanup completed. Freed {total_mb:.2f} MB",
                    "results": results,
                    "total_bytes_freed": total_bytes,
                    "total_mb_freed": total_mb
                }))
            except Exception as e:
                logger.error(f"Error running cleanup: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/chat/compare", methods=["POST"])
        def api_compare_models() -> Tuple[Dict[str, Any], int]:
            """Compare responses from multiple models"""
            import time
            import concurrent.futures
            
            try:
                data = request.get_json()
                prompt = data.get("prompt")
                models = data.get("models", [])
                system_prompt = data.get("system_prompt")
                temperature = data.get("temperature", 0.7)
                disable_safety_filters = data.get("disable_safety_filters", True)
                
                if not prompt:
                    return jsonify(self._error_response("Prompt required", status_code=400, error_type="validation"))
                
                if not models or len(models) < 2:
                    return jsonify(self._error_response("At least 2 models required for comparison", status_code=400, error_type="validation"))
                
                if len(models) > 5:
                    return jsonify(self._error_response("Maximum 5 models can be compared at once", status_code=400, error_type="validation"))
                
                # Get unrestricted mode setting
                config = self.config_manager.get_config()
                if disable_safety_filters is None:
                    disable_safety_filters = getattr(config, 'disable_safety_filters', True)
                
                # Compare models in parallel
                results = []
                errors = []
                
                def generate_for_model(model_name):
                    """Generate response for a single model"""
                    try:
                        start_time = time.time()
                        
                        # Determine backend
                        backend_name, _ = _get_backend_for_model(model_name)
                        if not backend_name:
                            return {
                                "model": model_name,
                                "error": "Backend not found",
                                "success": False
                            }
                        
                        # Generate response
                        response = self.model_loader.generate(
                            prompt=prompt,
                            model=model_name,
                            system_prompt=system_prompt,
                            temperature=temperature,
                            disable_safety_filters=disable_safety_filters
                        )
                        
                        response_time = time.time() - start_time
                        
                        # Track usage
                        self.usage_tracker.record_usage(
                            backend=backend_name,
                            model=model_name,
                            prompt_tokens=response.metadata.get("prompt_tokens", 0),
                            completion_tokens=response.metadata.get("completion_tokens", 0),
                            response_time=response_time,
                            success=True
                        )
                        
                        return {
                            "model": model_name,
                            "backend": backend_name,
                            "response": response.text,
                            "response_time": round(response_time, 2),
                            "metadata": response.metadata,
                            "success": True
                        }
                    except Exception as e:
                        logger.error(f"Error comparing model {model_name}: {e}", exc_info=True)
                        return {
                            "model": model_name,
                            "error": str(e),
                            "success": False
                        }
                
                # Run comparisons in parallel (max 5 concurrent)
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(models), 5)) as executor:
                    future_to_model = {executor.submit(generate_for_model, model): model for model in models}
                    for future in concurrent.futures.as_completed(future_to_model):
                        result = future.result()
                        if result["success"]:
                            results.append(result)
                        else:
                            errors.append(result)
                
                # Sort by response time
                results.sort(key=lambda x: x.get("response_time", 0))
                
                return jsonify(self._success_response({
                    "prompt": prompt,
                    "results": results,
                    "errors": errors,
                    "total_models": len(models),
                    "successful": len(results),
                    "failed": len(errors)
                }))
            except Exception as e:
                logger.error(f"Error in model comparison: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/chat/ensemble", methods=["POST"])
        def api_ensemble_models() -> Tuple[Dict[str, Any], int]:
            """Generate ensemble response from multiple models"""
            import time
            import concurrent.futures
            
            try:
                data = request.get_json()
                prompt = data.get("prompt")
                models = data.get("models", [])
                system_prompt = data.get("system_prompt")
                temperature = data.get("temperature", 0.7)
                method = data.get("method", "majority_vote")
                disable_safety_filters = data.get("disable_safety_filters", True)
                
                if not prompt:
                    return jsonify(self._error_response("Prompt required", status_code=400, error_type="validation"))
                
                if not models or len(models) < 2:
                    return jsonify(self._error_response("At least 2 models required for ensemble", status_code=400, error_type="validation"))
                
                if len(models) > 5:
                    return jsonify(self._error_response("Maximum 5 models can be used in ensemble", status_code=400, error_type="validation"))
                
                # Get unrestricted mode setting
                config = self.config_manager.get_config()
                if disable_safety_filters is None:
                    disable_safety_filters = getattr(config, 'disable_safety_filters', True)
                
                # Generate responses from all models in parallel
                responses = []
                errors = []
                
                def generate_for_model(model_name):
                    """Generate response for a single model"""
                    try:
                        start_time = time.time()
                        
                        # Determine backend
                        backend_name, _ = _get_backend_for_model(model_name)
                        if not backend_name:
                            return {
                                "model": model_name,
                                "error": "Backend not found",
                                "success": False
                            }
                        
                        # Generate response
                        response = self.model_loader.generate(
                            prompt=prompt,
                            model=model_name,
                            system_prompt=system_prompt,
                            temperature=temperature,
                            disable_safety_filters=disable_safety_filters
                        )
                        
                        response_time = time.time() - start_time
                        
                        # Track usage
                        self.usage_tracker.record_usage(
                            backend=backend_name,
                            model=model_name,
                            prompt_tokens=response.metadata.get("prompt_tokens", 0),
                            completion_tokens=response.metadata.get("completion_tokens", 0),
                            response_time=response_time,
                            success=True
                        )
                        
                        return {
                            "model": model_name,
                            "backend": backend_name,
                            "response": response.text,
                            "response_time": round(response_time, 2),
                            "metadata": response.metadata,
                            "success": True
                        }
                    except Exception as e:
                        logger.error(f"Error in ensemble for model {model_name}: {e}", exc_info=True)
                        return {
                            "model": model_name,
                            "error": str(e),
                            "success": False
                        }
                
                # Run in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(models), 5)) as executor:
                    future_to_model = {executor.submit(generate_for_model, model): model for model in models}
                    for future in concurrent.futures.as_completed(future_to_model):
                        result = future.result()
                        if result["success"]:
                            responses.append(result)
                        else:
                            errors.append(result)
                
                # Need at least 2 successful responses for ensemble
                if len(responses) < 2:
                    return jsonify(self._error_response(
                        f"Need at least 2 successful responses for ensemble (got {len(responses)})",
                        status_code=400,
                        error_type="validation"
                    ))
                
                # Combine responses using ensemble method
                ensemble_result = self.ensemble_processor.combine_responses(responses, method=method)
                
                return jsonify(self._success_response({
                    "prompt": prompt,
                    "response": ensemble_result["response"],
                    "method": method,
                    "models_used": ensemble_result["models_used"],
                    "individual_responses": responses,
                    "errors": errors,
                    "metadata": ensemble_result.get("metadata", {})
                }))
            except Exception as e:
                logger.error(f"Error in ensemble: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/chat/route", methods=["POST"])
        def api_route_model() -> Tuple[Dict[str, Any], int]:
            """Route prompt to best model based on task type"""
            try:
                data = request.get_json()
                prompt = data.get("prompt")
                task_type = data.get("task_type")  # Optional explicit task type
                
                if not prompt:
                    return jsonify(self._error_response("Prompt required", status_code=400, error_type="validation"))
                
                # Get available models
                available_models = []
                try:
                    models_data = self.model_loader.list_available_models()
                    for backend_models in models_data.values():
                        available_models.extend(backend_models)
                except Exception as e:
                    logger.warning(f"Error getting available models: {e}")
                
                # Route to best model
                recommended_model, detected_task, confidence = self.model_router.route_to_model(
                    prompt=prompt,
                    available_models=available_models,
                    task_type=task_type
                )
                
                # Get recommendations for this task
                recommendations = self.model_router.get_task_recommendations(
                    detected_task,
                    available_models
                )
                
                return jsonify(self._success_response({
                    "prompt": prompt,
                    "recommended_model": recommended_model,
                    "detected_task": detected_task,
                    "confidence": round(confidence, 2),
                    "recommendations": recommendations[:5],  # Top 5
                    "available_models_count": len(available_models)
                }))
            except Exception as e:
                logger.error(f"Error in model routing: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/tasks/types", methods=["GET"])
        def api_get_task_types() -> Tuple[Dict[str, Any], int]:
            """Get list of supported task types"""
            try:
                task_types = self.model_router.get_all_task_types()
                return jsonify(self._success_response({
                    "task_types": task_types,
                    "count": len(task_types)
                }))
            except Exception as e:
                logger.error(f"Error getting task types: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/suggest", methods=["POST"])
        def api_suggest_model() -> Tuple[Dict[str, Any], int]:
            """Suggest best model based on context and preferences"""
            try:
                data = request.get_json() or {}
                conversation_history = data.get("conversation_history", [])
                current_model = data.get("current_model")
                preferences = data.get("preferences", {})
                
                # Get available models
                available_models = []
                try:
                    models_data = self.model_loader.list_available_models()
                    for backend_models in models_data.values():
                        available_models.extend(backend_models)
                except Exception as e:
                    logger.warning(f"Error getting available models: {e}")
                
                if not available_models:
                    return jsonify(self._error_response("No models available", status_code=400, error_type="validation"))
                
                # If no conversation history, suggest default
                if not conversation_history:
                    suggested = self.model_router.select_best_default_model(
                        available_models=available_models,
                        preferences=preferences
                    )
                    return jsonify(self._success_response({
                        "suggested_model": suggested,
                        "reason": "Default model selection",
                        "method": "default"
                    }))
                
                # Suggest based on context
                suggested, reason = self.model_router.suggest_model_for_context(
                    conversation_history=conversation_history,
                    available_models=available_models,
                    current_model=current_model
                )
                
                return jsonify(self._success_response({
                    "suggested_model": suggested,
                    "reason": reason,
                    "method": "context_aware",
                    "current_model": current_model
                }))
            except Exception as e:
                logger.error(f"Error suggesting model: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
        
        @self.app.route("/api/models/auto-select", methods=["GET"])
        def api_auto_select_model() -> Tuple[Dict[str, Any], int]:
            """Automatically select best default model"""
            try:
                # Get available models
                available_models = []
                try:
                    models_data = self.model_loader.list_available_models()
                    for backend_models in models_data.values():
                        available_models.extend(backend_models)
                except Exception as e:
                    logger.warning(f"Error getting available models: {e}")
                
                if not available_models:
                    return jsonify(self._error_response("No models available", status_code=400, error_type="validation"))
                
                # Select best default
                selected = self.model_router.select_best_default_model(available_models)
                
                return jsonify(self._success_response({
                    "selected_model": selected,
                    "available_models_count": len(available_models),
                    "method": "auto_select"
                }))
            except Exception as e:
                logger.error(f"Error in auto-select: {e}", exc_info=True)
                return jsonify(self._error_response(str(e), error_type="server_error"))
    
    def run(self, debug: bool = False) -> None:
        """
        Run the Flask web server.
        
        Args:
            debug: Enable Flask debug mode (default: False)
        """
        logger.info(f"Starting LocalMind web server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)

