"""
Model manager - handles model loading, unloading, and memory management
"""

import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model lifecycle and automatic unloading"""
    
    def __init__(self, idle_timeout: int = 300, check_interval: int = 60):
        """
        Initialize model manager
        
        Args:
            idle_timeout: Time in seconds before unloading idle models (default: 5 minutes)
            check_interval: Interval in seconds to check for idle models (default: 1 minute)
        """
        self.idle_timeout = idle_timeout
        self.check_interval = check_interval
        
        # Track model usage
        self.model_last_used: Dict[str, float] = {}  # model_name -> timestamp
        self.model_loaded: Dict[str, bool] = {}  # model_name -> is_loaded
        self.model_backend: Dict[str, str] = {}  # model_name -> backend_name
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Auto-unload thread
        self.auto_unload_thread: Optional[threading.Thread] = None
        self.running = False
    
    def start_auto_unload(self):
        """Start the automatic model unloading thread"""
        if self.running:
            return
        
        self.running = True
        self.auto_unload_thread = threading.Thread(target=self._auto_unload_loop, daemon=True)
        self.auto_unload_thread.start()
        logger.info(f"Started automatic model unloading (idle timeout: {self.idle_timeout}s)")
    
    def stop_auto_unload(self):
        """Stop the automatic model unloading thread"""
        self.running = False
        if self.auto_unload_thread:
            self.auto_unload_thread.join(timeout=2)
        logger.info("Stopped automatic model unloading")
    
    def _auto_unload_loop(self):
        """Main loop for automatic model unloading"""
        while self.running:
            try:
                self._check_and_unload_idle_models()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in auto-unload loop: {e}", exc_info=True)
                time.sleep(self.check_interval)
    
    def _check_and_unload_idle_models(self):
        """Check for idle models and unload them"""
        current_time = time.time()
        idle_models = []
        
        with self.lock:
            for model_name, last_used in self.model_last_used.items():
                if not self.model_loaded.get(model_name, False):
                    continue
                
                idle_time = current_time - last_used
                if idle_time >= self.idle_timeout:
                    idle_models.append(model_name)
        
        # Unload idle models
        for model_name in idle_models:
            try:
                self.unload_model(model_name, backend_name=self.model_backend.get(model_name))
                logger.info(f"Auto-unloaded idle model: {model_name} (idle for {idle_time:.0f}s)")
            except Exception as e:
                logger.warning(f"Failed to auto-unload model {model_name}: {e}")
    
    def register_model_usage(self, model_name: str, backend_name: str):
        """
        Register that a model was used
        
        Args:
            model_name: Name of the model
            backend_name: Name of the backend
        """
        with self.lock:
            self.model_last_used[model_name] = time.time()
            self.model_loaded[model_name] = True
            self.model_backend[model_name] = backend_name
    
    def register_model_loaded(self, model_name: str, backend_name: str):
        """
        Register that a model was loaded
        
        Args:
            model_name: Name of the model
            backend_name: Name of the backend
        """
        with self.lock:
            self.model_last_used[model_name] = time.time()
            self.model_loaded[model_name] = True
            self.model_backend[model_name] = backend_name
    
    def register_model_unloaded(self, model_name: str):
        """
        Register that a model was unloaded
        
        Args:
            model_name: Name of the model
        """
        with self.lock:
            self.model_loaded[model_name] = False
    
    def unload_model(self, model_name: str, backend_name: Optional[str] = None) -> bool:
        """
        Unload a model from memory
        
        Args:
            model_name: Name of the model to unload
            backend_name: Optional backend name (will try to find if not provided)
            
        Returns:
            True if model was unloaded successfully
        """
        if not backend_name:
            backend_name = self.model_backend.get(model_name)
        
        if not backend_name:
            logger.warning(f"Cannot unload model {model_name}: backend not known")
            return False
        
        # This will be called by the backend's unload_model method
        # We just track it here
        self.register_model_unloaded(model_name)
        return True
    
    def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """
        Get status information for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model status information
        """
        with self.lock:
            is_loaded = self.model_loaded.get(model_name, False)
            last_used = self.model_last_used.get(model_name)
            backend = self.model_backend.get(model_name)
            
            if last_used:
                idle_time = time.time() - last_used
                time_until_unload = max(0, self.idle_timeout - idle_time)
            else:
                idle_time = None
                time_until_unload = None
            
            return {
                "model": model_name,
                "loaded": is_loaded,
                "backend": backend,
                "last_used": datetime.fromtimestamp(last_used).isoformat() if last_used else None,
                "idle_time_seconds": idle_time,
                "time_until_unload_seconds": time_until_unload,
                "idle_timeout_seconds": self.idle_timeout
            }
    
    def get_all_models_status(self) -> List[Dict[str, Any]]:
        """
        Get status for all tracked models
        
        Returns:
            List of model status dictionaries
        """
        with self.lock:
            model_names = set(self.model_loaded.keys())
        
        return [self.get_model_status(model_name) for model_name in model_names]
    
    def set_idle_timeout(self, timeout: int):
        """
        Set the idle timeout for automatic unloading
        
        Args:
            timeout: Time in seconds before unloading idle models
        """
        self.idle_timeout = max(60, timeout)  # Minimum 1 minute
        logger.info(f"Updated idle timeout to {self.idle_timeout}s")
    
    def force_unload_all(self) -> Dict[str, bool]:
        """
        Force unload all loaded models
        
        Returns:
            Dictionary mapping model names to unload success status
        """
        results = {}
        
        with self.lock:
            loaded_models = [
                (name, self.model_backend.get(name))
                for name, loaded in self.model_loaded.items()
                if loaded
            ]
        
        for model_name, backend_name in loaded_models:
            try:
                success = self.unload_model(model_name, backend_name)
                results[model_name] = success
            except Exception as e:
                logger.error(f"Failed to force unload {model_name}: {e}")
                results[model_name] = False
        
        return results

