from typing import Dict, Any, Optional
from guardrails.content_filter import content_filter
from guardrails.rate_limiter import rate_limiter
from utils.logger import log

class SafetyChecker:
    """Comprehensive safety checks for queries"""
    
    def __init__(self):
        log.info("Initialized SafetyChecker")
    
    async def validate_request(
        self,
        query: str,
        request=None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive request validation
        
        Args:
            query: User query string
            request: FastAPI request object (for rate limiting)
            user_id: Optional user identifier
            
        Returns:
            Dict with validation results
        """
        # Step 1: Input sanitization and basic validation
        validation_result = content_filter.validate_query(query)
        
        if not validation_result["valid"]:
            return {
                "allowed": False,
                "reason": validation_result["reason"],
                "category": validation_result.get("category", "validation_error"),
                "sanitized_query": validation_result.get("sanitized_query")
            }
        
        sanitized_query = validation_result["sanitized_query"]
        
        # Step 2: Rate limiting (if request provided)
        if request:
            identifier = user_id or rate_limiter.get_identifier(request)
            rate_limit_result = rate_limiter.check_rate_limit(identifier)
            
            if not rate_limit_result["allowed"]:
                log.warning(f"Rate limit exceeded for {identifier}: {rate_limit_result['reason']}")
                return {
                    "allowed": False,
                    "reason": rate_limit_result["reason"],
                    "category": "rate_limit",
                    "retry_after": rate_limit_result.get("retry_after"),
                    "sanitized_query": sanitized_query
                }
        
        # All checks passed
        return {
            "allowed": True,
            "sanitized_query": sanitized_query,
            "reason": "Request validated successfully",
            "rate_limit_info": rate_limit_result if request else None
        }


# Global instance
safety_checker = SafetyChecker()