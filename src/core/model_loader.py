"""
Model loader - manages different backends and models
"""

from typing import Dict, Optional, List
from pathlib import Path
import logging

from ..backends.base import BaseBackend, ModelResponse
from ..backends.ollama import OllamaBackend
from ..backends.openai import OpenAIBackend
from ..backends.anthropic import AnthropicBackend
from ..backends.google import GoogleBackend
from ..backends.mistral_ai import MistralAIBackend
from ..backends.cohere import CohereBackend
from ..backends.groq import GroqBackend
from ..utils.config import ConfigManager, LocalMindConfig


logger = logging.getLogger(__name__)


class ModelLoader:
    """Manages model backends and loading"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize model loader
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.backends: Dict[str, BaseBackend] = {}
        self._initialize_backends()
    
    def _initialize_backends(self) -> None:
        """Initialize available backends"""
        for backend_name, backend_config in self.config.backends.items():
            if not backend_config.enabled:
                continue
            
            try:
                if backend_config.type == "ollama":
                    backend = OllamaBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available")
                elif backend_config.type == "openai":
                    backend = OpenAIBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (check API key)")
                elif backend_config.type == "anthropic":
                    backend = AnthropicBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (check API key)")
                elif backend_config.type == "google":
                    backend = GoogleBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (check API key)")
                elif backend_config.type == "mistral-ai":
                    backend = MistralAIBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (check API key)")
                elif backend_config.type == "cohere":
                    backend = CohereBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (check API key)")
                elif backend_config.type == "groq":
                    backend = GroqBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (check API key)")
                # Add more backends here as they're implemented
                # elif backend_config.type == "transformers":
                #     backend = TransformersBackend(backend_config.settings)
                #     ...
            except Exception as e:
                logger.error(f"❌ Failed to initialize backend '{backend_name}': {e}")
    
    def get_backend(self, backend_name: Optional[str] = None) -> Optional[BaseBackend]:
        """
        Get a backend by name
        
        Args:
            backend_name: Name of backend, or None for default
        
        Returns:
            Backend instance or None if not found
        """
        if backend_name is None:
            # Try to find a default backend
            if self.backends:
                return next(iter(self.backends.values()))
            return None
        
        return self.backends.get(backend_name)
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """
        List all available models across all backends
        
        Returns:
            Dictionary mapping backend names to lists of model names
        """
        models = {}
        for backend_name, backend in self.backends.items():
            try:
                models[backend_name] = backend.list_models()
            except Exception as e:
                logger.error(f"Error listing models for {backend_name}: {e}")
                models[backend_name] = []
        return models
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        backend: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text using specified model
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if not specified)
            backend: Backend name (auto-detects if not specified)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            ModelResponse with generated text
        """
        # Get model configuration
        if model is None:
            model = self.config.default_model
        
        model_config = self.config.models.get(model)
        if model_config:
            if backend is None:
                backend = model_config.backend
            if temperature is None:
                temperature = model_config.temperature
            if max_tokens is None:
                max_tokens = model_config.max_tokens
        else:
            # Fallback to defaults
            if backend is None:
                backend = next(iter(self.backends.keys())) if self.backends else None
            if temperature is None:
                temperature = 0.7
        
        # Get backend
        backend_instance = self.get_backend(backend)
        if backend_instance is None:
            raise RuntimeError(f"No available backend found (tried: {backend})")
        
        # Generate
        logger.info(f"🤖 Generating with {backend} / {model}")
        return backend_instance.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

