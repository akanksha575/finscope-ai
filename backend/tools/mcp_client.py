"""
MCP Client Implementation

Client for interacting with MCP servers using JSON-RPC 2.0 protocol.
"""

import json
import uuid
from typing import Dict, Any, Optional, List, Callable, Awaitable
from utils.logger import log
from tools.mcp_protocol import MCPRequest, MCPResponse


class MCPClient:
    """MCP Client for communicating with MCP servers"""
    
    def __init__(self, server: 'MCPServer'):
        """
        Initialize MCP client
        
        Args:
            server: MCP server instance to connect to
        """
        self.server = server
        self.initialized = False
        self.client_info = {
            "name": "FinScope Client",
            "version": "1.0.0"
        }
        log.info("Initialized MCP Client")
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize connection with MCP server
        
        Returns:
            Server capabilities and info
        """
        request = MCPRequest(
            id=str(uuid.uuid4()),
            method="initialize",
            params={
                "protocolVersion": self.server.PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "prompts": {}
                },
                "clientInfo": self.client_info
            }
        )
        
        response_dict = await self.server.handle_request(request)
        response = MCPResponse(**response_dict.to_dict() if hasattr(response_dict, 'to_dict') else response_dict)
        
        if response.error:
            raise Exception(f"Initialize failed: {response.error}")
        
        self.initialized = True
        
        # Send initialized notification
        await self._send_notification("initialized", {})
        
        return response.result
    
    async def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Send notification (no response expected)"""
        request = MCPRequest(
            method=method,
            params=params or {}
        )
        await self.server.handle_request(request)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            method="tools/list"
        )
        
        response = await self.server.handle_request(request)
        if response.error:
            raise Exception(f"List tools failed: {response.error}")
        
        return response.result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        request = MCPRequest(
            id=str(uuid.uuid4()),
            method="tools/call",
            params={
                "name": name,
                "arguments": arguments
            }
        )
        
        response = await self.server.handle_request(request)
        if response.error:
            raise Exception(f"Tool call failed: {response.error}")
        
        return response.result
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            method="resources/list"
        )
        
        response = await self.server.handle_request(request)
        if response.error:
            raise Exception(f"List resources failed: {response.error}")
        
        return response.result.get("resources", [])
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a resource
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        request = MCPRequest(
            id=str(uuid.uuid4()),
            method="resources/read",
            params={"uri": uri}
        )
        
        response = await self.server.handle_request(request)
        if response.error:
            raise Exception(f"Read resource failed: {response.error}")
        
        return response.result
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompts"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            method="prompts/list"
        )
        
        response = await self.server.handle_request(request)
        if response.error:
            raise Exception(f"List prompts failed: {response.error}")
        
        return response.result.get("prompts", [])
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a prompt template
        
        Args:
            name: Prompt name
            arguments: Optional prompt arguments
            
        Returns:
            Prompt template
        """
        request = MCPRequest(
            id=str(uuid.uuid4()),
            method="prompts/get",
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )
        
        response = await self.server.handle_request(request)
        if response.error:
            raise Exception(f"Get prompt failed: {response.error}")
        
        return response.result
