"""
Agent configuration loader for the GRC Agent Squad.

This module provides functionality to load and manage agent configurations
from individual YAML files with JSON schema validation.
"""

import json
import os
from typing import Any, Dict, List, Optional

import structlog
import yaml

try:
    from jsonschema import ValidationError, validate
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    ValidationError = Exception

from src.models.agent_models import AgentCapability
from src.utils.settings import settings


class AgentConfigLoader:
    """Loads and manages agent configurations from individual YAML files with schema validation."""
    
    def __init__(self, config_directory: Optional[str] = None, active_agents: Optional[List[str]] = None):
        """
        Initialize the agent configuration loader.
        
        Args:
            config_directory: Path to directory containing individual agent files.
                            If None, uses the path from settings.
            active_agents: List of agent IDs to load. If None, uses settings.
        """
        self.logger = structlog.get_logger(__name__)
        self.config_directory = config_directory or settings.agent_config_directory
        self.active_agents = active_agents or settings.active_agents_list
        self.individual_schema_path = self._get_individual_schema_path()
        self._agent_configs: Dict[str, 'FileBasedAgentConfig'] = {}
        self._individual_schema: Optional[Dict[str, Any]] = None
        
        self._load_schema()
        self._load_config()
    
    def _get_individual_schema_path(self) -> str:
        """Get the path for agent schema file."""
        config_dir = os.path.dirname(self.config_directory)
        return os.path.join(config_dir, "agent-schema.json")
    
    def _load_schema(self):
        """Load the JSON schema for individual agent validation."""
        try:
            if os.path.exists(self.individual_schema_path):
                with open(self.individual_schema_path, 'r', encoding='utf-8') as f:
                    self._individual_schema = json.load(f)
                self.logger.info("Individual agent schema loaded successfully", schema_path=self.individual_schema_path)
            else:
                self.logger.warning("Individual agent schema not found, skipping validation", 
                                  schema_path=self.individual_schema_path)
        except Exception as e:
            self.logger.error("Failed to load individual agent schema", 
                            schema_path=self.individual_schema_path, error=str(e))
            self._individual_schema = None
    
    def _load_config(self) -> None:
        """Load the agent configurations from individual YAML files with optional schema validation."""
        self._load_individual_agent_files()
    
    def _load_individual_agent_files(self) -> None:
        """Load agent configurations from individual YAML files."""
        try:
            # Resolve relative paths from the project root
            if not os.path.isabs(self.config_directory):
                # Get the project root (assuming this file is in src/agents/)
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                config_dir = os.path.join(project_root, self.config_directory)
            else:
                config_dir = self.config_directory
            
            if not os.path.exists(config_dir):
                raise FileNotFoundError(f"Agent config directory not found: {config_dir}")
            
            # Get list of active agents from instance or settings
            active_agent_ids = self.active_agents
            if not active_agent_ids:
                self.logger.warning("No active agents specified in configuration")
                return
            
            self.logger.info(f"Loading active agents: {active_agent_ids}")
            
            # Load each active agent's configuration file
            for agent_id in active_agent_ids:
                agent_file_path = os.path.join(config_dir, f"{agent_id}.yaml")
                
                # Try .yml extension if .yaml doesn't exist
                if not os.path.exists(agent_file_path):
                    agent_file_path = os.path.join(config_dir, f"{agent_id}.yml")
                
                if not os.path.exists(agent_file_path):
                    self.logger.error(f"Agent configuration file not found for '{agent_id}': {agent_file_path}")
                    continue
                
                try:
                    with open(agent_file_path, 'r', encoding='utf-8') as f:
                        agent_data = yaml.safe_load(f)
                    
                    # Validate individual agent configuration
                    self._validate_individual_agent_config(agent_data, agent_id)
                    
                    # Create FileBasedAgentConfig instance
                    self._agent_configs[agent_id] = FileBasedAgentConfig(
                        agent_id=agent_id,
                        config_data=agent_data,
                        default_model_settings=agent_data.get('model_settings', {})
                    )
                    
                    self.logger.info(f"Loaded agent configuration for '{agent_id}'", 
                                   config_file=agent_file_path)
                    
                except Exception as e:
                    self.logger.error(f"Failed to load agent '{agent_id}' configuration", 
                                    config_file=agent_file_path, error=str(e))
                    continue
            
            self.logger.info(
                "Individual agent configurations loaded successfully",
                config_directory=config_dir,
                agent_count=len(self._agent_configs),
                active_agents=active_agent_ids
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to load individual agent configurations",
                config_directory=self.config_directory,
                error=str(e)
            )
            raise

    def _validate_individual_agent_config(self, agent_data: Dict[str, Any], agent_id: str) -> None:
        """Validate an individual agent configuration against the schema."""
        if not self._individual_schema or not HAS_JSONSCHEMA:
            if not HAS_JSONSCHEMA:
                self.logger.warning("jsonschema not available, skipping individual agent validation")
            else:
                self.logger.info("No individual agent schema loaded, skipping validation")
            return
        
        try:
            validate(instance=agent_data, schema=self._individual_schema)
            self.logger.info(f"Individual agent configuration validation passed for '{agent_id}'")
        except ValidationError as e:
            self.logger.error(f"Individual agent configuration validation failed for '{agent_id}'", 
                            validation_error=str(e),
                            path=list(e.absolute_path) if e.absolute_path else None)
            raise ValueError(f"Individual agent configuration validation failed for '{agent_id}': {e.message}")
        except Exception as e:
            self.logger.error(f"Unexpected error during individual agent validation for '{agent_id}'", error=str(e))
            raise

    def get_config(self, agent_id: str) -> Optional['FileBasedAgentConfig']:
        """Get the configuration for a specific agent."""
        return self._agent_configs.get(agent_id)

    def get_all_configs(self) -> Dict[str, 'FileBasedAgentConfig']:
        """Get all loaded agent configurations."""
        return self._agent_configs.copy()

    def list_agent_ids(self) -> List[str]:
        """Get a list of all loaded agent IDs."""
        return list(self._agent_configs.keys())

    def reload_config(self) -> None:
        """Reload all agent configurations from files."""
        self._agent_configs.clear()
        self._load_schema()
        self._load_config()


class FileBasedAgentConfig:
    """Configuration for a single agent loaded from a YAML file."""
    
    def __init__(self, agent_id: str, config_data: Dict[str, Any], default_model_settings: Dict[str, Any]):
        """
        Initialize agent configuration from loaded data.
        
        Args:
            agent_id: Unique identifier for the agent
            config_data: Raw configuration data from YAML file
            default_model_settings: Default model settings to use if not specified
        """
        self.agent_id = agent_id
        self.config_data = config_data
        self.default_model_settings = default_model_settings
        
        # Validate required fields
        required_fields = ['id', 'name', 'description']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field '{field}' in agent configuration for {agent_id}")

    def get_system_prompt(self) -> str:
        """Get the system prompt template for the agent."""
        return self.config_data.get('system_prompt_template', '')

    def get_capabilities(self) -> List[AgentCapability]:
        """Get the list of capabilities for the agent."""
        capabilities_data = self.config_data.get('capabilities', [])
        capabilities = []
        for cap in capabilities_data:
            try:
                # Try to convert string to enum
                if isinstance(cap, str):
                    # Handle different naming conventions
                    cap_normalized = cap.upper().replace('-', '_').replace(' ', '_')
                    capabilities.append(AgentCapability[cap_normalized])
                else:
                    capabilities.append(cap)
            except (KeyError, ValueError):
                # If conversion fails, skip this capability or handle gracefully
                print(f"Warning: Unknown capability '{cap}' for agent {self.agent_id}")
                continue
        return capabilities

    def get_specialized_tools(self) -> List[str]:
        """Get the list of specialized tools for the agent."""
        return self.config_data.get('specialized_tools', [])

    def get_voice_settings(self) -> Dict[str, str]:
        """Get voice settings for the agent."""
        return self.config_data.get('voice_settings', {})

    def get_use_cases(self) -> List[str]:
        """Get the list of use cases for the agent."""
        return self.config_data.get('use_cases', [])

    def get_personality(self) -> Dict[str, Any]:
        """Get personality configuration for the agent."""
        return self.config_data.get('personality', {})

    def get_model_settings(self) -> Dict[str, Any]:
        """Get model settings for the agent, with fallback to defaults."""
        agent_model_settings = self.config_data.get('model_settings', {})
        # Merge with defaults, agent-specific settings take precedence
        merged_settings = {**self.default_model_settings, **agent_model_settings}
        return merged_settings


class FileBasedGRCAgentConfigRegistry:
    """Registry for managing GRC agent configurations."""
    
    def __init__(self, config_directory: Optional[str] = None, active_agents: Optional[List[str]] = None):
        """Initialize the registry with a configuration loader."""
        self.loader = AgentConfigLoader(config_directory=config_directory, active_agents=active_agents)

    def get_config(self, agent_id: str) -> Optional[FileBasedAgentConfig]:
        """Get configuration for a specific agent."""
        return self.loader.get_config(agent_id)

    def get_all_configs(self) -> Dict[str, FileBasedAgentConfig]:
        """Get all agent configurations."""
        return self.loader.get_all_configs()

    def build_agent_metadata(self, agent_id: str) -> Dict[str, Any]:
        """Build metadata for an agent suitable for the agent-squad framework."""
        config = self.get_config(agent_id)
        if not config:
            raise ValueError(f"No configuration found for agent: {agent_id}")
        
        return {
            "agent_id": agent_id,
            "name": config.config_data.get('name', agent_id),
            "description": config.config_data.get('description', ''),
            "capabilities": [cap.value for cap in config.get_capabilities()],
            "use_cases": config.get_use_cases(),
            "specialized_tools": config.get_specialized_tools(),
            "voice_settings": config.get_voice_settings(),
            "personality": config.get_personality(),
            "system_prompt": config.get_system_prompt(),
            "model_settings": config.get_model_settings()
        }

    def list_agent_ids(self) -> List[str]:
        """Get list of all available agent IDs."""
        return self.loader.list_agent_ids()

    def reload_configs(self) -> None:
        """Reload all configurations from files."""
        self.loader.reload_config()


def get_default_config_registry() -> FileBasedGRCAgentConfigRegistry:
    """Get the default configuration registry instance."""
    return FileBasedGRCAgentConfigRegistry() 