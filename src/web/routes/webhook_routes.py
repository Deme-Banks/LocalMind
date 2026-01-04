"""
Webhook routes - Handle webhook management endpoints
"""

from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify
import logging

from .base import error_response, success_response

logger = logging.getLogger(__name__)


def setup_webhook_routes(app: Flask, server_instance):
    """
    Setup webhook-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/webhooks", methods=["GET"])
    def api_list_webhooks() -> Tuple[Dict[str, Any], int]:
        """List all webhooks"""
        try:
            webhooks = server_instance.webhook_manager.list_webhooks()
            return jsonify(success_response({"webhooks": webhooks}))
        except Exception as e:
            logger.error(f"Error listing webhooks: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/webhooks", methods=["POST"])
    def api_create_webhook() -> Tuple[Dict[str, Any], int]:
        """Create a new webhook"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            url = data.get("url")
            events = data.get("events", [])
            secret = data.get("secret")
            enabled = data.get("enabled", True)
            
            if not url:
                return jsonify(error_response("URL required", status_code=400, error_type="validation")), 400
            
            webhook = server_instance.webhook_manager.create_webhook(
                url=url,
                events=events,
                secret=secret,
                enabled=enabled
            )
            
            return jsonify(success_response({
                "webhook_id": webhook["id"],
                "message": "Webhook created successfully"
            }))
        except Exception as e:
            logger.error(f"Error creating webhook: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/webhooks/<webhook_id>", methods=["GET"])
    def api_get_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
        """Get webhook by ID"""
        try:
            webhook = server_instance.webhook_manager.get_webhook(webhook_id)
            if not webhook:
                return jsonify(error_response("Webhook not found", status_code=404, error_type="not_found")), 404
            return jsonify(success_response(webhook))
        except Exception as e:
            logger.error(f"Error getting webhook: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/webhooks/<webhook_id>", methods=["PUT"])
    def api_update_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
        """Update webhook"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            updates = {}
            if "url" in data:
                updates["url"] = data["url"]
            if "events" in data:
                updates["events"] = data["events"]
            if "secret" in data:
                updates["secret"] = data["secret"]
            if "enabled" in data:
                updates["enabled"] = data["enabled"]
            
            success = server_instance.webhook_manager.update_webhook(webhook_id, **updates)
            if success:
                return jsonify(success_response({"message": "Webhook updated successfully"}))
            else:
                return jsonify(error_response("Webhook not found", status_code=404, error_type="not_found")), 404
        except Exception as e:
            logger.error(f"Error updating webhook: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/webhooks/<webhook_id>", methods=["DELETE"])
    def api_delete_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
        """Delete webhook"""
        try:
            success = server_instance.webhook_manager.delete_webhook(webhook_id)
            if success:
                return jsonify(success_response({"message": "Webhook deleted successfully"}))
            else:
                return jsonify(error_response("Webhook not found", status_code=404, error_type="not_found")), 404
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/webhooks/<webhook_id>/test", methods=["POST"])
    def api_test_webhook(webhook_id: str) -> Tuple[Dict[str, Any], int]:
        """Test webhook"""
        try:
            result = server_instance.webhook_manager.test_webhook(webhook_id)
            if result:
                return jsonify(success_response({
                    "message": "Webhook test sent",
                    "result": result
                }))
            else:
                return jsonify(error_response("Webhook not found", status_code=404, error_type="not_found")), 404
        except Exception as e:
            logger.error(f"Error testing webhook: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/webhooks/events", methods=["GET"])
    def api_list_webhook_events() -> Tuple[Dict[str, Any], int]:
        """List available webhook event types"""
        try:
            from ...core.webhook_manager import WebhookEvent
            events = [event.value for event in WebhookEvent]
            return jsonify(success_response({"events": events}))
        except Exception as e:
            logger.error(f"Error listing webhook events: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500

