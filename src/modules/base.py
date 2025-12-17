"""
Base module interface for LocalMind modules
All modules must implement this interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModuleResponse:
    """Response from a module"""
    content: str
    metadata: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None


class BaseModule(ABC):
    """Base class for all LocalMind modules"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize module
        
        Args:
            config: Module-specific configuration
        """
        self.config = config or {}
        self.name = self.__class__.__name__.replace("Module", "").lower()
        self.enabled = self.config.get("enabled", True)
        self.version = "1.0.0"
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get module information
        
        Returns:
            Dictionary with module metadata (name, description, version, etc.)
        """
        pass
    
    @abstractmethod
    def can_handle(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if this module can handle the given prompt
        
        Args:
            prompt: User prompt
            context: Optional context (conversation history, etc.)
        
        Returns:
            True if module can handle this prompt
        """
        pass
    
    @abstractmethod
    def process(
        self,
        prompt: str,
        model_loader: Any = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ModuleResponse:
        """
        Process a prompt using this module
        
        Args:
            prompt: User prompt
            model_loader: ModelLoader instance for AI generation
            context: Optional context (conversation history, etc.)
            **kwargs: Additional parameters
        
        Returns:
            ModuleResponse with processed content
        """
        pass
    
    def get_commands(self) -> List[Dict[str, str]]:
        """
        Get list of commands/triggers this module supports
        
        Returns:
            List of command dictionaries with 'trigger', 'description', 'example'
        """
        return []
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of tools/functions this module provides
        
        Returns:
            List of tool dictionaries
        """
        return []
    
    def call_module(self, module_name: str, prompt: str, **kwargs) -> Optional[ModuleResponse]:
        """
        Call another module (for inter-module communication)
        
        Args:
            module_name: Name of module to call
            prompt: Prompt to send to module
            **kwargs: Additional parameters
        
        Returns:
            ModuleResponse from called module, or None if module not found
        """
        # This will be set by ModuleLoader
        if hasattr(self, '_module_loader'):
            return self._module_loader.call_module(module_name, prompt, **kwargs)
        return None
    
    def is_enabled(self) -> bool:
        """Check if module is enabled"""
        return self.enabled
    
    def enable(self):
        """Enable the module"""
        self.enabled = True
    
    def disable(self):
        """Disable the module"""
        self.enabled = False

