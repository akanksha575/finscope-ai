import time
from typing import Dict, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta
from utils.logger import log

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(
        self,
        max_requests_per_minute: int = 10,
        max_requests_per_hour: int = 50,
        max_requests_per_day: int = 200
    ):
        self.max_per_minute = max_requests_per_minute
        self.max_per_hour = max_requests_per_hour
        self.max_per_day = max_requests_per_day
        
        # Track requests by identifier (IP or user_id)
        self.requests: Dict[str, list] = defaultdict(list)
        
        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        log.info(f"Initialized RateLimiter: {max_requests_per_minute}/min, {max_requests_per_hour}/hour, {max_requests_per_day}/day")
    
    def _cleanup_old_entries(self):
        """Remove old request timestamps"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 86400  # 24 hours ago
        
        for identifier in self.requests.keys():
            self.requests[identifier] = [
                ts for ts in self.requests[identifier] if ts > cutoff_time
            ]
            if not self.requests[identifier]:
                del self.requests[identifier]
        
        self.last_cleanup = current_time
    
    def check_rate_limit(self, identifier: str) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            identifier: User IP or user_id
            
        Returns:
            Dict with 'allowed' (bool) and 'reason' (str)
        """
        self._cleanup_old_entries()
        
        current_time = time.time()
        requests = self.requests[identifier]
        
        # Filter requests by time windows
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        day_ago = current_time - 86400
        
        requests_last_minute = [ts for ts in requests if ts > minute_ago]
        requests_last_hour = [ts for ts in requests if ts > hour_ago]
        requests_last_day = [ts for ts in requests if ts > day_ago]
        
        # Check limits
        if len(requests_last_minute) >= self.max_per_minute:
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded: {self.max_per_minute} requests per minute",
                "retry_after": 60 - (current_time - requests_last_minute[0])
            }
        
        if len(requests_last_hour) >= self.max_per_hour:
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded: {self.max_per_hour} requests per hour",
                "retry_after": 3600 - (current_time - requests_last_hour[0])
            }
        
        if len(requests_last_day) >= self.max_per_day:
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded: {self.max_per_day} requests per day",
                "retry_after": 86400 - (current_time - requests_last_day[0])
            }
        
        # Record this request
        requests.append(current_time)
        
        return {
            "allowed": True,
            "remaining_minute": self.max_per_minute - len(requests_last_minute),
            "remaining_hour": self.max_per_hour - len(requests_last_hour),
            "remaining_day": self.max_per_day - len(requests_last_day)
        }
    
    def get_identifier(self, request) -> str:
        """
        Get identifier from request (IP address or user_id)
        
        Args:
            request: FastAPI request object
            
        Returns:
            Identifier string
        """
        # Try to get client IP
        client_ip = request.client.host if hasattr(request, 'client') and request.client else None
        
        # Try to get forwarded IP (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        # Fallback to a default identifier
        if not client_ip:
            client_ip = "unknown"
        
        return client_ip


# Global instance
rate_limiter = RateLimiter()