import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Get environment variable with optional default
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def sanitize_query(query: str) -> str:
    """
    Sanitize user query input
    
    Args:
        query: Raw user query
        
    Returns:
        Sanitized query string
    """
    if not query:
        return ""
    
    # Remove excessive whitespace
    query = " ".join(query.split())
    
    # Limit length (prevent abuse)
    max_length = 1000
    if len(query) > max_length:
        query = query[:max_length].rsplit(" ", 1)[0] + "..."
    
    return query.strip()

def validate_query(query: str) -> tuple[bool, Optional[str]]:
    """
    Validate query input
    
    Args:
        query: User query to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query:
        return False, "Query cannot be empty"
    
    if len(query.strip()) < 3:
        return False, "Query must be at least 3 characters long"
    
    if len(query) > 1000:
        return False, "Query must be less than 1000 characters"
    
    return True, None