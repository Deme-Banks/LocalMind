"""
Model routes - Handle model management endpoints
"""

from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify
from pathlib import Path
import logging
import time
import threading

from .base import error_response, success_response

logger = logging.getLogger(__name__)


def setup_model_routes(app: Flask, server_instance):
    """
    Setup model-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/models", methods=["GET"])
    def api_models():
        """List all available models"""
        try:
            models = server_instance.model_loader.list_available_models()
            
            # Filter models if local-only mode is enabled
            if server_instance.local_only_mode.enabled:
                models = server_instance.local_only_mode.filter_models(models)
            
            return jsonify(success_response({"models": models}))
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/models/available", methods=["GET"])
    def api_available_models():
        """Get list of models available to download"""
        try:
            backend = request.args.get("backend", "ollama")
            backend_instance = server_instance.model_loader.backends.get(backend)
            
            if not backend_instance:
                return jsonify(error_response(f"Backend '{backend}' not available", status_code=404)), 404
            
            available = backend_instance.list_available_models() if hasattr(backend_instance, 'list_available_models') else []
            
            return jsonify(success_response({
                "backend": backend,
                "models": available
            }))
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/models/download", methods=["POST"])
    def api_download_model():
        """Download a model"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            model_name = data.get("model")
            backend = data.get("backend", "ollama")
            
            if not model_name:
                return jsonify(error_response("Model name required", status_code=400, error_type="validation")), 400
            
            backend_instance = server_instance.model_loader.backends.get(backend)
            if not backend_instance:
                return jsonify(error_response(f"Backend '{backend}' not available", status_code=404)), 404
            
            # Start download in background
            download_id = f"{backend}_{model_name}_{int(time.time())}"
            server_instance.download_progress[download_id] = {
                "status": "starting",
                "progress": 0,
                "model": model_name,
                "backend": backend
            }
            
            def download_thread():
                try:
                    result = backend_instance.download_model(model_name)
                    server_instance.download_progress[download_id] = {
                        "status": "completed",
                        "progress": 100,
                        "model": model_name,
                        "backend": backend,
                        "result": result
                    }
                    
                    from ...core.webhook_manager import WebhookEvent
                    server_instance.webhook_manager.trigger_webhook(
                        WebhookEvent.MODEL_DOWNLOADED,
                        {"model": model_name, "backend": backend, "download_id": download_id}
                    )
                except Exception as e:
                    server_instance.download_progress[download_id] = {
                        "status": "error",
                        "error": str(e),
                        "model": model_name,
                        "backend": backend
                    }
            
            import threading
            thread = threading.Thread(target=download_thread)
            thread.daemon = True
            thread.start()
            
            return jsonify(success_response({
                "download_id": download_id,
                "message": "Download started"
            }))
        except Exception as e:
            logger.error(f"Error starting download: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/models/download/<download_id>", methods=["GET"])
    def api_get_download_progress(download_id):
        """Get download progress"""
        try:
            progress = server_instance.download_progress.get(download_id, {"status": "not_found"})
            return jsonify(success_response(progress))
        except Exception as e:
            logger.error(f"Error getting download progress: {e}")
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/models/status", methods=["GET"])
    def api_models_status():
        """Get status of all models"""
        try:
            status = {}
            for backend_name, backend in server_instance.model_loader.backends.items():
                try:
                    models = backend.list_models()
                    status[backend_name] = {
                        "available": len(models),
                        "models": models[:10]  # Limit to first 10
                    }
                except Exception as e:
                    status[backend_name] = {"error": str(e)}
            
            return jsonify(success_response({"backends": status}))
        except Exception as e:
            logger.error(f"Error getting models status: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/models/auto-select", methods=["GET"])
    def api_auto_select_model():
        """Auto-select best model"""
        try:
            from ...core.model_router import ModelRouter
            router = ModelRouter()
            
            # Get available models
            available_models = server_instance.model_loader.list_available_models()
            flat_models = []
            for backend, models in available_models.items():
                flat_models.extend([f"{backend}:{m}" for m in models])
            
            if not flat_models:
                return jsonify(error_response("No models available", status_code=404)), 404
            
            # Select best model (simple heuristic - prefer local, then by name)
            selected = router.select_best_model(available_models)
            
            return jsonify(success_response({"selected_model": selected}))
        except Exception as e:
            logger.error(f"Error auto-selecting model: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500

