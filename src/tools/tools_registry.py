"""
Tool Registry for GRC Agent Squad

This module provides a registry system for Agent tools that can be used by
the GRC Agent Squad. It loads tool definitions from the tools.yaml configuration
and makes them available to agents based on their configuration.
"""

import os
import yaml
import importlib
import structlog
from typing import Dict, List, Optional, Any
from agent_squad.utils import AgentTool


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
        
        # Load tool configuration from YAML first
        self._load_tool_configs()
        
        # Then dynamically import and register tools based on the config
        self._register_tools_from_config()
    
    def _register_tools_from_config(self) -> None:
        """Dynamically import and register tools based on the YAML configuration."""
        if not self.tool_configs:
            self.logger.warning("No tool configurations found. No tools will be registered.")
            return
            
        for tool_name, tool_config in self.tool_configs.items():
            try:
                # Determine module path based on naming convention
                # For example, highbond_token_exchange_api_tool should be in api_tools/user_token.py
                if "_api_tool" in tool_name:
                    module_category = "api_tools"
                    # For simplicity, we assume the module name matches part of the tool name
                    # This is a convention that can be adjusted as needed
                    if "highbond" in tool_name and "token" in tool_name:
                        module_name = "user_token"
                    else:
                        # Default fallback
                        module_name = tool_name.replace("_api_tool", "")
                elif tool_name == "interview_guide_tool":
                    # Special handling for interview guide tool
                    module_category = ""
                    module_name = "interview_guide_tool"
                else:
                    # Default fallback
                    module_category = "tools"
                    module_name = tool_name
                
                # Construct the full module path
                if module_category:
                    module_path = f"src.tools.{module_category}.{module_name}"
                else:
                    module_path = f"src.tools.{module_name}"
                
                # Dynamically import the module
                self.logger.info(f"Attempting to import tool '{tool_name}' from module '{module_path}'")
                module = importlib.import_module(module_path)
                
                # Look for the tool in the module
                if hasattr(module, tool_name):
                    tool = getattr(module, tool_name)
                    self.register_tool(tool)
                    self.logger.info(f"Successfully registered tool '{tool_name}' from '{module_path}'")
                else:
                    self.logger.error(f"Tool '{tool_name}' not found in module '{module_path}'")
            except ImportError as e:
                self.logger.error(f"Failed to import module for tool '{tool_name}': {e}")
                # Log more detailed information about the path being tried
                self.logger.error(f"Module path attempted: '{module_path}'")
            except Exception as e:
                self.logger.error(f"Error registering tool '{tool_name}': {e}")
    
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