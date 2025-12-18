"""
Model registry - manages model metadata and information for all backends
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages model metadata and information for multiple backends"""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize model registry
        
        Args:
            registry_path: Path to store model registry (default: models/registry.json)
        """
        if registry_path is None:
            # Use project root models directory
            registry_path = Path(__file__).parent.parent.parent / "models" / "registry.json"
        
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry: Dict[str, Any] = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from file"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
                return {"backends": {}, "models": {}, "last_updated": None}
        return {"backends": {}, "models": {}, "last_updated": None}
    
    def _save_registry(self):
        """Save registry to file"""
        try:
            with open(self.registry_path, 'w') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def get_available_models(self, backend_name: str, backend_instance: Any = None) -> List[Dict[str, Any]]:
        """
        Get list of available models for a specific backend
        
        Args:
            backend_name: Name of the backend (e.g., "ollama", "transformers")
            backend_instance: Optional backend instance to check installed models
        
        Returns:
            List of model information dictionaries
        """
        # Get installed models from backend if available
        installed = []
        if backend_instance and hasattr(backend_instance, 'list_models'):
            try:
                installed = backend_instance.list_models()
            except Exception:
                pass
        
        # Get models for this backend from registry
        backend_models = self._get_backend_models(backend_name)
        
        # Update installed status
        for model in backend_models:
            model["installed"] = model["name"] in installed
        
        return backend_models
    
    def _get_backend_models(self, backend_name: str) -> List[Dict[str, Any]]:
        """Get model list for a specific backend"""
        if backend_name == "ollama":
            return self._get_ollama_models()
        elif backend_name == "transformers":
            return self._get_transformers_models()
        elif backend_name == "openai":
            return self._get_openai_models()
        elif backend_name == "anthropic":
            return self._get_anthropic_models()
        elif backend_name == "google":
            return self._get_google_models()
        elif backend_name == "mistral-ai":
            return self._get_mistral_ai_models()
        elif backend_name == "cohere":
            return self._get_cohere_models()
        elif backend_name == "groq":
            return self._get_groq_models()
        else:
            return []
    
    def _get_ollama_models(self) -> List[Dict[str, Any]]:
        """Get Ollama models list"""
        return [
            # Llama Models
            {"name": "llama2", "size": "3.8GB", "description": "Meta's Llama 2 model - general purpose", "tags": ["general", "chat"]},
            {"name": "llama2:13b", "size": "7.3GB", "description": "Llama 2 13B - larger, more capable", "tags": ["general", "chat", "large"]},
            {"name": "llama2:70b", "size": "39GB", "description": "Llama 2 70B - most capable", "tags": ["general", "chat", "very-large"]},
            {"name": "llama3", "size": "4.7GB", "description": "Meta Llama 3 - latest generation", "tags": ["general", "chat", "latest"]},
            {"name": "llama3:8b", "size": "4.7GB", "description": "Llama 3 8B - improved performance", "tags": ["general", "chat", "latest"]},
            {"name": "llama3:70b", "size": "40GB", "description": "Llama 3 70B - most capable Llama 3", "tags": ["general", "chat", "latest", "very-large"]},
            {"name": "llama3.1", "size": "4.7GB", "description": "Llama 3.1 - improved version", "tags": ["general", "chat", "latest"]},
            {"name": "llama3.1:8b", "size": "4.7GB", "description": "Llama 3.1 8B", "tags": ["general", "chat", "latest"]},
            {"name": "llama3.1:70b", "size": "40GB", "description": "Llama 3.1 70B - largest Llama 3.1", "tags": ["general", "chat", "latest", "very-large"]},
            # Mistral Models
            {"name": "mistral", "size": "4.1GB", "description": "Mistral AI 7B - efficient and capable", "tags": ["general", "chat", "efficient"]},
            {"name": "mistral:7b-instruct", "size": "4.1GB", "description": "Mistral 7B Instruct - optimized for instructions", "tags": ["general", "instruct", "chat"]},
            {"name": "mixtral", "size": "26GB", "description": "Mixtral 8x7B - mixture of experts", "tags": ["general", "chat", "large", "experts"]},
            {"name": "mixtral:8x7b-instruct", "size": "26GB", "description": "Mixtral 8x7B Instruct", "tags": ["general", "instruct", "large", "experts"]},
            # Code Models
            {"name": "codellama", "size": "3.8GB", "description": "Code Llama - specialized for code generation", "tags": ["code", "programming"]},
            {"name": "codellama:13b", "size": "7.3GB", "description": "Code Llama 13B - larger code model", "tags": ["code", "programming", "large"]},
            {"name": "deepseek-coder", "size": "4.1GB", "description": "DeepSeek Coder - advanced code generation", "tags": ["code", "programming", "advanced"]},
            # Phi Models
            {"name": "phi3", "size": "2.3GB", "description": "Microsoft Phi-3 - small but capable", "tags": ["general", "small", "efficient"]},
            {"name": "phi3:mini", "size": "2.3GB", "description": "Phi-3 Mini - smallest variant", "tags": ["general", "small", "efficient"]},
            # DeepSeek Models
            {"name": "deepseek-r1", "size": "4.7GB", "description": "DeepSeek R1 - reasoning model", "tags": ["reasoning", "general"]},
            {"name": "deepseek", "size": "4.7GB", "description": "DeepSeek - general purpose model", "tags": ["general", "chat"]},
            # Google Models
            {"name": "gemma", "size": "2.0GB", "description": "Google Gemma - open model", "tags": ["general", "chat"]},
            {"name": "gemma:7b", "size": "5.4GB", "description": "Google Gemma 7B", "tags": ["general", "chat", "large"]},
            # Qwen Models
            {"name": "qwen2", "size": "4.4GB", "description": "Qwen2 - improved multilingual model", "tags": ["general", "multilingual"]},
            {"name": "qwen2.5", "size": "4.4GB", "description": "Qwen2.5 - latest Qwen version", "tags": ["general", "multilingual", "latest"]},
            # Specialized
            {"name": "neural-chat", "size": "4.1GB", "description": "Intel Neural Chat - conversational AI", "tags": ["chat", "conversational"]},
            {"name": "starling-lm", "size": "4.1GB", "description": "Starling LM - fine-tuned for helpfulness", "tags": ["general", "helpful", "chat"]},
            {"name": "nous-hermes2", "size": "4.1GB", "description": "Nous Hermes 2 - fine-tuned for instruction following", "tags": ["instruct", "helpful"]},
            {"name": "tinyllama", "size": "637MB", "description": "TinyLlama - ultra small model", "tags": ["general", "tiny", "efficient"]},
        ]
    
    def _get_transformers_models(self) -> List[Dict[str, Any]]:
        """Get HuggingFace Transformers models list"""
        return [
            # Small Models (Good for testing)
            {"name": "gpt2", "size": "500MB", "description": "GPT-2 - OpenAI's original model", "tags": ["general", "small", "classic"]},
            {"name": "distilgpt2", "size": "350MB", "description": "DistilGPT-2 - smaller, faster GPT-2", "tags": ["general", "small", "efficient"]},
            {"name": "microsoft/DialoGPT-small", "size": "117MB", "description": "DialoGPT Small - conversational", "tags": ["chat", "conversational", "small"]},
            {"name": "microsoft/DialoGPT-medium", "size": "350MB", "description": "DialoGPT Medium - conversational model", "tags": ["chat", "conversational"]},
            
            # Medium Models
            {"name": "EleutherAI/gpt-neo-125M", "size": "500MB", "description": "GPT-Neo 125M - open source GPT alternative", "tags": ["general", "small", "open-source"]},
            {"name": "EleutherAI/gpt-neo-1.3B", "size": "5GB", "description": "GPT-Neo 1.3B - larger open source model", "tags": ["general", "medium", "open-source"]},
            {"name": "EleutherAI/gpt-neo-2.7B", "size": "11GB", "description": "GPT-Neo 2.7B - capable open source model", "tags": ["general", "medium", "open-source"]},
            
            # Code Models
            {"name": "microsoft/CodeGPT-small-py", "size": "350MB", "description": "CodeGPT Small - Python code generation", "tags": ["code", "python", "small"]},
            {"name": "Salesforce/codegen-350M-mono", "size": "700MB", "description": "CodeGen 350M - code generation model", "tags": ["code", "programming"]},
            
            # Instruction-Tuned Models
            {"name": "google/flan-t5-small", "size": "240MB", "description": "FLAN-T5 Small - instruction following", "tags": ["instruct", "small", "efficient"]},
            {"name": "google/flan-t5-base", "size": "990MB", "description": "FLAN-T5 Base - instruction following", "tags": ["instruct", "medium"]},
            {"name": "google/flan-t5-large", "size": "3GB", "description": "FLAN-T5 Large - instruction following", "tags": ["instruct", "large"]},
            
            # Note: Larger models (7B+) are available but require significant RAM/VRAM
            # Users can specify any HuggingFace model ID, these are just curated suggestions
        ]
    
    def _get_openai_models(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible models list"""
        return [
            # GPT-3.5 Models
            {"name": "gpt-3.5-turbo", "size": "API", "description": "GPT-3.5 Turbo - fast and efficient", "tags": ["api", "general", "fast"]},
            {"name": "gpt-3.5-turbo-16k", "size": "API", "description": "GPT-3.5 Turbo 16K - larger context window", "tags": ["api", "general", "large-context"]},
            {"name": "gpt-3.5-turbo-1106", "size": "API", "description": "GPT-3.5 Turbo (Nov 2023) - latest version", "tags": ["api", "general", "latest"]},
            {"name": "gpt-3.5-turbo-0125", "size": "API", "description": "GPT-3.5 Turbo (Jan 2025) - newest version", "tags": ["api", "general", "latest"]},
            
            # GPT-4 Models
            {"name": "gpt-4", "size": "API", "description": "GPT-4 - most capable model", "tags": ["api", "general", "advanced", "premium"]},
            {"name": "gpt-4-turbo", "size": "API", "description": "GPT-4 Turbo - faster GPT-4", "tags": ["api", "general", "advanced", "fast"]},
            {"name": "gpt-4-turbo-preview", "size": "API", "description": "GPT-4 Turbo Preview - latest features", "tags": ["api", "general", "advanced", "preview"]},
            {"name": "gpt-4-0125-preview", "size": "API", "description": "GPT-4 (Jan 2025 Preview)", "tags": ["api", "general", "advanced", "preview"]},
            {"name": "gpt-4-1106-preview", "size": "API", "description": "GPT-4 (Nov 2023 Preview)", "tags": ["api", "general", "advanced", "preview"]},
            {"name": "gpt-4-32k", "size": "API", "description": "GPT-4 32K - very large context", "tags": ["api", "general", "advanced", "large-context"]},
            {"name": "gpt-4-turbo-2024-04-09", "size": "API", "description": "GPT-4 Turbo (April 2024)", "tags": ["api", "general", "advanced"]},
            
            # GPT-4o Models (Latest)
            {"name": "gpt-4o", "size": "API", "description": "GPT-4o - optimized model", "tags": ["api", "general", "advanced", "optimized", "latest"]},
            {"name": "gpt-4o-2024-05-13", "size": "API", "description": "GPT-4o (May 2024)", "tags": ["api", "general", "advanced", "optimized"]},
            {"name": "gpt-4o-mini", "size": "API", "description": "GPT-4o Mini - smaller, faster", "tags": ["api", "general", "fast", "efficient"]},
            
            # Legacy Models
            {"name": "gpt-3.5-turbo-instruct", "size": "API", "description": "GPT-3.5 Turbo Instruct - instruction following", "tags": ["api", "instruct"]},
            {"name": "text-davinci-003", "size": "API", "description": "Text Davinci 003 - legacy model", "tags": ["api", "legacy"]},
            {"name": "text-davinci-002", "size": "API", "description": "Text Davinci 002 - legacy model", "tags": ["api", "legacy"]},
        ]
    
    def _get_anthropic_models(self) -> List[Dict[str, Any]]:
        """Get Anthropic Claude models list"""
        return [
            {"name": "claude-3-opus-20240229", "size": "API", "description": "Claude 3 Opus - most capable", "tags": ["api", "general", "advanced", "premium"]},
            {"name": "claude-3-sonnet-20240229", "size": "API", "description": "Claude 3 Sonnet - balanced performance", "tags": ["api", "general", "balanced"]},
            {"name": "claude-3-haiku-20240307", "size": "API", "description": "Claude 3 Haiku - fast and efficient", "tags": ["api", "general", "fast", "efficient"]},
            {"name": "claude-3-5-sonnet-20241022", "size": "API", "description": "Claude 3.5 Sonnet (Oct 2024) - latest generation", "tags": ["api", "general", "latest", "advanced"]},
            {"name": "claude-3-5-sonnet-20240620", "size": "API", "description": "Claude 3.5 Sonnet (Jun 2024)", "tags": ["api", "general", "advanced"]},
            {"name": "claude-2.1", "size": "API", "description": "Claude 2.1 - improved version", "tags": ["api", "general"]},
            {"name": "claude-2.0", "size": "API", "description": "Claude 2.0 - previous generation", "tags": ["api", "general"]},
            {"name": "claude-instant-1.2", "size": "API", "description": "Claude Instant 1.2 - fast model", "tags": ["api", "general", "fast"]},
        ]
    
    def _get_google_models(self) -> List[Dict[str, Any]]:
        """Get Google Gemini models list"""
        return [
            {"name": "gemini-pro", "size": "API", "description": "Gemini Pro - Google's advanced model", "tags": ["api", "general", "advanced"]},
            {"name": "gemini-pro-vision", "size": "API", "description": "Gemini Pro Vision - with image support", "tags": ["api", "general", "vision", "multimodal"]},
            {"name": "gemini-1.5-pro", "size": "API", "description": "Gemini 1.5 Pro - latest generation", "tags": ["api", "general", "latest", "advanced"]},
            {"name": "gemini-1.5-flash", "size": "API", "description": "Gemini 1.5 Flash - fast and efficient", "tags": ["api", "general", "fast", "efficient"]},
            {"name": "gemini-ultra", "size": "API", "description": "Gemini Ultra - most capable", "tags": ["api", "general", "premium", "advanced"]},
        ]
    
    def _get_mistral_ai_models(self) -> List[Dict[str, Any]]:
        """Get Mistral AI API models list"""
        return [
            {"name": "mistral-tiny", "size": "API", "description": "Mistral Tiny - smallest API model", "tags": ["api", "general", "small", "fast"]},
            {"name": "mistral-small", "size": "API", "description": "Mistral Small - balanced API model", "tags": ["api", "general", "balanced"]},
            {"name": "mistral-medium", "size": "API", "description": "Mistral Medium - capable API model", "tags": ["api", "general", "advanced"]},
            {"name": "mistral-large", "size": "API", "description": "Mistral Large - most capable API model", "tags": ["api", "general", "premium", "advanced"]},
        ]
    
    def _get_cohere_models(self) -> List[Dict[str, Any]]:
        """Get Cohere models list"""
        return [
            {"name": "command", "size": "API", "description": "Cohere Command - general purpose", "tags": ["api", "general"]},
            {"name": "command-light", "size": "API", "description": "Cohere Command Light - faster", "tags": ["api", "general", "fast"]},
            {"name": "command-r", "size": "API", "description": "Cohere Command R - advanced", "tags": ["api", "general", "advanced"]},
            {"name": "command-r-plus", "size": "API", "description": "Cohere Command R+ - most capable", "tags": ["api", "general", "premium", "advanced"]},
        ]
    
    def _get_groq_models(self) -> List[Dict[str, Any]]:
        """Get Groq models list (fast inference)"""
        return [
            {"name": "llama-3.1-70b-versatile", "size": "API", "description": "Llama 3.1 70B on Groq - very fast", "tags": ["api", "general", "fast", "large"]},
            {"name": "llama-3.1-8b-instant", "size": "API", "description": "Llama 3.1 8B Instant - ultra fast", "tags": ["api", "general", "very-fast", "efficient"]},
            {"name": "mixtral-8x7b-32768", "size": "API", "description": "Mixtral 8x7B on Groq - fast experts model", "tags": ["api", "general", "fast", "experts"]},
            {"name": "gemma-7b-it", "size": "API", "description": "Gemma 7B Instruct on Groq", "tags": ["api", "general", "fast"]},
            {"name": "llama-3-70b-8192", "size": "API", "description": "Llama 3 70B on Groq", "tags": ["api", "general", "fast", "large"]},
            {"name": "llama-3-8b-8192", "size": "API", "description": "Llama 3 8B on Groq", "tags": ["api", "general", "fast"]},
        ]
    
    def register_model(self, backend_name: str, model_name: str, metadata: Dict[str, Any]):
        """
        Register a model in the registry
        
        Args:
            backend_name: Name of the backend
            model_name: Name of the model
            metadata: Model metadata (size, description, etc.)
        """
        if "backends" not in self.registry:
            self.registry["backends"] = {}
        if backend_name not in self.registry["backends"]:
            self.registry["backends"][backend_name] = {}
        if "models" not in self.registry["backends"][backend_name]:
            self.registry["backends"][backend_name]["models"] = {}
        
        self.registry["backends"][backend_name]["models"][model_name] = {
            **metadata,
            "registered_at": str(Path(__file__).stat().st_mtime)
        }
        self._save_registry()
    
    def get_model_info(self, backend_name: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered model"""
        return self.registry.get("backends", {}).get(backend_name, {}).get("models", {}).get(model_name)
    
    def list_registered_models(self, backend_name: Optional[str] = None) -> List[str]:
        """List all registered model names, optionally filtered by backend"""
        if backend_name:
            return list(self.registry.get("backends", {}).get(backend_name, {}).get("models", {}).keys())
        all_models = []
        for backend_models in self.registry.get("backends", {}).values():
            all_models.extend(backend_models.get("models", {}).keys())
        return all_models
    
    def check_model_updates(
        self, 
        backend_name: str, 
        model_name: str, 
        backend_instance: Any = None
    ) -> Dict[str, Any]:
        """
        Check if a model has updates available
        
        Args:
            backend_name: Name of the backend
            model_name: Name of the model to check
            backend_instance: Optional backend instance for checking
            
        Returns:
            Dictionary with update information:
            {
                "has_update": bool,
                "current_version": str,
                "latest_version": str,
                "update_available": bool,
                "last_checked": str,
                "error": Optional[str]
            }
        """
        result = {
            "has_update": False,
            "current_version": None,
            "latest_version": None,
            "update_available": False,
            "last_checked": datetime.now().isoformat(),
            "error": None
        }
        
        try:
            if backend_name == "ollama":
                result = self._check_ollama_update(model_name, backend_instance)
            elif backend_name == "transformers":
                result = self._check_transformers_update(model_name)
            elif backend_name in ["openai", "anthropic", "google", "mistral-ai", "cohere", "groq"]:
                result = self._check_api_model_update(backend_name, model_name)
            else:
                result["error"] = f"Update checking not supported for backend: {backend_name}"
        except Exception as e:
            logger.error(f"Error checking updates for {backend_name}/{model_name}: {e}", exc_info=True)
            result["error"] = str(e)
        
        # Store last checked time
        self._update_last_checked(backend_name, model_name, result["last_checked"])
        
        return result
    
    def _check_ollama_update(self, model_name: str, backend_instance: Any = None) -> Dict[str, Any]:
        """Check for Ollama model updates"""
        result = {
            "has_update": False,
            "current_version": None,
            "latest_version": None,
            "update_available": False,
            "last_checked": datetime.now().isoformat(),
            "error": None
        }
        
        try:
            # Ollama models are automatically updated when pulled
            # We can check if there's a newer version by attempting to pull
            # For now, we'll indicate that updates are available via pull
            if backend_instance and hasattr(backend_instance, 'list_models'):
                installed_models = backend_instance.list_models()
                if model_name in installed_models:
                    result["current_version"] = "installed"
                    result["latest_version"] = "latest"
                    # Ollama automatically uses latest when model is pulled
                    # User can pull again to update
                    result["update_available"] = True
                    result["has_update"] = True
        except Exception as e:
            result["error"] = f"Error checking Ollama update: {e}"
        
        return result
    
    def _check_transformers_update(self, model_name: str) -> Dict[str, Any]:
        """Check for HuggingFace Transformers model updates"""
        result = {
            "has_update": False,
            "current_version": None,
            "latest_version": None,
            "update_available": False,
            "last_checked": datetime.now().isoformat(),
            "error": None
        }
        
        try:
            # Extract model ID from name (could be "model-name" or "org/model-name")
            model_id = model_name
            if "/" not in model_id:
                # Try to find the full model ID
                model_id = f"microsoft/{model_id}" if model_id.startswith("DialoGPT") else model_id
            
            # Check HuggingFace Hub for latest version
            api_url = f"https://huggingface.co/api/models/{model_id}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result["latest_version"] = data.get("modelId", model_id)
                result["current_version"] = model_name
                # For Transformers, updates are available if model exists on Hub
                result["update_available"] = True
                result["has_update"] = True
            else:
                result["error"] = f"Model not found on HuggingFace Hub: {model_id}"
        except Exception as e:
            result["error"] = f"Error checking Transformers update: {e}"
        
        return result
    
    def _check_api_model_update(self, backend_name: str, model_name: str) -> Dict[str, Any]:
        """Check for API model updates (most API models are always latest)"""
        result = {
            "has_update": False,
            "current_version": model_name,
            "latest_version": model_name,
            "update_available": False,
            "last_checked": datetime.now().isoformat(),
            "error": None
        }
        
        # API models are typically always up-to-date
        # We can check if there are newer model versions available
        try:
            # For API models, check if there's a newer version in the registry
            backend_models = self._get_backend_models(backend_name)
            model_info = next((m for m in backend_models if m["name"] == model_name), None)
            
            if model_info:
                # Check if there are newer models with similar names
                # (e.g., gpt-4-turbo vs gpt-4-turbo-preview)
                similar_models = [m for m in backend_models if model_name.split("-")[0] in m["name"]]
                if len(similar_models) > 1:
                    # Check if any have "latest" tag
                    latest_models = [m for m in similar_models if "latest" in m.get("tags", [])]
                    if latest_models and latest_models[0]["name"] != model_name:
                        result["latest_version"] = latest_models[0]["name"]
                        result["update_available"] = True
                        result["has_update"] = True
        except Exception as e:
            result["error"] = f"Error checking API model update: {e}"
        
        return result
    
    def _update_last_checked(self, backend_name: str, model_name: str, timestamp: str):
        """Update the last checked timestamp for a model"""
        if "backends" not in self.registry:
            self.registry["backends"] = {}
        if backend_name not in self.registry["backends"]:
            self.registry["backends"][backend_name] = {}
        if "models" not in self.registry["backends"][backend_name]:
            self.registry["backends"][backend_name]["models"] = {}
        if model_name not in self.registry["backends"][backend_name]["models"]:
            self.registry["backends"][backend_name]["models"][model_name] = {}
        
        self.registry["backends"][backend_name]["models"][model_name]["last_checked"] = timestamp
        self._save_registry()
    
    def check_all_updates(
        self, 
        backend_name: str, 
        installed_models: List[str], 
        backend_instance: Any = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Check updates for all installed models in a backend
        
        Args:
            backend_name: Name of the backend
            installed_models: List of installed model names
            backend_instance: Optional backend instance
            
        Returns:
            Dictionary mapping model names to their update information
        """
        updates = {}
        for model_name in installed_models:
            updates[model_name] = self.check_model_updates(
                backend_name, 
                model_name, 
                backend_instance
            )
        return updates
