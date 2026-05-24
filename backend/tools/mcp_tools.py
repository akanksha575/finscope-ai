"""
Full MCP (Model Context Protocol) Implementation

This module provides both a full MCP server implementation and a simplified
interface for backward compatibility with existing code.
"""

import json
from typing import List, Dict, Any, Optional
from tools.web_search import WebSearchTool
from tools.financial_data import FinancialDataTool
from tools.web_scraper import WebScraperTool
from tools.calculator import CalculatorTool
from tools.mcp_server import MCPServer
from tools.mcp_protocol import MCPResource, MCPPrompt
from utils.logger import log


class MCPTools:
    """
    Full MCP implementation with backward-compatible interface
    
    This class wraps the full MCP server and provides:
    1. Full MCP protocol support (JSON-RPC 2.0)
    2. Backward-compatible execute_tool() method
    3. Tool registration and management
    4. Resource and prompt management
    """
    
    def __init__(self):
        """Initialize MCP server and register all tools"""
        # Initialize MCP server
        self.mcp_server = MCPServer(
            name="FinScope MCP Server",
            version="1.0.0"
        )
        
        # Initialize and register tools
        self.web_search = WebSearchTool()
        self.financial_data = FinancialDataTool()
        self.web_scraper = WebScraperTool()
        self.calculator = CalculatorTool()
        
        # Register tools with MCP server
        self.mcp_server.register_tool(self.web_search)
        self.mcp_server.register_tool(self.financial_data)
        self.mcp_server.register_tool(self.web_scraper)
        self.mcp_server.register_tool(self.calculator)
        
        # Maintain backward compatibility
        self.tools = {
            "web_search": self.web_search,
            "financial_data": self.financial_data,
            "web_scraper": self.web_scraper,
            "calculator": self.calculator,
        }
        
        # Register default resources
        self._register_default_resources()
        
        # Register default prompts
        self._register_default_prompts()
        
        log.info(f"Initialized full MCP server with {len(self.tools)} tools")
    
    def _register_default_resources(self):
        """Register default MCP resources"""
        # Financial data resources
        resources = [
            MCPResource(
                uri="resource://financial/markets",
                name="Financial Markets",
                description="Access to global financial markets data",
                mimeType="application/json"
            ),
            MCPResource(
                uri="resource://financial/sectors",
                name="Sector Information",
                description="IT and Pharmaceutical sector information",
                mimeType="application/json"
            ),
        ]
        
        for resource in resources:
            self.mcp_server.register_resource(resource)
    
    def _register_default_prompts(self):
        """Register default MCP prompts"""
        prompts = [
            MCPPrompt(
                name="financial_analysis",
                description="Generate financial analysis prompt",
                arguments=[
                    {
                        "name": "company",
                        "description": "Company name to analyze",
                        "required": True
                    },
                    {
                        "name": "sector",
                        "description": "Sector (IT or Pharma)",
                        "required": True
                    }
                ]
            ),
            MCPPrompt(
                name="comparative_analysis",
                description="Generate comparative analysis prompt",
                arguments=[
                    {
                        "name": "companies",
                        "description": "List of companies to compare",
                        "required": True
                    }
                ]
            ),
        ]
        
        for prompt in prompts:
            self.mcp_server.register_prompt(prompt)
    
    def get_mcp_server(self) -> MCPServer:
        """
        Get the underlying MCP server instance
        
        Returns:
            MCPServer instance for full MCP protocol access
        """
        return self.mcp_server
    
    async def handle_mcp_request(self, json_request: str) -> Optional[str]:
        """
        Handle full MCP JSON-RPC request
        
        Args:
            json_request: JSON-RPC request string
            
        Returns:
            JSON-RPC response string, or None for notifications
        """
        return await self.mcp_server.handle_json(json_request)
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all tool schemas in MCP format
        
        Returns:
            List of MCP tool schema dictionaries
        """
        return self.mcp_server._get_tool_schemas()
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name (backward-compatible interface)
        
        This method provides backward compatibility while using the full MCP
        protocol internally.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        tool = self.tools[tool_name]
        log.info(f"Executing tool: {tool_name} with params: {kwargs}")
        
        try:
            # Use MCP server's tool execution for consistency
            result = await self.mcp_server._handle_tools_call({
                "name": tool_name,
                "arguments": kwargs
            })
            
            # Extract text content from MCP response format
            if "content" in result and result["content"]:
                content = result["content"][0].get("text", "")
                try:
                    # Try to parse as JSON to return structured data
                    return json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    # Return as string if not JSON
                    return {"result": content}
            
            return result
        except Exception as e:
            log.error(f"Tool execution failed for {tool_name}: {e}")
            return {
                "error": str(e),
                "tool": tool_name
            }
    
    def get_tool(self, tool_name: str):
        """Get tool instance by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names"""
        return list(self.tools.keys())
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Get all registered resources"""
        return [
            resource.to_dict()
            for resource in self.mcp_server.resources.values()
        ]
    
    def get_prompts(self) -> List[Dict[str, Any]]:
        """Get all registered prompts"""
        return [
            prompt.to_dict()
            for prompt in self.mcp_server.prompts.values()
        ]


# Global instance
mcp_tools = MCPTools()