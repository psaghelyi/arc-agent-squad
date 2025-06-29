"""
Agent configuration loader for the GRC Agent Squad.

This module provides functionality to load and manage agent configurations
from individual YAML files with JSON schema validation.
"""

import json
import os
import structlog
from typing import Any, Dict, List, Optional

import yaml

try:
    from jsonschema import ValidationError, validate
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    ValidationError = Exception

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
        self._communication_formats: Dict[str, str] = {}
        self._use_cases: Dict[str, Dict[str, Any]] = {}
        
        self._load_schema()
        self._load_communication_formats()
        self._load_use_cases()
        self._load_config()
    
    def _get_individual_schema_path(self) -> str:
        """Get the path for agent schema file."""
        config_dir = os.path.dirname(self.config_directory)
        return os.path.join(config_dir, "agent-schema.json")
    
    def _load_communication_formats(self) -> None:
        """Load common communication format instructions from YAML file."""
        try:
            # Get path to communication_formats.yaml
            config_dir = os.path.dirname(self.config_directory)
            common_dir = os.path.join(config_dir, "common")
            formats_path = os.path.join(common_dir, "communication_formats.yaml")
            
            if os.path.exists(formats_path):
                with open(formats_path, 'r', encoding='utf-8') as f:
                    formats_data = yaml.safe_load(f)
                
                # Store communication format instructions
                self._communication_formats = {
                    'display_mode': formats_data.get('display_mode_instructions', ''),
                    'voice_mode': formats_data.get('voice_mode_instructions', '')
                }
                
                self.logger.info("Communication format instructions loaded successfully")
            else:
                self.logger.warning("Communication formats file not found, using empty instructions", 
                                  formats_path=formats_path)
                self._communication_formats = {'display_mode': '', 'voice_mode': ''}
        except Exception as e:
            self.logger.error(f"Failed to load communication formats: {e}")
            self._communication_formats = {'display_mode': '', 'voice_mode': ''}

    def _load_use_cases(self) -> None:
        """Load common use case descriptions from YAML file."""
        try:
            # Get path to use_cases.yaml
            config_dir = os.path.dirname(self.config_directory)
            common_dir = os.path.join(config_dir, "common")
            use_cases_path = os.path.join(common_dir, "use_cases.yaml")
            
            if os.path.exists(use_cases_path):
                with open(use_cases_path, 'r', encoding='utf-8') as f:
                    use_cases_data = yaml.safe_load(f)
                
                # Store use cases
                self._use_cases = use_cases_data.get('use_cases', {})
                
                self.logger.info("Use cases loaded successfully", count=len(self._use_cases))
            else:
                self.logger.warning("Use cases file not found, using empty dictionary", 
                                  use_cases_path=use_cases_path)
                self._use_cases = {}
        except Exception as e:
            self.logger.error(f"Failed to load use cases: {e}")
            self._use_cases = {}

    def get_communication_formats(self) -> Dict[str, str]:
        """Get the loaded communication format instructions."""
        return self._communication_formats.copy()
    
    def get_use_cases(self) -> Dict[str, Dict[str, Any]]:
        """Get the loaded use cases."""
        return self._use_cases.copy()

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
                    
                    # Create FileBasedAgentConfig instance with communication formats and use cases
                    self._agent_configs[agent_id] = FileBasedAgentConfig(
                        agent_id=agent_id,
                        config_data=agent_data,
                        default_model_settings=agent_data.get('model_settings', {}),
                        communication_formats=self._communication_formats,
                        use_cases=self._use_cases
                    )
                    
                    self.logger.debug(f"Loaded agent configuration for '{agent_id}'", 
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
            self.logger.debug(f"Individual agent configuration validation passed for '{agent_id}'")
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
    
    def __init__(self, agent_id: str, config_data: Dict[str, Any], default_model_settings: Dict[str, Any],
                 communication_formats: Optional[Dict[str, str]] = None, use_cases: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize agent configuration from loaded data.
        
        Args:
            agent_id: Unique identifier for the agent
            config_data: Raw configuration data from YAML file
            default_model_settings: Default model settings to use if not specified
            communication_formats: Common communication format instructions
            use_cases: Common use case descriptions
        """

        self.logger = structlog.get_logger(__name__)

        self.agent_id = agent_id
        self.config_data = config_data
        self.default_model_settings = default_model_settings
        self.communication_formats = communication_formats or {}
        self.use_cases = use_cases or {}
        
        # Validate required fields
        required_fields = ['id', 'name', 'description']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field '{field}' in agent configuration for {agent_id}")

    def get_system_prompt(self) -> str:
        """Get the system prompt template for the agent."""
        base_prompt = self.config_data.get('system_prompt_template', '')
        
        # Add use case descriptions if available
        agent_use_cases = self.get_use_cases()
        self.logger.debug(f"Agent {self.agent_id} use cases: {agent_use_cases}")
        self.logger.debug(f"Available common use cases: {list(self.use_cases.keys())}")
        
        if agent_use_cases and self.use_cases:
            use_cases_section = "\n\n## USE CASES:\n"
            
            for use_case_id in agent_use_cases:
                # Check if this use case has a detailed description in the common use cases
                if use_case_id in self.use_cases:
                    use_case = self.use_cases[use_case_id]
                    self.logger.debug(f"Adding use case {use_case_id}: {use_case['name']}")
                    use_cases_section += f"### {use_case['name']}\n"
                    use_cases_section += f"{use_case['description']}\n\n"
                else:
                    self.logger.debug(f"Use case {use_case_id} not found in common use cases")
            
            # Only add the section if we found at least one matching use case
            if use_cases_section != "\n\n## USE CASES:\n":
                self.logger.debug(f"Adding use cases section to prompt for agent {self.agent_id}")
                base_prompt += use_cases_section
            else:
                self.logger.debug(f"No matching use cases found for agent {self.agent_id}")
        else:
            self.logger.debug(f"No use cases available for agent {self.agent_id} or no common use cases defined")
        
        # Add communication format instructions if available
        if self.communication_formats and (self.communication_formats.get('display_mode') 
                                           or self.communication_formats.get('voice_mode')):
            # Add a section heading for communication formats
            format_section = "\n\n## RESPONSE FORMATTING:\n"
            
            # Add display mode instructions if available
            if self.communication_formats.get('display_mode'):
                format_section += self.communication_formats['display_mode'] + "\n\n"
                
            # Add voice mode instructions if available
            if self.communication_formats.get('voice_mode'):
                format_section += self.communication_formats['voice_mode']
                
            # Append the format section to the base prompt
            base_prompt += format_section
        
        return base_prompt
    
    def get_system_prompt_variables(self) -> Optional[Dict[str, Any]]:
        """Get the system prompt variables for the agent."""
        return self.config_data.get('system_prompt_variables', None)


    def get_tools(self) -> List[str]:
        """Get the list of available tools for the agent."""
        return self.config_data.get('tools', [])

    def get_voice_settings(self) -> Dict[str, str]:
        """Get voice settings for the agent."""
        return self.config_data.get('voice_settings', {})

    def get_use_cases(self) -> List[str]:
        """Get the list of use cases for the agent."""
        return self.config_data.get('use_cases', [])

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
        
        voice_settings = config.get_voice_settings()
        voice_enabled = bool(voice_settings and voice_settings.get('voice_id'))
        
        return {
            "agent_id": agent_id,
            "name": config.config_data.get('name', agent_id),
            "description": config.config_data.get('description', ''),
            "use_cases": config.get_use_cases(),
            "tools": config.get_tools(),
            "voice_settings": voice_settings,
            "voice_enabled": voice_enabled,
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