"""
Tool Registry for GRC Agent Squad

This module provides a registry system for Agent tools that can be used by
the GRC Agent Squad. It loads tool definitions from the tools.yaml configuration
and makes them available to agents based on their configuration.
"""

import os
import yaml
import structlog
from typing import Dict, List, Optional, Any
from agent_squad.utils import AgentTool

# Import available tools
from src.tools.api_tools.user_token_tool import highbond_token_exchange_api_tool


class ToolsRegistry:
    """
    Registry for agent tools that can be used by GRC agents.
    
    Loads tool definitions from configuration and provides a unified
    interface for accessing and managing available tools.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the tools registry.
        
        Args:
            config_path: Optional path to the tools configuration file.
                         If not provided, uses the default path.
        """
        self.logger = structlog.get_logger(__name__)
        self.tools: Dict[str, AgentTool] = {}
        self.tool_configs: Dict[str, Dict[str, Any]] = {}
        
        # Set default config path if not provided
        if config_path is None:
            # Navigate from the current file to the config directory
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'config', 'common', 'tools.yaml'
            )
        
        self.config_path = config_path
        
        # Register built-in tools
        self._register_builtin_tools()
        
        # Load tool configuration from YAML
        self._load_tool_configs()
    
    def _register_builtin_tools(self) -> None:
        """Register the built-in tools with the registry."""
        # Register the highbond token exchange tool
        self.register_tool(highbond_token_exchange_api_tool)
        
        # More built-in tools can be registered here as they are developed
    
    def register_tool(self, tool: AgentTool) -> None:
        """
        Register a tool with the registry.
        
        Args:
            tool: The AgentTool instance to register
        """
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def _load_tool_configs(self) -> None:
        """Load tool configurations from the YAML configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    config = yaml.safe_load(file)
                
                self.logger.info(f"Loaded tools configuration from {self.config_path}")
                
                if isinstance(config, dict) and 'tools' in config:
                    tool_definitions = config['tools']
                    self.tool_configs = tool_definitions
                    self.logger.info(f"Found {len(tool_definitions)} tool definitions in configuration")
                    
                    # Log available tools vs configured tools
                    configured_tool_names = list(tool_definitions.keys())
                    registered_tool_names = list(self.tools.keys())
                    
                    self.logger.info(f"Configured tools: {configured_tool_names}")
                    self.logger.info(f"Registered tools: {registered_tool_names}")
                    
                    # Check for tools that are configured but not registered
                    missing_tools = [name for name in configured_tool_names if name not in registered_tool_names]
                    if missing_tools:
                        self.logger.warning(f"Some configured tools are not registered: {missing_tools}")
            else:
                self.logger.warning(f"Tools configuration file not found: {self.config_path}")
                
        except Exception as e:
            self.logger.error(f"Error loading tools configuration: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[AgentTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: The name of the tool to get
            
        Returns:
            The AgentTool instance if found, None otherwise
        """
        return self.tools.get(tool_name)
    
    def get_tools_for_agent(self, tool_names: List[str]) -> List[AgentTool]:
        """
        Get a list of tools for an agent based on the tool names in its configuration.
        
        Args:
            tool_names: List of tool names the agent is configured to use
            
        Returns:
            List of AgentTool instances that match the requested names
        """
        agent_tools = []
        for tool_name in tool_names:
            tool = self.get_tool(tool_name)
            if tool:
                agent_tools.append(tool)
            else:
                self.logger.warning(f"Tool '{tool_name}' requested but not available in registry")
                
        return agent_tools
    
    def list_available_tools(self) -> List[str]:
        """
        Get a list of all available tool names.
        
        Returns:
            List of tool names registered in the registry
        """
        return list(self.tools.keys())
    
    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a tool by name.
        
        Args:
            tool_name: The name of the tool to get configuration for
            
        Returns:
            The tool configuration if found, None otherwise
        """
        return self.tool_configs.get(tool_name)


# Create a singleton instance of the tools registry
tools_registry = ToolsRegistry() 