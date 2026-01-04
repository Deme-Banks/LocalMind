"""
Web server routes
Organized by functionality
"""

from .chat_routes import setup_chat_routes
from .model_routes import setup_model_routes
from .config_routes import setup_config_routes
from .plugin_routes import setup_plugin_routes
from .webhook_routes import setup_webhook_routes
from .conversation_routes import setup_conversation_routes
from .additional_routes import setup_additional_routes
from .video_routes import setup_video_routes

__all__ = [
    'setup_chat_routes',
    'setup_model_routes',
    'setup_config_routes',
    'setup_plugin_routes',
    'setup_webhook_routes',
    'setup_conversation_routes',
    'setup_additional_routes',
    'setup_video_routes',
]

