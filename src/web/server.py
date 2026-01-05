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
from ..core.code_execution_manager import CodeExecutionManager
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
    setup_video_routes,
    setup_code_execution_routes
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
        self.code_execution_manager = CodeExecutionManager(config_manager)
        # Register code execution tool
        self._register_code_execution_tool()
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
        
        # Enable response compression for better performance
        try:
            from flask_compress import Compress
            compress = Compress()
            compress.init_app(self.app)
            logger.info("Response compression enabled")
        except ImportError:
            logger.debug("flask-compress not installed, skipping compression")
        
        # Initialize SocketIO for real-time updates
        try:
            from .routes.video_websocket import init_socketio, setup_video_websocket_routes
            self.socketio = init_socketio(self.app)
            # Setup WebSocket routes
            setup_video_websocket_routes(self.socketio, self)
        except (ImportError, NameError) as e:
            logger.warning(f"Could not initialize SocketIO: {e}. WebSocket features will be disabled.")
            # Create a dummy socketio object for compatibility
            class DummySocketIO:
                def run(self, app, **kwargs):
                    app.run(**{k: v for k, v in kwargs.items() if k != 'allow_unsafe_werkzeug'})
            self.socketio = DummySocketIO()
        
        # Setup routes
        self._setup_routes()
        
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
    
    def _register_code_execution_tool(self):
        """Register code execution as a tool for AI models"""
        try:
            from ..core.tool_registry import ToolParameter
            
            def execute_code_tool(code: str, language: str = None, timeout: int = 30) -> str:
                """Execute code and return result"""
                if not language:
                    language = self.code_execution_manager.detect_language(code)
                    if not language:
                        return "Error: Could not detect programming language. Please specify 'language' parameter."
                
                result = self.code_execution_manager.execute_code(
                    code=code,
                    language=language,
                    timeout=timeout
                )
                
                if result.status.value == "success":
                    return f"Execution successful ({result.execution_time:.2f}s):\n{result.output}"
                else:
                    return f"Execution failed: {result.error}\nOutput: {result.output}"
            
            # Register with model loader's tool registry
            if hasattr(self.model_loader, 'tool_registry'):
                self.model_loader.tool_registry.register_tool(
                    name="execute_code",
                    description="Execute Python or JavaScript code in a sandboxed environment. Use this to run calculations, process data, or test code snippets.",
                    parameters=[
                        ToolParameter("code", "string", "The code to execute", True),
                        ToolParameter("language", "string", "Programming language (python or javascript). Auto-detected if not specified.", False),
                        ToolParameter("timeout", "integer", "Execution timeout in seconds (default: 30)", False)
                    ],
                    function=execute_code_tool,
                    safe=True,
                    requires_confirmation=False
                )
                logger.info("✅ Code execution tool registered")
        except Exception as e:
            logger.warning(f"Failed to register code execution tool: {e}")
    
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
        
        @self.app.route("/code")
        def code_page():
            """Serve code execution page"""
            return render_template("code.html")
        
        # Setup all route modules
        setup_chat_routes(self.app, self)
        setup_model_routes(self.app, self)
        setup_config_routes(self.app, self)
        setup_plugin_routes(self.app, self)
        setup_webhook_routes(self.app, self)
        setup_conversation_routes(self.app, self)
        setup_additional_routes(self.app, self)
        setup_video_routes(self.app, self)
        setup_code_execution_routes(self.app, self)
    
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
        
        # Start cache cleanup task
        self._start_cache_cleanup()
    
    def _start_cache_cleanup(self):
        """Start periodic cache cleanup"""
        import threading
        import time
        
        def cleanup_loop():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    self.video_cache.clear_expired()
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Video cache cleanup started")
    
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
        
        # Default to ollama for unknown models (likely local)
        return "ollama", "ollama"
