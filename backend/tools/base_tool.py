from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from utils.logger import log

class BaseTool(ABC):
    """Base class for all research tools"""
    
    def __init__(self, name: str, description: str):
        """
        Initialize base tool
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        log.info(f"Initialized tool: {name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dictionary with tool results
        """
        pass
    
    def validate_input(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate tool input parameters
        
        Args:
            **kwargs: Input parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for MCP/LangGraph integration
        
        Returns:
            Tool schema dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }