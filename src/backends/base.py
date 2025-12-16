"""
Base backend interface for model backends
All backends must implement this interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator
from pydantic import BaseModel, Field


class ModelResponse(BaseModel):
    """Response from a model"""
    text: str
    model: str
    done: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseBackend(ABC):
    """Base class for all model backends"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize backend
        
        Args:
            config: Backend-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if backend is available and ready
        
        Returns:
            True if backend is available
        """
        pass
    
    @abstractmethod
    def list_models(self) -> list[str]:
        """
        List available models for this backend
        
        Returns:
            List of model identifiers
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text from a prompt
        
        Args:
            prompt: Input prompt
            model: Model identifier
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional backend-specific parameters
        
        Returns:
            ModelResponse with generated text
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate text stream from a prompt
        
        Args:
            prompt: Input prompt
            model: Model identifier
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional backend-specific parameters
        
        Yields:
            Text chunks as they're generated
        """
        pass
    
    @abstractmethod
    def load_model(self, model: str) -> bool:
        """
        Load a model into memory
        
        Args:
            model: Model identifier
        
        Returns:
            True if model loaded successfully
        """
        pass
    
    def unload_model(self, model: str) -> bool:
        """
        Unload a model from memory (optional)
        
        Args:
            model: Model identifier
        
        Returns:
            True if model unloaded successfully
        """
        return True
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """
        Download a model (optional - not all backends support this)
        
        Args:
            model: Model identifier to download
        
        Returns:
            Dictionary with download status and information
        """
        raise NotImplementedError("This backend does not support model downloads")
    
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about this backend
        
        Returns:
            Dictionary with backend information (name, type, capabilities, etc.)
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__.replace("Backend", "").lower(),
            "supports_download": hasattr(self, "download_model") and 
                                 self.download_model.__func__ != BaseBackend.download_model
        }

