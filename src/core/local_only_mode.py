"""
Local-Only Mode - Enforce local-only operation, block API backends
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class LocalOnlyMode:
    """Enforces local-only mode, blocking API backends"""
    
    def __init__(self, enabled: bool = False):
        """
        Initialize local-only mode
        
        Args:
            enabled: Whether local-only mode is enabled
        """
        self.enabled = enabled
        
        # Local backends (allowed)
        self.local_backends = {
            "ollama",
            "transformers",
            "gguf"
        }
        
        # API backends (blocked when enabled)
        self.api_backends = {
            "openai",
            "anthropic",
            "google",
            "mistral-ai",
            "cohere",
            "groq"
        }
    
    def is_allowed(self, backend_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if backend is allowed in local-only mode
        
        Args:
            backend_name: Name of backend to check
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not self.enabled:
            return True, None
        
        backend_lower = backend_name.lower()
        
        # Check if it's a local backend
        if backend_lower in self.local_backends:
            return True, None
        
        # Check if it's an API backend
        if backend_lower in self.api_backends:
            return False, f"API backend '{backend_name}' is not allowed in local-only mode. Only local backends are permitted."
        
        # Unknown backend - allow by default but warn
        logger.warning(f"Unknown backend '{backend_name}' in local-only mode")
        return True, None
    
    def filter_models(self, models: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Filter models to only include local backends
        
        Args:
            models: Dictionary of {backend: [models]}
            
        Returns:
            Filtered models dictionary
        """
        if not self.enabled:
            return models
        
        filtered = {}
        for backend, model_list in models.items():
            is_allowed, _ = self.is_allowed(backend)
            if is_allowed:
                filtered[backend] = model_list
        
        return filtered
    
    def get_blocked_backends(self) -> List[str]:
        """Get list of blocked backends when local-only mode is enabled"""
        if not self.enabled:
            return []
        return list(self.api_backends)
    
    def get_allowed_backends(self) -> List[str]:
        """Get list of allowed backends"""
        return list(self.local_backends)
    
    def enable(self):
        """Enable local-only mode"""
        self.enabled = True
        logger.info("Local-only mode enabled - API backends will be blocked")
    
    def disable(self):
        """Disable local-only mode"""
        self.enabled = False
        logger.info("Local-only mode disabled - All backends allowed")

