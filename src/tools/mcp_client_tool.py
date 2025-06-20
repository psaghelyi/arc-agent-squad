"""
MCP Client Tool for connecting to Model Context Protocol servers.

This tool allows agents to connect to MCP servers and use their tools
and resources through the standardized MCP protocol.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from .base_tool import BaseTool, ToolResult, ToolParameter

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class MCPClientTool(BaseTool):
    """Tool for connecting to and interacting with MCP servers."""
    
    def __init__(self, 
                 server_command: List[str],
                 server_name: str = "mcp-server",
                 timeout: int = 30):
        """
        Initialize the MCP Client Tool.
        
        Args:
            server_command: Command to start the MCP server (e.g., ["python", "server.py"])
            server_name: Name identifier for the server
            timeout: Connection timeout in seconds
        """
        super().__init__()
        self.server_command = server_command
        self.server_name = server_name
        self.timeout = timeout
        self._session: Optional[ClientSession] = None
        self._available_tools: List[Dict[str, Any]] = []
        self._available_resources: List[Dict[str, Any]] = []
    
    @property
    def name(self) -> str:
        return f"mcp_client_{self.server_name}"
    
    @property
    def description(self) -> str:
        return f"Connect to and interact with MCP server '{self.server_name}' to access its tools and resources"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform with the MCP server",
                enum=["connect", "list_tools", "list_resources", "call_tool", "read_resource", "disconnect"],
                required=True
            ),
            ToolParameter(
                name="tool_name",
                type="string",
                description="Name of the tool to call (required for call_tool action)",
                required=False
            ),
            ToolParameter(
                name="tool_arguments",
                type="object",
                description="Arguments to pass to the tool (required for call_tool action)",
                required=False
            ),
            ToolParameter(
                name="resource_uri",
                type="string",
                description="URI of the resource to read (required for read_resource action)",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute MCP client operations."""
        if not MCP_AVAILABLE:
            return ToolResult(
                success=False,
                error="MCP client library not available. Install with: pip install mcp"
            )
        
        action = kwargs.get("action")
        
        try:
            if action == "connect":
                return await self._connect()
            elif action == "list_tools":
                return await self._list_tools()
            elif action == "list_resources":
                return await self._list_resources()
            elif action == "call_tool":
                tool_name = kwargs.get("tool_name")
                tool_arguments = kwargs.get("tool_arguments", {})
                return await self._call_tool(tool_name, tool_arguments)
            elif action == "read_resource":
                resource_uri = kwargs.get("resource_uri")
                return await self._read_resource(resource_uri)
            elif action == "disconnect":
                return await self._disconnect()
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"MCP client error: {str(e)}",
                metadata={"action": action, "server": self.server_name}
            )
    
    async def _connect(self) -> ToolResult:
        """Connect to the MCP server."""
        try:
            if self._session:
                return ToolResult(
                    success=True,
                    data={"message": f"Already connected to {self.server_name}"},
                    metadata={"server": self.server_name}
                )
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else []
            )
            
            # Connect to server
            async with stdio_client(server_params) as (read, write):
                self._session = ClientSession(read, write)
                
                # Initialize the session
                await self._session.initialize()
                
                # Get available tools and resources
                tools_result = await self._session.list_tools()
                resources_result = await self._session.list_resources()
                
                self._available_tools = tools_result.tools if hasattr(tools_result, 'tools') else []
                self._available_resources = resources_result.resources if hasattr(resources_result, 'resources') else []
                
                return ToolResult(
                    success=True,
                    data={
                        "message": f"Successfully connected to {self.server_name}",
                        "tools_count": len(self._available_tools),
                        "resources_count": len(self._available_resources),
                        "tools": [tool.name for tool in self._available_tools] if self._available_tools else [],
                        "resources": [res.uri for res in self._available_resources] if self._available_resources else []
                    },
                    metadata={"server": self.server_name}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to connect to MCP server: {str(e)}",
                metadata={"server": self.server_name, "command": self.server_command}
            )
    
    async def _list_tools(self) -> ToolResult:
        """List available tools from the MCP server."""
        if not self._session:
            return ToolResult(
                success=False,
                error="Not connected to MCP server. Use 'connect' action first."
            )
        
        try:
            result = await self._session.list_tools()
            tools = result.tools if hasattr(result, 'tools') else []
            
            tools_info = []
            for tool in tools:
                tool_info = {
                    "name": tool.name,
                    "description": getattr(tool, 'description', ''),
                    "schema": getattr(tool, 'inputSchema', {})
                }
                tools_info.append(tool_info)
            
            return ToolResult(
                success=True,
                data={
                    "tools": tools_info,
                    "count": len(tools_info)
                },
                metadata={"server": self.server_name}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list tools: {str(e)}",
                metadata={"server": self.server_name}
            )
    
    async def _list_resources(self) -> ToolResult:
        """List available resources from the MCP server."""
        if not self._session:
            return ToolResult(
                success=False,
                error="Not connected to MCP server. Use 'connect' action first."
            )
        
        try:
            result = await self._session.list_resources()
            resources = result.resources if hasattr(result, 'resources') else []
            
            resources_info = []
            for resource in resources:
                resource_info = {
                    "uri": resource.uri,
                    "name": getattr(resource, 'name', ''),
                    "description": getattr(resource, 'description', ''),
                    "mimeType": getattr(resource, 'mimeType', '')
                }
                resources_info.append(resource_info)
            
            return ToolResult(
                success=True,
                data={
                    "resources": resources_info,
                    "count": len(resources_info)
                },
                metadata={"server": self.server_name}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list resources: {str(e)}",
                metadata={"server": self.server_name}
            )
    
    async def _call_tool(self, tool_name: str, tool_arguments: Dict[str, Any]) -> ToolResult:
        """Call a tool on the MCP server."""
        if not self._session:
            return ToolResult(
                success=False,
                error="Not connected to MCP server. Use 'connect' action first."
            )
        
        if not tool_name:
            return ToolResult(
                success=False,
                error="tool_name is required for call_tool action"
            )
        
        try:
            result = await self._session.call_tool(tool_name, tool_arguments)
            
            return ToolResult(
                success=True,
                data={
                    "tool_name": tool_name,
                    "arguments": tool_arguments,
                    "result": result.content if hasattr(result, 'content') else str(result),
                    "is_error": getattr(result, 'isError', False)
                },
                metadata={
                    "server": self.server_name,
                    "tool": tool_name
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to call tool '{tool_name}': {str(e)}",
                metadata={
                    "server": self.server_name,
                    "tool": tool_name,
                    "arguments": tool_arguments
                }
            )
    
    async def _read_resource(self, resource_uri: str) -> ToolResult:
        """Read a resource from the MCP server."""
        if not self._session:
            return ToolResult(
                success=False,
                error="Not connected to MCP server. Use 'connect' action first."
            )
        
        if not resource_uri:
            return ToolResult(
                success=False,
                error="resource_uri is required for read_resource action"
            )
        
        try:
            result = await self._session.read_resource(resource_uri)
            
            return ToolResult(
                success=True,
                data={
                    "uri": resource_uri,
                    "content": result.contents if hasattr(result, 'contents') else str(result),
                    "mimeType": getattr(result, 'mimeType', '')
                },
                metadata={
                    "server": self.server_name,
                    "resource_uri": resource_uri
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to read resource '{resource_uri}': {str(e)}",
                metadata={
                    "server": self.server_name,
                    "resource_uri": resource_uri
                }
            )
    
    async def _disconnect(self) -> ToolResult:
        """Disconnect from the MCP server."""
        try:
            if self._session:
                # Close the session if it has a close method
                if hasattr(self._session, 'close'):
                    await self._session.close()
                self._session = None
                self._available_tools = []
                self._available_resources = []
                
                return ToolResult(
                    success=True,
                    data={"message": f"Disconnected from {self.server_name}"},
                    metadata={"server": self.server_name}
                )
            else:
                return ToolResult(
                    success=True,
                    data={"message": f"Already disconnected from {self.server_name}"},
                    metadata={"server": self.server_name}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error disconnecting from MCP server: {str(e)}",
                metadata={"server": self.server_name}
            )


class MCPServerManager(BaseTool):
    """Tool for managing multiple MCP server connections."""
    
    def __init__(self):
        """Initialize the MCP Server Manager."""
        super().__init__()
        self.servers: Dict[str, MCPClientTool] = {}
    
    @property
    def name(self) -> str:
        return "mcp_server_manager"
    
    @property
    def description(self) -> str:
        return "Manage multiple MCP server connections and route requests to appropriate servers"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Management action to perform",
                enum=["add_server", "remove_server", "list_servers", "route_request"],
                required=True
            ),
            ToolParameter(
                name="server_name",
                type="string",
                description="Name of the server",
                required=False
            ),
            ToolParameter(
                name="server_command",
                type="array",
                description="Command to start the MCP server (for add_server)",
                required=False
            ),
            ToolParameter(
                name="server_action",
                type="string",
                description="Action to route to the server (for route_request)",
                required=False
            ),
            ToolParameter(
                name="server_params",
                type="object",
                description="Parameters to pass to the server action (for route_request)",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute MCP server management operations."""
        action = kwargs.get("action")
        
        try:
            if action == "add_server":
                server_name = kwargs.get("server_name")
                server_command = kwargs.get("server_command", [])
                return await self._add_server(server_name, server_command)
            
            elif action == "remove_server":
                server_name = kwargs.get("server_name")
                return await self._remove_server(server_name)
            
            elif action == "list_servers":
                return await self._list_servers()
            
            elif action == "route_request":
                server_name = kwargs.get("server_name")
                server_action = kwargs.get("server_action")
                server_params = kwargs.get("server_params", {})
                return await self._route_request(server_name, server_action, server_params)
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"MCP server manager error: {str(e)}",
                metadata={"action": action}
            )
    
    async def _add_server(self, server_name: str, server_command: List[str]) -> ToolResult:
        """Add a new MCP server."""
        if not server_name:
            return ToolResult(success=False, error="server_name is required")
        
        if not server_command:
            return ToolResult(success=False, error="server_command is required")
        
        if server_name in self.servers:
            return ToolResult(
                success=False,
                error=f"Server '{server_name}' already exists"
            )
        
        self.servers[server_name] = MCPClientTool(
            server_command=server_command,
            server_name=server_name
        )
        
        return ToolResult(
            success=True,
            data={
                "message": f"Added MCP server '{server_name}'",
                "server_name": server_name,
                "command": server_command
            }
        )
    
    async def _remove_server(self, server_name: str) -> ToolResult:
        """Remove an MCP server."""
        if not server_name:
            return ToolResult(success=False, error="server_name is required")
        
        if server_name not in self.servers:
            return ToolResult(
                success=False,
                error=f"Server '{server_name}' not found"
            )
        
        # Disconnect the server first
        await self.servers[server_name].execute(action="disconnect")
        del self.servers[server_name]
        
        return ToolResult(
            success=True,
            data={"message": f"Removed MCP server '{server_name}'"}
        )
    
    async def _list_servers(self) -> ToolResult:
        """List all managed MCP servers."""
        servers_info = []
        for name, server in self.servers.items():
            servers_info.append({
                "name": name,
                "command": server.server_command,
                "connected": server._session is not None
            })
        
        return ToolResult(
            success=True,
            data={
                "servers": servers_info,
                "count": len(servers_info)
            }
        )
    
    async def _route_request(self, server_name: str, server_action: str, server_params: Dict[str, Any]) -> ToolResult:
        """Route a request to a specific MCP server."""
        if not server_name:
            return ToolResult(success=False, error="server_name is required")
        
        if not server_action:
            return ToolResult(success=False, error="server_action is required")
        
        if server_name not in self.servers:
            return ToolResult(
                success=False,
                error=f"Server '{server_name}' not found"
            )
        
        # Route the request to the specific server
        return await self.servers[server_name].execute(
            action=server_action,
            **server_params
        ) 