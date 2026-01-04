"""
Plugin routes - Handle plugin management endpoints
"""

from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify
from pathlib import Path
import logging
import tempfile

from .base import error_response, success_response

logger = logging.getLogger(__name__)


def setup_plugin_routes(app: Flask, server_instance):
    """
    Setup plugin-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/plugins", methods=["GET"])
    def api_list_plugins() -> Tuple[Dict[str, Any], int]:
        """List all plugins"""
        try:
            enabled_only = request.args.get("enabled_only", "false").lower() == "true"
            plugins = server_instance.plugin_manager.list_plugins(enabled_only=enabled_only)
            return jsonify(success_response({
                "plugins": plugins,
                "count": len(plugins)
            }))
        except Exception as e:
            logger.error(f"Error listing plugins: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/plugins/<plugin_id>", methods=["GET"])
    def api_get_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
        """Get plugin information"""
        try:
            plugin_info = server_instance.plugin_manager.get_plugin_info(plugin_id)
            if not plugin_info:
                return jsonify(error_response("Plugin not found", status_code=404, error_type="not_found")), 404
            return jsonify(success_response(plugin_info))
        except Exception as e:
            logger.error(f"Error getting plugin: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/plugins", methods=["POST"])
    def api_install_plugin() -> Tuple[Dict[str, Any], int]:
        """Install a plugin"""
        try:
            if 'file' in request.files:
                file = request.files['file']
                if file.filename == '':
                    return jsonify(error_response("No file selected", status_code=400, error_type="validation")), 400
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                    file.save(tmp.name)
                    tmp_path = Path(tmp.name)
                
                try:
                    plugin_id = request.form.get('plugin_id')
                    result = server_instance.plugin_manager.install_plugin(tmp_path, plugin_id)
                finally:
                    tmp_path.unlink()
            else:
                data = request.get_json()
                if not data:
                    return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
                
                plugin_path = Path(data.get("path"))
                plugin_id = data.get("plugin_id")
                
                if not plugin_path.exists():
                    return jsonify(error_response("Plugin path does not exist", status_code=400, error_type="validation")), 400
                
                result = server_instance.plugin_manager.install_plugin(plugin_path, plugin_id)
            
            if result["success"]:
                return jsonify(success_response({
                    "message": result["message"],
                    "plugin_id": result["plugin_id"]
                }))
            else:
                return jsonify(error_response(
                    f"Installation failed: {', '.join(result['errors'])}",
                    status_code=400,
                    error_type="installation_error"
                )), 400
        except Exception as e:
            logger.error(f"Error installing plugin: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/plugins/<plugin_id>", methods=["DELETE"])
    def api_uninstall_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
        """Uninstall a plugin"""
        try:
            result = server_instance.plugin_manager.uninstall_plugin(plugin_id)
            
            if result["success"]:
                return jsonify(success_response({"message": result["message"]}))
            else:
                return jsonify(error_response(
                    f"Uninstallation failed: {', '.join(result['errors'])}",
                    status_code=400,
                    error_type="uninstallation_error"
                )), 400
        except Exception as e:
            logger.error(f"Error uninstalling plugin: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/plugins/<plugin_id>/enable", methods=["POST"])
    def api_enable_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
        """Enable a plugin"""
        try:
            success = server_instance.plugin_manager.enable_plugin(plugin_id)
            if success:
                return jsonify(success_response({"message": f"Plugin '{plugin_id}' enabled"}))
            else:
                return jsonify(error_response("Plugin not found", status_code=404, error_type="not_found")), 404
        except Exception as e:
            logger.error(f"Error enabling plugin: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/plugins/<plugin_id>/disable", methods=["POST"])
    def api_disable_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
        """Disable a plugin"""
        try:
            success = server_instance.plugin_manager.disable_plugin(plugin_id)
            if success:
                return jsonify(success_response({"message": f"Plugin '{plugin_id}' disabled"}))
            else:
                return jsonify(error_response("Plugin not found", status_code=404, error_type="not_found")), 404
        except Exception as e:
            logger.error(f"Error disabling plugin: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/plugins/<plugin_id>/load", methods=["POST"])
    def api_load_plugin(plugin_id: str) -> Tuple[Dict[str, Any], int]:
        """Load a plugin module"""
        try:
            module = server_instance.plugin_manager.load_plugin(plugin_id)
            if module:
                return jsonify(success_response({
                    "message": f"Plugin '{plugin_id}' loaded successfully",
                    "module": module.__name__ if hasattr(module, '__name__') else str(module)
                }))
            else:
                return jsonify(error_response("Failed to load plugin", status_code=400, error_type="load_error")), 400
        except Exception as e:
            logger.error(f"Error loading plugin: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500

