"""
Model Context Protocol (MCP) Implementation

Full MCP specification implementation following the JSON-RPC 2.0 protocol
for standardized AI assistant tool integration.
"""

from typing import Dict, Any, List, Optional, Union, Literal
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import json


class MCPErrorCode(Enum):
    """MCP Error Codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32000
    SERVER_ERROR_END = -32099


class MCPMessageType(str, Enum):
    """MCP Message Types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPSchema:
    """MCP Tool Parameter Schema"""
    type: str
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None
    properties: Optional[Dict[str, 'MCPSchema']] = None
    items: Optional['MCPSchema'] = None
    required: Optional[List[str]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {"type": self.type}
        if self.description:
            result["description"] = self.description
        if self.enum is not None:
            result["enum"] = self.enum
        if self.default is not None:
            result["default"] = self.default
        if self.properties:
            result["properties"] = {
                k: v.to_dict() if isinstance(v, MCPSchema) else v
                for k, v in self.properties.items()
            }
        if self.items:
            result["items"] = self.items.to_dict() if isinstance(self.items, MCPSchema) else self.items
        if self.required:
            result["required"] = self.required
        if self.minimum is not None:
            result["minimum"] = self.minimum
        if self.maximum is not None:
            result["maximum"] = self.maximum
        return result


@dataclass
class MCPTool:
    """MCP Tool Definition"""
    name: str
    description: str
    inputSchema: MCPSchema
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP tool format"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema.to_dict()
        }


@dataclass
class MCPResource:
    """MCP Resource Definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "uri": self.uri,
            "name": self.name
        }
        if self.description:
            result["description"] = self.description
        if self.mimeType:
            result["mimeType"] = self.mimeType
        return result


@dataclass
class MCPPrompt:
    """MCP Prompt Template"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.arguments:
            result["arguments"] = self.arguments
        return result


@dataclass
class MCPRequest:
    """MCP JSON-RPC Request"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPRequest':
        """Create from dictionary"""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.id is not None:
            result["id"] = self.id
        if self.params:
            result["params"] = self.params
        return result


@dataclass
class MCPResponse:
    """MCP JSON-RPC Response"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            result["id"] = self.id
        if self.error:
            result["error"] = self.error
        elif self.result is not None:
            result["result"] = self.result
        return result
    
    @classmethod
    def success(cls, request_id: Optional[Union[str, int]], result: Any) -> 'MCPResponse':
        """Create success response"""
        return cls(jsonrpc="2.0", id=request_id, result=result)
    
    @classmethod
    def error_response(
        cls,
        request_id: Optional[Union[str, int]],
        code: int,
        message: str,
        data: Optional[Any] = None
    ) -> 'MCPResponse':
        """Create error response"""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return cls(jsonrpc="2.0", id=request_id, error=error)


@dataclass
class MCPInitializeParams:
    """MCP Initialize Parameters"""
    protocolVersion: str
    capabilities: Dict[str, Any]
    clientInfo: Dict[str, str]


@dataclass
class MCPInitializeResult:
    """MCP Initialize Result"""
    protocolVersion: str
    capabilities: Dict[str, Any]
    serverInfo: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "protocolVersion": self.protocolVersion,
            "capabilities": self.capabilities,
            "serverInfo": self.serverInfo
        }
