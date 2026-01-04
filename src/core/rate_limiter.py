"""
Rate Limiter - Rate limiting per user/IP
"""

import time
from typing import Dict, Tuple, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int  # Number of requests
    window: int  # Time window in seconds


class RateLimiter:
    """Rate limiting per user/IP address"""
    
    def __init__(
        self,
        default_limit: RateLimit = RateLimit(requests=100, window=60),
        per_user_limits: Optional[Dict[str, RateLimit]] = None
    ):
        """
        Initialize rate limiter
        
        Args:
            default_limit: Default rate limit for all users
            per_user_limits: Custom limits per user/IP
        """
        self.default_limit = default_limit
        self.per_user_limits = per_user_limits or {}
        
        # Track requests: {identifier: deque of timestamps}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
    
    def is_allowed(
        self,
        identifier: str,
        custom_limit: Optional[RateLimit] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed
        
        Args:
            identifier: User/IP identifier
            custom_limit: Optional custom limit for this check
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Get limit for this identifier
        limit = custom_limit or self.per_user_limits.get(identifier) or self.default_limit
        
        # Get request history
        history = self.request_history[identifier]
        now = time.time()
        
        # Remove old requests outside the window
        while history and history[0] < now - limit.window:
            history.popleft()
        
        # Check if limit exceeded
        if len(history) >= limit.requests:
            retry_after = limit.window - (now - history[0]) if history else limit.window
            return False, f"Rate limit exceeded. Try again in {int(retry_after)} seconds."
        
        # Record this request
        history.append(now)
        
        return True, None
    
    def get_remaining(
        self,
        identifier: str,
        custom_limit: Optional[RateLimit] = None
    ) -> int:
        """
        Get remaining requests in current window
        
        Args:
            identifier: User/IP identifier
            custom_limit: Optional custom limit
            
        Returns:
            Number of remaining requests
        """
        limit = custom_limit or self.per_user_limits.get(identifier) or self.default_limit
        history = self.request_history[identifier]
        now = time.time()
        
        # Remove old requests
        while history and history[0] < now - limit.window:
            history.popleft()
        
        remaining = limit.requests - len(history)
        return max(0, remaining)
    
    def reset(self, identifier: Optional[str] = None):
        """
        Reset rate limit for identifier or all
        
        Args:
            identifier: User/IP identifier (None for all)
        """
        if identifier:
            self.request_history.pop(identifier, None)
        else:
            self.request_history.clear()
    
    def get_stats(self, identifier: str) -> Dict[str, Any]:
        """
        Get rate limit statistics for identifier
        
        Args:
            identifier: User/IP identifier
            
        Returns:
            Statistics dictionary
        """
        limit = self.per_user_limits.get(identifier) or self.default_limit
        history = self.request_history[identifier]
        now = time.time()
        
        # Remove old requests
        while history and history[0] < now - limit.window:
            history.popleft()
        
        return {
            "limit": limit.requests,
            "window": limit.window,
            "used": len(history),
            "remaining": max(0, limit.requests - len(history)),
            "reset_in": limit.window - (now - history[0]) if history else 0
        }

