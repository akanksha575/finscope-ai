"""
MCP Server Implementation

Full Model Context Protocol server with JSON-RPC 2.0 protocol support.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from utils.logger import log
from tools.mcp_protocol import (
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPResource,
    MCPPrompt,
    MCPErrorCode,
    MCPInitializeParams,
    MCPInitializeResult,
    MCPSchema
)
from tools.base_tool import BaseTool


class MCPServer:
    """Full MCP Server implementation with JSON-RPC 2.0 protocol"""
    
    PROTOCOL_VERSION = "2024-11-05"
    
    def __init__(self, name: str = "FinScope MCP Server", version: str = "1.0.0"):
        """
        Initialize MCP Server
        
        Args:
            name: Server name
            version: Server version
        """
        self.name = name
        self.version = version
        self.tools: Dict[str, BaseTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.initialized = False
        self.client_capabilities: Dict[str, Any] = {}
        self.client_info: Dict[str, str] = {}
        
        log.info(f"Initialized MCP Server: {name} v{version}")
    
    def register_tool(self, tool: BaseTool):
        """Register a tool with the MCP server"""
        self.tools[tool.name] = tool
        log.info(f"Registered MCP tool: {tool.name}")
    
    def register_resource(self, resource: MCPResource):
        """Register a resource with the MCP server"""
        self.resources[resource.uri] = resource
        log.info(f"Registered MCP resource: {resource.uri}")
    
    def register_prompt(self, prompt: MCPPrompt):
        """Register a prompt template with the MCP server"""
        self.prompts[prompt.name] = prompt
        log.info(f"Registered MCP prompt: {prompt.name}")
    
    def _convert_schema_to_mcp(self, schema: Dict[str, Any]) -> MCPSchema:
        """Convert tool schema to MCP schema format"""
        def _convert(value: Any) -> Any:
            if isinstance(value, dict):
                if "type" in value:
                    return MCPSchema(
                        type=value["type"],
                        description=value.get("description"),
                        enum=value.get("enum"),
                        default=value.get("default"),
                        properties={
                            k: _convert(v) for k, v in value.get("properties", {}).items()
                        } if "properties" in value else None,
                        items=_convert(value.get("items")) if "items" in value else None,
                        required=value.get("required"),
                        minimum=value.get("minimum"),
                        maximum=value.get("maximum")
                    )
                else:
                    return {k: _convert(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_convert(item) for item in value]
            else:
                return value
        
        params = schema.get("parameters", {})
        return MCPSchema(
            type="object",
            properties={
                k: _convert(v) for k, v in params.get("properties", {}).items()
            } if "properties" in params else {},
            required=params.get("required", [])
        )
    
    def _get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in MCP format"""
        mcp_tools = []
        for tool_name, tool in self.tools.items():
            schema = tool.get_schema()
            mcp_schema = self._convert_schema_to_mcp(schema)
            
            mcp_tool = MCPTool(
                name=tool_name,
                description=schema.get("description", tool.description),
                inputSchema=mcp_schema
            )
            mcp_tools.append(mcp_tool.to_dict())
        
        return mcp_tools
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        init_params = MCPInitializeParams(
            protocolVersion=params.get("protocolVersion", self.PROTOCOL_VERSION),
            capabilities=params.get("capabilities", {}),
            clientInfo=params.get("clientInfo", {})
        )
        
        self.client_capabilities = init_params.capabilities
        self.client_info = init_params.clientInfo
        self.initialized = True
        
        result = MCPInitializeResult(
            protocolVersion=self.PROTOCOL_VERSION,
            capabilities={
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            },
            serverInfo={
                "name": self.name,
                "version": self.version
            }
        )
        
        log.info(f"MCP Server initialized with protocol version {self.PROTOCOL_VERSION}")
        return result.to_dict()
    
    async def _handle_tools_list(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {"tools": self._get_tool_schemas()}
    
    async def _handle_tools_call(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # Validate input
        is_valid, error_msg = tool.validate_input(**arguments)
        if not is_valid:
            raise ValueError(f"Invalid arguments: {error_msg}")
        
        # Execute tool
        try:
            result = await tool.execute(**arguments)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, default=str)
                    }
                ],
                "isError": False
            }
        except Exception as e:
            log.error(f"Tool execution error for {tool_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_resources_list(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle resources/list request"""
        return {
            "resources": [resource.to_dict() for resource in self.resources.values()]
        }
    
    async def _handle_resources_read(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Resource URI is required")
        
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")
        
        resource = self.resources[uri]
        
        # For now, return resource metadata
        # In a full implementation, this would fetch actual resource content
        return {
            "contents": [
                {
                    "uri": resource.uri,
                    "mimeType": resource.mimeType or "text/plain",
                    "text": resource.description or ""
                }
            ]
        }
    
    async def _handle_prompts_list(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle prompts/list request"""
        return {
            "prompts": [prompt.to_dict() for prompt in self.prompts.values()]
        }
    
    async def _handle_prompts_get(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle prompts/get request"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise ValueError("Prompt name is required")
        
        if name not in self.prompts:
            raise ValueError(f"Prompt not found: {name}")
        
        prompt = self.prompts[name]
        
        # Return prompt with arguments substituted
        # In a full implementation, this would template the arguments
        return {
            "name": prompt.name,
            "description": prompt.description,
            "arguments": prompt.arguments or [],
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt.description or ""
                    }
                }
            ]
        }
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        Handle MCP JSON-RPC request
        
        Args:
            request: MCP request object
            
        Returns:
            MCP response object
        """
        # Validate JSON-RPC version
        if request.jsonrpc != "2.0":
            return MCPResponse.error_response(
                request.id,
                MCPErrorCode.INVALID_REQUEST.value,
                "Invalid JSON-RPC version. Must be 2.0"
            )
        
        # Handle initialize separately (can be called before initialized)
        if request.method == "initialize":
            try:
                result = await self._handle_initialize(request.params or {})
                return MCPResponse.success(request.id, result)
            except Exception as e:
                log.error(f"Initialize error: {e}")
                return MCPResponse.error_response(
                    request.id,
                    MCPErrorCode.INTERNAL_ERROR.value,
                    f"Initialize failed: {str(e)}"
                )
        
        # Check if initialized (except for initialize)
        if not self.initialized:
            return MCPResponse.error_response(
                request.id,
                MCPErrorCode.INVALID_REQUEST.value,
                "Server not initialized. Call initialize first."
            )
        
        # Handle initialized notification
        if request.method == "initialized":
            # Notification - no response needed
            return None
        
        # Route to appropriate handler
        try:
            if request.method == "tools/list":
                result = await self._handle_tools_list(request.params)
                return MCPResponse.success(request.id, result)
            
            elif request.method == "tools/call":
                result = await self._handle_tools_call(request.params or {})
                return MCPResponse.success(request.id, result)
            
            elif request.method == "resources/list":
                result = await self._handle_resources_list(request.params)
                return MCPResponse.success(request.id, result)
            
            elif request.method == "resources/read":
                result = await self._handle_resources_read(request.params or {})
                return MCPResponse.success(request.id, result)
            
            elif request.method == "prompts/list":
                result = await self._handle_prompts_list(request.params)
                return MCPResponse.success(request.id, result)
            
            elif request.method == "prompts/get":
                result = await self._handle_prompts_get(request.params or {})
                return MCPResponse.success(request.id, result)
            
            else:
                return MCPResponse.error_response(
                    request.id,
                    MCPErrorCode.METHOD_NOT_FOUND.value,
                    f"Method not found: {request.method}"
                )
        
        except ValueError as e:
            return MCPResponse.error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS.value,
                str(e)
            )
        
        except Exception as e:
            log.error(f"Error handling request {request.method}: {e}")
            return MCPResponse.error_response(
                request.id,
                MCPErrorCode.INTERNAL_ERROR.value,
                f"Internal error: {str(e)}"
            )
    
    async def handle_json(self, json_str: str) -> Optional[str]:
        """
        Handle JSON-RPC request string and return response JSON string
        
        Args:
            json_str: JSON-RPC request as string
            
        Returns:
            JSON-RPC response as string, or None for notifications
        """
        try:
            data = json.loads(json_str)
            request = MCPRequest.from_dict(data)
            response = await self.handle_request(request)
            
            if response is None:
                return None  # Notification
            
            return json.dumps(response.to_dict(), default=str)
        
        except json.JSONDecodeError as e:
            error_response = MCPResponse.error_response(
                None,
                MCPErrorCode.PARSE_ERROR.value,
                f"Parse error: {str(e)}"
            )
            return json.dumps(error_response.to_dict())
        
        except Exception as e:
            log.error(f"Error parsing JSON: {e}")
            error_response = MCPResponse.error_response(
                None,
                MCPErrorCode.INTERNAL_ERROR.value,
                f"Internal error: {str(e)}"
            )
            return json.dumps(error_response.to_dict())
