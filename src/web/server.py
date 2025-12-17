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
from typing import Dict, Any, Optional, Tuple
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import logging

from ..core.model_loader import ModelLoader
from ..core.model_registry import ModelRegistry
from ..core.conversation_manager import ConversationManager
from ..core.context_manager import ContextManager
from ..core.module_loader import ModuleLoader
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
                logger.error(f"Error getting providers: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
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
                logger.error(f"Error saving provider: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/status", methods=["GET"])
        def api_status():
            """Get system status"""
            try:
                backends_status = {}
                for backend_name, backend in self.model_loader.backends.items():
                    backends_status[backend_name] = {
                        "available": backend.is_available(),
                        "models": backend.list_models()
                    }
                
                # Get modules status
                modules_status = self.module_loader.list_modules()
                
                return jsonify({
                    "status": "ok",
                    "backends": backends_status,
                    "modules": modules_status,
                    "default_model": self.config_manager.get_config().default_model
                })
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/modules", methods=["GET"])
        def api_list_modules():
            """List all available modules"""
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
                    except:
                        pass
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error getting available models: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
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
                                except:
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
                                                except:
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
                                except:
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
        def api_download_status(download_id):
            """Get download progress"""
            progress = self.download_progress.get(download_id)
            if not progress:
                return jsonify({"status": "error", "message": "Download not found"}), 404
            
            return jsonify({
                "status": "ok",
                "progress": progress
            })
        
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
                    return jsonify({"status": "error", "message": "Conversation not found"}), 404
                return jsonify({
                    "status": "ok",
                    "conversation": conversation
                })
            except Exception as e:
                logger.error(f"Error getting conversation: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/conversations/<conv_id>", methods=["PUT"])
        def api_update_conversation(conv_id):
            """Update conversation metadata"""
            try:
                data = request.get_json() or {}
                title = data.get("title")
                model = data.get("model")
                success = self.conversation_manager.update_conversation(conv_id, title=title, model=model)
                if not success:
                    return jsonify({"status": "error", "message": "Conversation not found"}), 404
                return jsonify({"status": "ok"})
            except Exception as e:
                logger.error(f"Error updating conversation: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/conversations/<conv_id>", methods=["DELETE"])
        def api_delete_conversation(conv_id):
            """Delete a conversation"""
            try:
                success = self.conversation_manager.delete_conversation(conv_id)
                if not success:
                    return jsonify({"status": "error", "message": "Conversation not found"}), 404
                return jsonify({"status": "ok"})
            except Exception as e:
                logger.error(f"Error deleting conversation: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/api/conversations/<conv_id>/export", methods=["GET"])
        def api_export_conversation(conv_id):
            """Export a conversation"""
            try:
                format_type = request.args.get("format", "json")
                exported = self.conversation_manager.export_conversation(conv_id, format=format_type)
                if not exported:
                    return jsonify({"status": "error", "message": "Conversation not found"}), 404
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
        def api_import_conversation():
            """Import a conversation"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "No data provided"}), 400
                conv_id = self.conversation_manager.import_conversation(data)
                if not conv_id:
                    return jsonify({"status": "error", "message": "Import failed"}), 500
                return jsonify({
                    "status": "ok",
                    "conversation_id": conv_id
                })
            except Exception as e:
                logger.error(f"Error importing conversation: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
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
                except:
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
            try:
                data = request.get_json()
                prompt = data.get("prompt")
                model = data.get("model")
                system_prompt = data.get("system_prompt")
                temperature = data.get("temperature", 0.7)
                stream = data.get("stream", False)
                conv_id = data.get("conversation_id")
                
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
                        temperature=temperature
                    )
                    
                    # Save assistant message
                    self.conversation_manager.save_message(
                        conv_id,
                        "assistant",
                        response.text,
                        metadata={"model": response.model, "temperature": temperature}
                    )
                    
                    # Add context metadata to response
                    response_metadata = response.metadata.copy()
                    response_metadata.update(context_metadata)
                    
                    return jsonify({
                        "status": "ok",
                        "response": response.text,
                        "model": response.model,
                        "metadata": response_metadata,
                        "conversation_id": conv_id
                    })
            except Exception as e:
                logger.error(f"Error in chat: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
    
    def run(self, debug: bool = False):
        """Run the web server"""
        logger.info(f"Starting LocalMind web server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)

