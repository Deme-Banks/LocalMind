"""
Model loader - manages different backends and models
"""

from typing import Dict, Optional, List
from pathlib import Path
import logging
import json

from ..backends.base import BaseBackend, ModelResponse
from ..backends.ollama import OllamaBackend
from ..backends.openai import OpenAIBackend
from ..backends.anthropic import AnthropicBackend
from ..backends.google import GoogleBackend
from ..backends.mistral_ai import MistralAIBackend
from ..backends.cohere import CohereBackend
from ..backends.groq import GroqBackend
from ..backends.transformers import TransformersBackend
from ..backends.gguf import GGUFBackend
from ..utils.config import ConfigManager, LocalMindConfig
from .tool_registry import ToolRegistry
from .tool_executor import ToolExecutor
from .cache import ResponseCache


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
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        self.cache = ResponseCache(ttl=self.config.cache_ttl if hasattr(self.config, 'cache_ttl') else 3600)
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
                elif backend_config.type == "transformers":
                    backend = TransformersBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (transformers library may not be installed)")
                elif backend_config.type == "gguf":
                    backend = GGUFBackend(backend_config.settings)
                    if backend.is_available():
                        self.backends[backend_name] = backend
                        logger.info(f"✅ Backend '{backend_name}' initialized")
                    else:
                        logger.warning(f"⚠️  Backend '{backend_name}' not available (llama-cpp-python may not be installed)")
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
        use_cache: bool = True,
        use_tools: bool = True,
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
            use_cache: Whether to use response cache
            use_tools: Whether to enable tool calling
            **kwargs: Additional parameters
        
        Returns:
            ModelResponse with generated text
        """
        # Check cache first
        if use_cache:
            cached_response = self.cache.get(
                prompt=prompt,
                model=model or self.config.default_model,
                temperature=temperature,
                system_prompt=system_prompt
            )
            if cached_response:
                logger.info(f"📦 Cache hit for prompt")
                return ModelResponse(
                    text=cached_response,
                    model=model or self.config.default_model,
                    metadata={"cached": True}
                )
        
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
        
        # Check if backend supports tool calling and tools are enabled
        tools = None
        if use_tools and backend_instance.supports_tool_calling():
            tools = self.tool_registry.get_tools_for_backend(backend)
            if tools:
                logger.info(f"🔧 Using {len(tools)} tools with {backend}")
        
        # Generate with or without tools
        logger.info(f"🤖 Generating with {backend} / {model}")
        if tools and backend_instance.supports_tool_calling():
            response = backend_instance.generate_with_tools(
                prompt=prompt,
                model=model,
                tools=tools,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Process tool calls if any
            tool_calls = response.metadata.get("tool_calls", [])
            if tool_calls:
                logger.info(f"🔧 Executing {len(tool_calls)} tool calls")
                # Execute tools and get results
                tool_results = self.tool_executor.execute_tool_calls([
                    {
                        "tool": call["function"]["name"],
                        "arguments": json.loads(call["function"]["arguments"])
                    }
                    for call in tool_calls
                ])
                
                # Format results and generate follow-up response
                results_text = self.tool_executor.format_tool_results(tool_results)
                follow_up_prompt = f"{prompt}\n\nTool Results:\n{results_text}"
                
                # Generate follow-up response
                follow_up_response = backend_instance.generate(
                    prompt=follow_up_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Combine responses
                response.text = f"{response.text}\n\n{follow_up_response.text}"
                response.metadata["tool_calls_executed"] = len(tool_calls)
        else:
            response = backend_instance.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        # Cache response
        if use_cache:
            self.cache.set(
                prompt=prompt,
                model=model,
                response=response.text,
                temperature=temperature,
                system_prompt=system_prompt
            )
        
        return response

