"""
Conversation routes - Handle conversation management endpoints
"""

from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify
import logging

from .base import error_response, success_response

logger = logging.getLogger(__name__)


def setup_conversation_routes(app: Flask, server_instance):
    """
    Setup conversation-related routes
    
    Args:
        app: Flask application
        server_instance: WebServer instance
    """
    
    @app.route("/api/conversations", methods=["GET"])
    def api_list_conversations():
        """List all conversations"""
        try:
            search = request.args.get("search", None)
            limit = request.args.get("limit", type=int)
            conversations = server_instance.conversation_manager.list_conversations(limit=limit, search=search)
            return jsonify(success_response({"conversations": conversations}))
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/conversations", methods=["POST"])
    def api_create_conversation():
        """Create a new conversation"""
        try:
            data = request.get_json() or {}
            title = data.get("title")
            model = data.get("model")
            conv_id = server_instance.conversation_manager.create_conversation(title=title, model=model)
            
            from ...core.webhook_manager import WebhookEvent
            server_instance.webhook_manager.trigger_webhook(
                WebhookEvent.CONVERSATION_CREATED,
                {"conversation_id": conv_id, "title": title, "model": model}
            )
            
            return jsonify(success_response({"conversation_id": conv_id}))
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/conversations/<conv_id>", methods=["GET"])
    def api_get_conversation(conv_id):
        """Get a conversation by ID"""
        try:
            conversation = server_instance.conversation_manager.get_conversation(conv_id)
            if not conversation:
                return jsonify(error_response("Conversation not found", status_code=404, error_type="not_found")), 404
            return jsonify(success_response({"conversation": conversation}))
        except Exception as e:
            logger.error(f"Error getting conversation: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/conversations/<conv_id>", methods=["PUT"])
    def api_update_conversation(conv_id):
        """Update conversation metadata"""
        try:
            data = request.get_json() or {}
            title = data.get("title")
            
            if title:
                server_instance.conversation_manager.update_conversation(conv_id, title=title)
            
            from ...core.webhook_manager import WebhookEvent
            server_instance.webhook_manager.trigger_webhook(
                WebhookEvent.CONVERSATION_UPDATED,
                {"conversation_id": conv_id, "updates": data}
            )
            
            return jsonify(success_response({"message": "Conversation updated"}))
        except Exception as e:
            logger.error(f"Error updating conversation: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/conversations/<conv_id>", methods=["DELETE"])
    def api_delete_conversation(conv_id):
        """Delete a conversation"""
        try:
            server_instance.conversation_manager.delete_conversation(conv_id)
            
            from ...core.webhook_manager import WebhookEvent
            server_instance.webhook_manager.trigger_webhook(
                WebhookEvent.CONVERSATION_DELETED,
                {"conversation_id": conv_id}
            )
            
            return jsonify(success_response({"message": "Conversation deleted"}))
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/conversations/<conv_id>/export", methods=["GET"])
    def api_export_conversation(conv_id):
        """Export conversation in various formats"""
        try:
            format_type = request.args.get("format", "json")
            conversation = server_instance.conversation_manager.get_conversation(conv_id)
            
            if not conversation:
                return jsonify(error_response("Conversation not found", status_code=404, error_type="not_found")), 404
            
            if format_type == "markdown":
                from ...core.conversation_importer import ConversationImporter
                markdown = ConversationImporter.conversation_to_markdown(conversation)
                return jsonify(success_response({"format": "markdown", "content": markdown}))
            elif format_type == "text":
                text = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation.get("messages", [])])
                return jsonify(success_response({"format": "text", "content": text}))
            else:
                return jsonify(success_response({"format": "json", "conversation": conversation}))
        except Exception as e:
            logger.error(f"Error exporting conversation: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500
    
    @app.route("/api/conversations/import", methods=["POST"])
    def api_import_conversation():
        """Import conversation from various formats"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(error_response("No data provided", status_code=400, error_type="validation")), 400
            
            content = data.get("content")
            format_type = data.get("format", "auto")
            
            if not content:
                return jsonify(error_response("Content required", status_code=400, error_type="validation")), 400
            
            imported = server_instance.conversation_importer.import_conversation(content, format_type)
            
            if imported:
                conv_id = imported.get("conversation_id")
                return jsonify(success_response({
                    "conversation_id": conv_id,
                    "message": "Conversation imported successfully"
                }))
            else:
                return jsonify(error_response("Failed to import conversation", status_code=400)), 400
        except ValueError as e:
            return jsonify(error_response(str(e), status_code=400, error_type="validation")), 400
        except Exception as e:
            logger.error(f"Error importing conversation: {e}", exc_info=True)
            return jsonify(error_response(str(e), status_code=500)), 500

