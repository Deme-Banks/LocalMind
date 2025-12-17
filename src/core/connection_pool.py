"""
Connection Pool Manager - manages HTTP connection pools for API backends
"""

from typing import Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """Manages HTTP connection pools for efficient API requests"""
    
    _pools: Dict[str, requests.Session] = {}
    _default_config = {
        "pool_connections": 10,  # Number of connection pools to cache
        "pool_maxsize": 20,  # Max connections per pool
        "max_retries": 3,  # Max retries for failed requests
        "backoff_factor": 0.3,  # Backoff factor for retries
        "status_forcelist": [500, 502, 503, 504],  # HTTP status codes to retry
    }
    
    @classmethod
    def get_session(
        cls,
        backend_name: str,
        base_url: str,
        config: Optional[Dict] = None
    ) -> requests.Session:
        """
        Get or create a session with connection pooling for a backend
        
        Args:
            backend_name: Name of the backend (e.g., "openai", "anthropic")
            base_url: Base URL for the API
            config: Optional pool configuration
        
        Returns:
            requests.Session with connection pooling configured
        """
        # Create unique key for this backend+URL combination
        pool_key = f"{backend_name}:{base_url}"
        
        if pool_key not in cls._pools:
            # Create new session with connection pooling
            session = requests.Session()
            
            # Merge config with defaults
            pool_config = cls._default_config.copy()
            if config:
                pool_config.update(config)
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=pool_config["max_retries"],
                backoff_factor=pool_config["backoff_factor"],
                status_forcelist=pool_config["status_forcelist"],
                allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
            )
            
            # Create HTTP adapter with connection pooling
            adapter = HTTPAdapter(
                pool_connections=pool_config["pool_connections"],
                pool_maxsize=pool_config["pool_maxsize"],
                max_retries=retry_strategy
            )
            
            # Mount adapter for HTTP and HTTPS
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            cls._pools[pool_key] = session
            logger.info(f"Created connection pool for {backend_name} ({base_url})")
        
        return cls._pools[pool_key]
    
    @classmethod
    def close_session(cls, backend_name: str, base_url: str):
        """
        Close and remove a session
        
        Args:
            backend_name: Name of the backend
            base_url: Base URL for the API
        """
        pool_key = f"{backend_name}:{base_url}"
        if pool_key in cls._pools:
            cls._pools[pool_key].close()
            del cls._pools[pool_key]
            logger.info(f"Closed connection pool for {backend_name}")
    
    @classmethod
    def close_all(cls):
        """Close all connection pools"""
        for pool_key, session in list(cls._pools.items()):
            session.close()
        cls._pools.clear()
        logger.info("Closed all connection pools")
    
    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """Get statistics about connection pools"""
        return {
            "active_pools": len(cls._pools),
            "total_connections": sum(
                pool.adapters.get("https://", pool.adapters.get("http://")).config.get("pool_maxsize", 0)
                for pool in cls._pools.values()
            )
        }

