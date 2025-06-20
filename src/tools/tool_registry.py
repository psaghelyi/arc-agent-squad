"""
Tool Registry for managing and discovering available tools.

This registry maintains a collection of tools that agents can use,
following the MCP pattern for tool discovery and execution.
"""

from typing import Dict, List, Optional, Any
import structlog
from .base_tool import BaseTool, ToolResult


class ToolRegistry:
    """Registry for managing agent tools."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        self.logger.info(f"Tool registered", tool_name=tool.name)
    
    def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if tool was found and removed
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            self.logger.info(f"Tool unregistered", tool_name=tool_name)
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all registered tools.
        
        Returns:
            List of tool schemas for agent consumption
        """
        return [tool.get_schema() for tool in self._tools.values()]
    
    def get_tools_by_capability(self, capability: str) -> List[BaseTool]:
        """
        Get tools that match a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of matching tools
        """
        # This is a simple implementation - could be enhanced with metadata
        matching_tools = []
        capability_lower = capability.lower()
        
        for tool in self._tools.values():
            if (capability_lower in tool.name.lower() or 
                capability_lower in tool.description.lower()):
                matching_tools.append(tool)
        
        return matching_tools
    
    async def execute_tool(self, tool_name: str, **parameters) -> ToolResult:
        """
        Execute a tool by name with parameters.
        
        Args:
            tool_name: Name of the tool to execute
            **parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                metadata={"available_tools": self.list_tools()}
            )
        
        return await tool.safe_execute(**parameters)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Registry statistics
        """
        return {
            "total_tools": len(self._tools),
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameter_count": len(tool.parameters)
                }
                for tool in self._tools.values()
            ]
        }


# Global tool registry instance
default_registry = ToolRegistry()


def get_default_registry() -> ToolRegistry:
    """Get the default global tool registry."""
    return default_registry 