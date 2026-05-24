"""
Query validation utilities for guardrails
Provides simple validation functions for query safety
"""
from typing import Tuple
from guardrails.content_filter import content_filter
from utils.logger import log

def validate_query_safety(query: str) -> Tuple[bool, str]:
    """
    Validate query safety - simple wrapper for content_filter
    
    Args:
        query: Query string to validate
        
    Returns:
        Tuple of (is_safe: bool, error_message: str)
        - If safe: (True, "")
        - If unsafe: (False, error_message)
    """
    if not query:
        return False, "Query is empty"
    
    try:
        validation_result = content_filter.validate_query(query)
        
        if validation_result["valid"]:
            return True, ""
        else:
            error_msg = validation_result.get("reason", "Query validation failed")
            log.warning(f"Query validation failed: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        log.error(f"Error during query validation: {e}")
        return False, f"Validation error: {str(e)}"









