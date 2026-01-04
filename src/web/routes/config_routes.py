"""
Config routes - Handle configuration endpoints
"""

from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify, send_file
from pathlib import Path
import logging
import os

from .base import error_response, success_response, get_project_root

logger = logging.getLogger(__name__)


def setup_config_routes(app: Flask, server_instance):
    """
    Setup configuration-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/config/unrestricted-mode", methods=["GET"])
    def api_get_unrestricted_mode() -> Tuple[Dict[str, Any], int]:
        """Get unrestricted mode setting"""
        try:
            config = server_instance.config_manager.get_config()
            unrestricted_mode = getattr(config, 'unrestricted_mode', True)
            disable_safety_filters = getattr(config, 'disable_safety_filters', True)
            
            return jsonify(success_response({
                "unrestricted_mode": unrestricted_mode,
                "disable_safety_filters": disable_safety_filters
            }))
        except Exception as e:
            logger.error(f"Error getting unrestricted mode: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/config/unrestricted-mode", methods=["POST"])
    def api_set_unrestricted_mode() -> Tuple[Dict[str, Any], int]:
        """Set unrestricted mode setting"""
        try:
            data = request.get_json()
            if data is None:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            unrestricted_mode = data.get("unrestricted_mode", True)
            disable_safety_filters = data.get("disable_safety_filters", unrestricted_mode)
            
            config = server_instance.config_manager.get_config()
            config.unrestricted_mode = unrestricted_mode
            config.disable_safety_filters = disable_safety_filters
            
            server_instance.config_manager.config = config
            server_instance.config_manager.save_config()
            
            return jsonify(success_response({
                "unrestricted_mode": unrestricted_mode,
                "disable_safety_filters": disable_safety_filters
            }, message="Unrestricted mode updated successfully"))
        except Exception as e:
            logger.error(f"Error setting unrestricted mode: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/config/providers", methods=["GET"])
    def api_get_providers():
        """Get list of providers and their configuration status"""
        try:
            config = server_instance.config_manager.get_config()
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
                # Check encrypted storage first, then env, then config
                api_key = server_instance.key_manager.decrypt_key(name) or os.getenv(info["env_var"]) or (backend_config.settings.get("api_key", "") if backend_config else "")
                
                providers.append({
                    "name": name,
                    "display_name": info["display_name"],
                    "setup_url": info["setup_url"],
                    "enabled": backend_config.enabled if backend_config else False,
                    "api_key": api_key if api_key else None,
                    "has_api_key": bool(api_key),
                    "encrypted": server_instance.key_manager.has_key(name)
                })
            
            return jsonify(success_response({"providers": providers}))
        except Exception as e:
            logger.error(f"Error getting providers: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/config/providers", methods=["POST"])
    def api_save_provider():
        """Save provider configuration"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            provider_name = data.get("provider")
            api_key = data.get("api_key")
            enabled = data.get("enabled", False)
            
            if not provider_name:
                return jsonify(error_response("Provider name required", status_code=400, error_type="validation")), 400
            
            config = server_instance.config_manager.get_config()
            
            if provider_name not in config.backends:
                from ...utils.config import BackendConfig
                config.backends[provider_name] = BackendConfig(
                    type=provider_name,
                    enabled=False,
                    settings={}
                )
            
            backend_config = config.backends[provider_name]
            
            # Encrypt and store API key
            if api_key:
                server_instance.key_manager.encrypt_key(api_key, provider_name)
                # Also store in config for backward compatibility (optional)
                backend_config.settings["api_key"] = api_key
            
            backend_config.enabled = enabled
            
            server_instance.config_manager.config = config
            server_instance.config_manager.save_config()
            
            # Audit log
            from ...core.audit_logger import AuditEventType
            server_instance.audit_logger.log(
                AuditEventType.API_KEY_UPDATE,
                ip_address=request.remote_addr or "unknown",
                details={"provider": provider_name, "action": "configured"}
            )
            
            return jsonify(success_response({
                "message": f"{provider_name} configuration saved"
            }))
        except Exception as e:
            logger.error(f"Error saving provider: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/config/backup", methods=["POST"])
    def api_backup_config() -> Tuple[Dict[str, Any], int]:
        """Create a backup of configuration"""
        try:
            data = request.get_json() or {}
            include_conversations = data.get("include_conversations", False)
            include_models = data.get("include_models", False)
            format_type = data.get("format", "json")
            
            backup_data = server_instance.config_backup.create_backup(
                include_conversations=include_conversations,
                include_models=include_models
            )
            
            if format_type == "download":
                import tempfile
                suffix = ".zip" if (include_conversations or include_models) else ".json"
                
                with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as tmp:
                    tmp_path = Path(tmp.name)
                
                server_instance.config_backup.export_backup(tmp_path, backup_data)
                
                return send_file(
                    tmp_path,
                    as_attachment=True,
                    download_name=f"localmind_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
                )
            else:
                return jsonify(success_response(backup_data))
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/config/restore", methods=["POST"])
    def api_restore_config() -> Tuple[Dict[str, Any], int]:
        """Restore configuration from backup"""
        try:
            if 'file' not in request.files:
                return jsonify(error_response("No file provided", status_code=400, error_type="validation")), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify(error_response("No file selected", status_code=400, error_type="validation")), 400
            
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                file.save(tmp.name)
                tmp_path = Path(tmp.name)
            
            try:
                result = server_instance.config_backup.restore_backup(tmp_path)
                
                if result["success"]:
                    return jsonify(success_response({"message": "Configuration restored successfully"}))
                else:
                    return jsonify(error_response(
                        f"Restore failed: {', '.join(result.get('errors', []))}",
                        status_code=400
                    )), 400
            finally:
                tmp_path.unlink()
        except Exception as e:
            logger.error(f"Error restoring backup: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500

