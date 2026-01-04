"""
Web server for LocalMind
Provides REST API and web interface
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from flask import Flask, render_template
from flask_cors import CORS

from ..core.model_loader import ModelLoader
from ..core.model_registry import ModelRegistry
from ..core.conversation_manager import ConversationManager
from ..core.context_manager import ContextManager
from ..core.video_loader import VideoLoader
from ..core.video_manager import VideoManager
from ..core.video_queue import VideoQueue
from ..core.video_cache import VideoCache
from ..core.video_templates import VideoTemplateManager
from ..core.shared_context import SharedContextManager
from ..core.module_loader import ModuleLoader
from ..core.usage_tracker import UsageTracker
from ..core.resource_monitor import ResourceMonitor
from ..core.resource_cleanup import ResourceCleanup
from ..core.ensemble import EnsembleProcessor
from ..core.model_router import ModelRouter
from ..core.conversation_importer import ConversationImporter
from ..core.config_backup import ConfigBackup
from ..core.migration_tools import MigrationTool
from ..core.webhook_manager import WebhookManager
from ..core.plugin_manager import PluginManager
from ..core.streaming_enhancer import StreamingEnhancer, TokenVisualizer
from ..core.response_quality import ResponseQualityScorer
from ..core.ab_testing import ABTester
from ..core.key_manager import KeyManager
from ..core.audit_logger import AuditLogger
from ..core.rate_limiter import RateLimiter, RateLimit
from ..core.privacy_manager import PrivacyManager
from ..core.conversation_encryption import ConversationEncryption
from ..core.local_only_mode import LocalOnlyMode
from ..core.privacy_audit import PrivacyAuditor
from ..core.finetuning import FineTuningManager
from ..core.model_versioning import ModelVersionManager
from ..utils.config import ConfigManager
from ..utils.logger import setup_logger
from .routes import (
    setup_chat_routes,
    setup_model_routes,
    setup_config_routes,
    setup_plugin_routes,
    setup_webhook_routes,
    setup_conversation_routes,
    setup_additional_routes,
    setup_video_routes
)

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
        self.video_loader = VideoLoader(config_manager)
        self.video_manager = VideoManager()
        self.video_queue = VideoQueue(max_concurrent=3)
        self.video_cache = VideoCache()
        self.video_templates = VideoTemplateManager()
        self.shared_context = SharedContextManager()
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
        self.quality_scorer = ResponseQualityScorer()
        self.ab_tester = ABTester(self.model_loader)
        self.key_manager = KeyManager()
        self.audit_logger = AuditLogger()
        self.rate_limiter = RateLimiter(
            default_limit=RateLimit(requests=100, window=60),
            per_user_limits={}  # Can be configured
        )
        self.privacy_manager = PrivacyManager()
        self.conversation_encryption = ConversationEncryption(self.key_manager)
        
        # Check config for local-only mode
        config = self.config_manager.get_config()
        local_only_enabled = getattr(config, 'local_only_mode', False)
        self.local_only_mode = LocalOnlyMode(enabled=local_only_enabled)
        
        self.privacy_auditor = PrivacyAuditor(
            privacy_manager=self.privacy_manager,
            audit_logger=self.audit_logger,
            conversations_dir=self.conversation_manager.conversations_dir
        )
        self.finetuning_manager = FineTuningManager()
        self.model_version_manager = ModelVersionManager()
        
        self.host = host
        self.port = port
        
        # Create Flask app
        self.app = Flask(
            __name__,
            template_folder=Path(__file__).parent / "templates",
            static_folder=Path(__file__).parent / "static"
        )
        CORS(self.app)
        
        # Initialize SocketIO for real-time updates
        self.socketio = init_socketio(self.app)
        
        # Setup routes
        self._setup_routes()
        
        # Setup WebSocket routes
        setup_video_websocket_routes(self.socketio, self)
        
        # Start video queue processor
        self._start_video_queue_processor()
        
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
    
    def _setup_routes(self):
        """Setup all routes"""
        
        # Basic page routes
        @self.app.route("/")
        def index():
            """Serve main page"""
            return render_template("index.html")
        
        @self.app.route("/configure")
        def configure_page():
            """Serve API configuration page"""
            return render_template("configure.html")
        
        @self.app.route("/video")
        def video_page():
            """Serve video generation page"""
            return render_template("video.html")
        
        # Setup all route modules
        setup_chat_routes(self.app, self)
        setup_model_routes(self.app, self)
        setup_config_routes(self.app, self)
        setup_plugin_routes(self.app, self)
        setup_webhook_routes(self.app, self)
        setup_conversation_routes(self.app, self)
        setup_additional_routes(self.app, self)
        setup_video_routes(self.app, self)
    
    def run(self, debug: bool = False) -> None:
        """
        Run the Flask web server.
        
        Args:
            debug: Enable Flask debug mode (default: False)
        """
        logger.info(f"Starting LocalMind web server on {self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug, allow_unsafe_werkzeug=True)
    
    def _start_video_queue_processor(self):
        """Start background video queue processor"""
        import threading
        import asyncio
        
        def run_processor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.video_queue.start_processor(
                    self.video_loader,
                    self.video_manager,
                    interval=1.0
                )
            )
        
        processor_thread = threading.Thread(target=run_processor, daemon=True)
        processor_thread.start()
        logger.info("Video queue processor started")
        
    def _get_backend_for_model(self, model: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
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
            return "ollama", "ollama"  # Default to ollama for local models
        else:
            # Default to ollama for unknown models (likely local)
            return "ollama", "ollama"
