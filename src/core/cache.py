"""
Response Cache - caches AI responses for performance
"""

from typing import Dict, Any, Optional
import hashlib
import json
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    """Cache for AI responses"""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = 3600):
        """
        Initialize response cache
        
        Args:
            cache_dir: Directory for cache files (default: ~/.localmind/cache)
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".localmind" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self.memory_cache: Dict[str, Dict[str, Any]] = {}  # In-memory cache
        self.max_memory_entries = 100  # Limit memory cache size
    
    def _get_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """
        Generate cache key from prompt and parameters
        
        Args:
            prompt: User prompt
            model: Model name
            **kwargs: Additional parameters
        
        Returns:
            Cache key (hash)
        """
        # Create a unique key from prompt, model, and relevant parameters
        key_data = {
            "prompt": prompt,
            "model": model,
            "temperature": kwargs.get("temperature"),
            "system_prompt": kwargs.get("system_prompt")
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, **kwargs) -> Optional[str]:
        """
        Get cached response
        
        Args:
            prompt: User prompt
            model: Model name
            **kwargs: Additional parameters
        
        Returns:
            Cached response text or None if not found/expired
        """
        cache_key = self._get_cache_key(prompt, model, **kwargs)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if time.time() - entry["timestamp"] < self.ttl:
                logger.debug(f"Cache hit (memory): {cache_key[:8]}")
                return entry["response"]
            else:
                # Expired, remove from memory
                del self.memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                
                if time.time() - entry["timestamp"] < self.ttl:
                    # Valid cache entry
                    response = entry["response"]
                    # Add to memory cache
                    self._add_to_memory_cache(cache_key, response)
                    logger.debug(f"Cache hit (disk): {cache_key[:8]}")
                    return response
                else:
                    # Expired, delete file
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error reading cache file: {e}")
        
        return None
    
    def set(self, prompt: str, model: str, response: str, **kwargs):
        """
        Cache a response
        
        Args:
            prompt: User prompt
            model: Model name
            response: Response text
            **kwargs: Additional parameters
        """
        cache_key = self._get_cache_key(prompt, model, **kwargs)
        
        # Add to memory cache
        self._add_to_memory_cache(cache_key, response)
        
        # Save to disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            entry = {
                "prompt": prompt,
                "model": model,
                "response": response,
                "timestamp": time.time(),
                "parameters": kwargs
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2)
        except Exception as e:
            logger.warning(f"Error writing cache file: {e}")
    
    def _add_to_memory_cache(self, cache_key: str, response: str):
        """Add entry to memory cache with size limit"""
        # Remove oldest entries if cache is full
        if len(self.memory_cache) >= self.max_memory_entries:
            # Remove oldest entry
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]["timestamp"]
            )
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
    
    def clear(self):
        """Clear all cache entries"""
        self.memory_cache.clear()
        
        # Clear disk cache
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        disk_entries = len(list(self.cache_dir.glob("*.json")))
        return {
            "memory_entries": len(self.memory_cache),
            "disk_entries": disk_entries,
            "max_memory_entries": self.max_memory_entries,
            "ttl": self.ttl
        }

