# Agent Tools

This directory contains tools that agents can use to interact with external systems and perform specific tasks.

## Available Tools

### 1. ExternalApiTool

**Purpose**: Make HTTP requests to external APIs (renamed from CompanyAPITool for broader use)

**Usage**:
```python
from src.tools import ExternalApiTool

# Initialize with your API configuration
api_tool = ExternalApiTool(
    base_url="https://api.yourcompany.com",
    default_headers={"Authorization": "Bearer YOUR_API_TOKEN"}
)

# Use in agent conversations
result = await api_tool.execute(
    method="GET",
    endpoint="/users/123",
    params={"include": "profile"}
)
```

**Parameters**:
- `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
- `endpoint`: API endpoint path
- `params`: Query parameters (optional)
- `data`: Request body data (optional)
- `headers`: Additional HTTP headers (optional)

### 2. UserManagementTool

**Purpose**: Specialized tool for user management operations (extends ExternalApiTool)

**Usage**:
```python
from src.tools import UserManagementTool

user_tool = UserManagementTool(
    base_url="https://api.yourcompany.com",
    default_headers={"Authorization": "Bearer YOUR_API_TOKEN"}
)

# Get user information
result = await user_tool.execute(
    action="get_user",
    user_id="123"
)

# Create new user
result = await user_tool.execute(
    action="create_user",
    user_data={"name": "John Doe", "email": "john@example.com"}
)
```

**Actions**:
- `get_user`: Retrieve user by ID
- `list_users`: List users with optional filters
- `create_user`: Create new user
- `update_user`: Update existing user

### 3. MCPClientTool

**Purpose**: Connect to and interact with Model Context Protocol (MCP) servers

**Usage**:
```python
from src.tools import MCPClientTool

# Initialize MCP client for a specific server
mcp_client = MCPClientTool(
    server_command=["python", "path/to/mcp_server.py"],
    server_name="my-mcp-server"
)

# Connect to server
await mcp_client.execute(action="connect")

# List available tools on the server
tools_result = await mcp_client.execute(action="list_tools")

# Call a tool on the server
result = await mcp_client.execute(
    action="call_tool",
    tool_name="weather_lookup",
    tool_arguments={"location": "San Francisco"}
)
```

**Actions**:
- `connect`: Connect to the MCP server
- `list_tools`: List available tools on the server
- `list_resources`: List available resources on the server
- `call_tool`: Execute a tool on the server
- `read_resource`: Read a resource from the server
- `disconnect`: Disconnect from the server

### 4. MCPServerManager

**Purpose**: Manage multiple MCP server connections and route requests

**Usage**:
```python
from src.tools import MCPServerManager

manager = MCPServerManager()

# Add MCP servers
await manager.execute(
    action="add_server",
    server_name="weather-server",
    server_command=["python", "weather_mcp_server.py"]
)

await manager.execute(
    action="add_server", 
    server_name="database-server",
    server_command=["node", "database_mcp_server.js"]
)

# Route requests to specific servers
result = await manager.execute(
    action="route_request",
    server_name="weather-server",
    server_action="call_tool",
    server_params={
        "tool_name": "get_weather",
        "tool_arguments": {"city": "New York"}
    }
)
```

**Actions**:
- `add_server`: Add a new MCP server
- `remove_server`: Remove an MCP server
- `list_servers`: List all managed servers
- `route_request`: Route a request to a specific server

## Agent Integration

Agents can choose the appropriate tool based on their needs:

1. **Direct API Access**: Use `ExternalApiTool` for direct HTTP requests to your company APIs
2. **User Operations**: Use `UserManagementTool` for user-related operations
3. **MCP Integration**: Use `MCPClientTool` or `MCPServerManager` to connect to standardized MCP servers

## MCP Server Examples

### Simple Weather MCP Server

```python
# weather_mcp_server.py
from mcp.server import Server
from mcp.types import Tool

server = Server("weather-server")

@server.tool("get_weather")
async def get_weather(location: str) -> str:
    # Your weather API logic here
    return f"Weather in {location}: Sunny, 25°C"

if __name__ == "__main__":
    server.run()
```

### Database MCP Server

```javascript
// database_mcp_server.js
const { Server } = require('mcp');

const server = new Server('database-server');

server.addTool('query_users', async (params) => {
    // Your database query logic here
    return { users: [...] };
});

server.run();
```

## Benefits of the Tool Architecture

1. **Flexibility**: Agents can choose between direct API calls or standardized MCP protocol
2. **Standardization**: MCP provides a consistent interface across different tools and servers
3. **Scalability**: Easy to add new tools and servers without changing agent code
4. **Modularity**: Each tool is self-contained and can be used independently
5. **Error Handling**: Consistent error handling and reporting across all tools

## Configuration

Tools are automatically registered in the tool registry and available to all agents. You can configure default tools in:

- `src/api/routes/agents.py` (for API endpoints)
- Your agent initialization code

The SupervisorAgent from agent-squad framework will automatically have access to all registered tools and can use them as needed for complex tasks. 