# Model Context Protocol (MCP) Implementation

Full MCP specification implementation following JSON-RPC 2.0 protocol for standardized AI assistant tool integration.

## Overview

This implementation provides a complete MCP server following the [Model Context Protocol specification](https://modelcontextprotocol.io/). It includes:

- ✅ Full JSON-RPC 2.0 protocol support
- ✅ Tool discovery and execution (`tools/list`, `tools/call`)
- ✅ Resource management (`resources/list`, `resources/read`)
- ✅ Prompt templates (`prompts/list`, `prompts/get`)
- ✅ Proper error handling with MCP error codes
- ✅ Backward compatibility with existing code

## Architecture

```
mcp_protocol.py    - MCP protocol definitions and data structures
mcp_server.py      - Full MCP server with JSON-RPC handler
mcp_client.py      - MCP client for server communication
mcp_tools.py       - Main interface (backward compatible + full MCP)
mcp_example.py     - Usage examples
```

## Quick Start

### Basic Usage (Backward Compatible)

```python
from tools.mcp_tools import mcp_tools

# Simple tool execution (works as before)
result = await mcp_tools.execute_tool(
    "web_search",
    query="Infosys financial performance",
    max_results=5
)
```

### Full MCP Protocol Usage

```python
from tools.mcp_tools import mcp_tools
from tools.mcp_client import MCPClient

# Get MCP server
server = mcp_tools.get_mcp_server()
client = MCPClient(server)

# Initialize connection
await client.initialize()

# List available tools
tools = await client.list_tools()
print([t['name'] for t in tools])

# Call a tool
result = await client.call_tool(
    "financial_data",
    arguments={"symbol": "INFY.NS", "period": "1y"}
)

# Access resources
resources = await client.list_resources()
prompts = await client.list_prompts()
```

### Direct JSON-RPC

```python
import json
from tools.mcp_tools import mcp_tools

server = mcp_tools.get_mcp_server()

# Create JSON-RPC request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "web_search",
        "arguments": {
            "query": "TCS revenue 2025",
            "max_results": 3
        }
    }
}

# Handle request
response_json = await server.handle_json(json.dumps(request))
response = json.loads(response_json)
```

## MCP Methods

### Initialize

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {"subscribe": true},
      "prompts": {}
    },
    "clientInfo": {
      "name": "Client Name",
      "version": "1.0.0"
    }
  }
}
```

### Tools

#### `tools/list`
List all available tools.

#### `tools/call`
Execute a tool with arguments.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "web_search",
    "arguments": {
      "query": "search query",
      "max_results": 5
    }
  }
}
```

### Resources

#### `resources/list`
List all available resources.

#### `resources/read`
Read a resource by URI.

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/read",
  "params": {
    "uri": "resource://financial/markets"
  }
}
```

### Prompts

#### `prompts/list`
List all available prompt templates.

#### `prompts/get`
Get a prompt template with optional arguments.

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "prompts/get",
  "params": {
    "name": "financial_analysis",
    "arguments": {
      "company": "Infosys",
      "sector": "IT"
    }
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| -32700 | Parse error |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32000 to -32099 | Server error range |

## Registering Custom Tools

```python
from tools.base_tool import BaseTool
from tools.mcp_tools import mcp_tools

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="My custom tool"
        )
    
    async def execute(self, **kwargs):
        # Tool implementation
        return {"result": "success"}
    
    def get_schema(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        }

# Register tool
tool = MyCustomTool()
server = mcp_tools.get_mcp_server()
server.register_tool(tool)
```

## Registering Resources

```python
from tools.mcp_protocol import MCPResource
from tools.mcp_tools import mcp_tools

resource = MCPResource(
    uri="resource://my/resource",
    name="My Resource",
    description="Resource description",
    mimeType="application/json"
)

server = mcp_tools.get_mcp_server()
server.register_resource(resource)
```

## Registering Prompts

```python
from tools.mcp_protocol import MCPPrompt
from tools.mcp_tools import mcp_tools

prompt = MCPPrompt(
    name="my_prompt",
    description="Prompt description",
    arguments=[
        {
            "name": "arg1",
            "description": "Argument description",
            "required": True
        }
    ]
)

server = mcp_tools.get_mcp_server()
server.register_prompt(prompt)
```

## Available Tools

1. **web_search** - Tavily web search
2. **financial_data** - Yahoo Finance data via yfinance
3. **web_scraper** - Web content scraping
4. **calculator** - Financial calculations

## Resources

- `resource://financial/markets` - Financial markets data
- `resource://financial/sectors` - Sector information

## Prompts

- `financial_analysis` - Financial analysis template
- `comparative_analysis` - Comparative analysis template

## Protocol Version

Current protocol version: `2024-11-05`

## Backward Compatibility

The implementation maintains full backward compatibility with existing code using `mcp_tools.execute_tool()`. Existing code continues to work without changes.

## Testing

Run the example file to test the implementation:

```bash
python backend/tools/mcp_example.py
```

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
