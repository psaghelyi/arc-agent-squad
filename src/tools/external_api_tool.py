"""
External API Tool for integrating with external APIs.

This tool allows agents to make HTTP requests to external APIs with
proper authentication and error handling.
"""

import httpx
from typing import Any, Dict, List, Optional
from .base_tool import BaseTool, ToolResult, ToolParameter


class ExternalApiTool(BaseTool):
    """Tool for making HTTP requests to external APIs."""
    
    def __init__(self, 
                 base_url: str = "",
                 default_headers: Optional[Dict[str, str]] = None,
                 timeout: int = 30):
        """
        Initialize the External API Tool.
        
        Args:
            base_url: Base URL for the external API
            default_headers: Default HTTP headers (e.g., authentication)
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return "external_api_request"
    
    @property
    def description(self) -> str:
        return "Make HTTP requests to external APIs to retrieve or send data"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="method",
                type="string",
                description="HTTP method",
                enum=["GET", "POST", "PUT", "DELETE", "PATCH"],
                default="GET"
            ),
            ToolParameter(
                name="endpoint",
                type="string",
                description="API endpoint path (e.g., /users/123)",
                required=True
            ),
            ToolParameter(
                name="params",
                type="object",
                description="Query parameters",
                required=False
            ),
            ToolParameter(
                name="data",
                type="object",
                description="Request body data (for POST/PUT/PATCH)",
                required=False
            ),
            ToolParameter(
                name="headers",
                type="object",
                description="Additional HTTP headers",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the API request."""
        method = kwargs.get("method", "GET").upper()
        endpoint = kwargs.get("endpoint", "")
        params = kwargs.get("params", {})
        data = kwargs.get("data", {})
        additional_headers = kwargs.get("headers", {})
        
        # Build full URL
        if endpoint.startswith('http'):
            url = endpoint
        else:
            endpoint = endpoint.lstrip('/')
            url = f"{self.base_url}/{endpoint}" if self.base_url else endpoint
        
        # Combine headers
        headers = {**self.default_headers, **additional_headers}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    response = await client.post(url, params=params, json=data, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, params=params, json=data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, params=params, headers=headers)
                elif method == "PATCH":
                    response = await client.patch(url, params=params, json=data, headers=headers)
                else:
                    return ToolResult(
                        success=False,
                        error=f"Unsupported HTTP method: {method}"
                    )
                
                # Parse response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                return ToolResult(
                    success=response.is_success,
                    data={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response_data
                    },
                    error=None if response.is_success else f"HTTP {response.status_code}: {response.text}",
                    metadata={
                        "url": url,
                        "method": method,
                        "request_headers": headers
                    }
                )
                
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error=f"Request timeout after {self.timeout} seconds",
                metadata={"url": url, "method": method}
            )
        except httpx.RequestError as e:
            return ToolResult(
                success=False,
                error=f"Request failed: {str(e)}",
                metadata={"url": url, "method": method}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata={"url": url, "method": method}
            )


class UserManagementTool(ExternalApiTool):
    """Specialized tool for user management APIs."""
    
    @property
    def name(self) -> str:
        return "user_management"
    
    @property
    def description(self) -> str:
        return "Manage users in external systems (get, create, update user information)"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="User management action",
                enum=["get_user", "list_users", "create_user", "update_user"],
                required=True
            ),
            ToolParameter(
                name="user_id",
                type="string",
                description="User ID (required for get_user, update_user)",
                required=False
            ),
            ToolParameter(
                name="user_data",
                type="object",
                description="User data for create/update operations",
                required=False
            ),
            ToolParameter(
                name="filters",
                type="object",
                description="Filters for list_users operation",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute user management operation."""
        action = kwargs.get("action")
        user_id = kwargs.get("user_id")
        user_data = kwargs.get("user_data", {})
        filters = kwargs.get("filters", {})
        
        if action == "get_user":
            if not user_id:
                return ToolResult(success=False, error="user_id is required for get_user action")
            return await super().execute(
                method="GET",
                endpoint=f"/users/{user_id}"
            )
        
        elif action == "list_users":
            return await super().execute(
                method="GET",
                endpoint="/users",
                params=filters
            )
        
        elif action == "create_user":
            return await super().execute(
                method="POST",
                endpoint="/users",
                data=user_data
            )
        
        elif action == "update_user":
            if not user_id:
                return ToolResult(success=False, error="user_id is required for update_user action")
            return await super().execute(
                method="PUT",
                endpoint=f"/users/{user_id}",
                data=user_data
            )
        
        else:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}"
            ) 