"""
MCP Usage Examples

Examples demonstrating how to use the full MCP implementation.
"""

import asyncio
import json
from tools.mcp_tools import mcp_tools
from tools.mcp_client import MCPClient
from tools.mcp_protocol import MCPRequest, MCPResponse


async def example_basic_usage():
    """Example: Basic tool execution using backward-compatible interface"""
    print("=== Basic Tool Execution ===")
    
    # Use the simplified interface (backward compatible)
    result = await mcp_tools.execute_tool(
        "web_search",
        query="Infosys financial performance 2025",
        max_results=3
    )
    print(f"Search result: {result}")
    print()


async def example_mcp_protocol():
    """Example: Using full MCP protocol via JSON-RPC"""
    print("=== Full MCP Protocol ===")
    
    server = mcp_tools.get_mcp_server()
    client = MCPClient(server)
    
    # Initialize connection
    init_result = await client.initialize()
    print(f"Initialized: {init_result['serverInfo']}")
    
    # List all tools
    tools = await client.list_tools()
    print(f"Available tools: {[t['name'] for t in tools]}")
    
    # Call a tool using MCP protocol
    tool_result = await client.call_tool(
        "financial_data",
        arguments={
            "symbol": "INFY.NS",
            "period": "1y"
        }
    )
    print(f"Tool result: {tool_result}")
    
    # List resources
    resources = await client.list_resources()
    print(f"Available resources: {[r['name'] for r in resources]}")
    
    # List prompts
    prompts = await client.list_prompts()
    print(f"Available prompts: {[p['name'] for p in prompts]}")
    print()


async def example_json_rpc_direct():
    """Example: Direct JSON-RPC request/response"""
    print("=== Direct JSON-RPC ===")
    
    server = mcp_tools.get_mcp_server()
    
    # Create JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    # Handle request
    response_json = await server.handle_json(json.dumps(request))
    response = json.loads(response_json)
    
    print(f"Response: {response}")
    print()


async def example_custom_tool_registration():
    """Example: Registering custom tools"""
    print("=== Custom Tool Registration ===")
    
    from tools.base_tool import BaseTool
    
    class CustomTool(BaseTool):
        def __init__(self):
            super().__init__(
                name="custom_calculator",
                description="Custom calculation tool"
            )
        
        async def execute(self, operation: str, a: float, b: float) -> dict:
            if operation == "add":
                return {"result": a + b}
            elif operation == "multiply":
                return {"result": a * b}
            else:
                return {"error": "Unknown operation"}
        
        def get_schema(self):
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "multiply"],
                            "description": "Operation to perform"
                        },
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["operation", "a", "b"]
                }
            }
    
    # Register custom tool
    custom_tool = CustomTool()
    server = mcp_tools.get_mcp_server()
    server.register_tool(custom_tool)
    
    # Use the custom tool
    result = await mcp_tools.execute_tool(
        "custom_calculator",
        operation="multiply",
        a=5,
        b=7
    )
    print(f"Custom tool result: {result}")
    print()


if __name__ == "__main__":
    print("MCP Implementation Examples\n")
    print("=" * 50)
    
    # Run examples
    asyncio.run(example_basic_usage())
    asyncio.run(example_mcp_protocol())
    asyncio.run(example_json_rpc_direct())
    asyncio.run(example_custom_tool_registration())
