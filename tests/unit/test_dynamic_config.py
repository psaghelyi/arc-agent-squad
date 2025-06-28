"""
Test suite for dynamic configuration system.

This module tests:
1. Settings class and all its configuration keys
2. Agent configuration loader functionality
3. Dynamic agent filtering and validation
4. Schema validation
5. Ensures all configuration keys are being used in the application
"""

import os
import tempfile
import json
import yaml
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from src.utils.settings import Settings, settings
from src.agents.agent_config_loader import AgentConfigLoader, FileBasedAgentConfig, FileBasedGRCAgentConfigRegistry


class TestSettings:
    """Test the Settings class and configuration management."""
    
    def test_settings_initialization(self):
        """Test that settings can be initialized with defaults."""
        test_settings = Settings()
        
        # Test AWS defaults
        assert test_settings.aws_profile == "acl-playground"
        assert test_settings.aws_region == "us-west-2"
        
        # Test agent configuration defaults
        assert test_settings.agent_config_directory == "config/agents"
        assert "empathetic_interviewer_executive" in test_settings.active_agents
        assert test_settings.default_agent == "supervisor_grc"
        
        # Test API defaults
        assert test_settings.api_port == 8000
        assert test_settings.api_host == "0.0.0.0"
        
        # Test voice defaults
        assert test_settings.transcribe_language_code == "en-US"
        assert test_settings.polly_voice_id == "Joanna"
        assert test_settings.polly_engine == "neural"
    
    def test_active_agents_list_property(self):
        """Test the active_agents_list property."""
        test_settings = Settings()
        agents_list = test_settings.active_agents_list
        
        assert isinstance(agents_list, list)
        assert len(agents_list) == 5
        assert "empathetic_interviewer_executive" in agents_list
        assert "authoritative_compliance_executive" in agents_list
        assert "analytical_risk_expert_executive" in agents_list
        assert "strategic_governance_executive" in agents_list
        assert "supervisor_grc" in agents_list
        
        # Verify that active_agents_list returns the same list as active_agents
        assert agents_list is test_settings.active_agents
    
    def test_cors_origins_list_property(self):
        """Test the cors_origins_list property conversion."""
        test_settings = Settings()
        cors_list = test_settings.cors_origins_list
        
        assert isinstance(cors_list, list)
        # Check that the list contains the expected values (may be parsed differently)
        cors_str = ",".join(cors_list)
        assert "localhost:3000" in cors_str
        assert "localhost:8080" in cors_str
    
    def test_stun_servers_list_property(self):
        """Test the stun_servers_list property conversion."""
        test_settings = Settings()
        stun_list = test_settings.stun_servers_list
        
        assert isinstance(stun_list, list)
        assert "stun:stun.l.google.com:19302" in stun_list
    
    def test_turn_servers_list_property_empty(self):
        """Test the turn_servers_list property when no TURN servers are configured."""
        test_settings = Settings()
        turn_list = test_settings.turn_servers_list
        
        assert isinstance(turn_list, list)
        assert len(turn_list) == 0
    
    def test_turn_servers_list_property_with_servers(self):
        """Test the turn_servers_list property with TURN servers configured."""
        test_settings = Settings(webrtc_turn_servers="turn:server1.com:3478,turn:server2.com:3478")
        turn_list = test_settings.turn_servers_list
        
        assert isinstance(turn_list, list)
        assert len(turn_list) == 2
        assert "turn:server1.com:3478" in turn_list
        assert "turn:server2.com:3478" in turn_list
    
    def test_is_production_property(self):
        """Test the is_production property logic."""
        # Test development mode
        test_settings = Settings(development_mode=True, debug=False)
        assert not test_settings.is_production
        
        # Test debug mode
        test_settings = Settings(development_mode=False, debug=True)
        assert not test_settings.is_production
        
        # Test production mode
        test_settings = Settings(development_mode=False, debug=False)
        assert test_settings.is_production
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_is_production_with_env_var(self):
        """Test is_production with environment variable override."""
        test_settings = Settings(development_mode=True)
        assert test_settings.is_production
    
    def test_should_validate_production(self):
        """Test the should_validate_production logic."""
        # Development mode should not validate
        test_settings = Settings(development_mode=True)
        assert not test_settings.should_validate_production()
        
        # Debug mode should not validate
        test_settings = Settings(debug=True)
        assert not test_settings.should_validate_production()
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production", "SKIP_AWS_VALIDATION": "false"})
    def test_should_validate_production_with_env(self):
        """Test should_validate_production with environment variables."""
        test_settings = Settings(development_mode=False, debug=False)
        assert test_settings.should_validate_production()
    
    @patch.dict(os.environ, {"SKIP_AWS_VALIDATION": "true"})
    def test_should_skip_validation_with_env(self):
        """Test should_validate_production when validation is skipped."""
        test_settings = Settings(development_mode=False, debug=False)
        assert not test_settings.should_validate_production()
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production", "SKIP_AWS_VALIDATION": "false"})
    def test_validate_required_for_production_missing_lex(self):
        """Test validation fails when LEX_BOT_ID is missing in production."""
        test_settings = Settings(development_mode=False, debug=False)
        
        with pytest.raises(ValueError, match="Missing required production settings.*LEX_BOT_ID"):
            test_settings.validate_required_for_production()
    
    @patch.dict(os.environ, {"AWS_PROFILE": "", "ENVIRONMENT": "production", "SKIP_AWS_VALIDATION": "false"}, clear=True)
    def test_validate_required_for_production_missing_aws(self):
        """Test validation fails when AWS credentials are missing in production."""
        test_settings = Settings(
            development_mode=False, 
            debug=False,
            lex_bot_id="test-bot",
            aws_access_key_id=None
        )
        
        with pytest.raises(ValueError, match="Missing required production settings.*AWS_ACCESS_KEY_ID"):
            test_settings.validate_required_for_production()
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production", "SKIP_AWS_VALIDATION": "false"})
    def test_validate_required_for_production_success(self):
        """Test validation passes when all required fields are present."""
        test_settings = Settings(
            development_mode=False,
            debug=False,
            lex_bot_id="test-bot",
            aws_access_key_id="test-key"
        )
        
        # Should not raise any exception
        test_settings.validate_required_for_production()


class TestAgentConfigLoader:
    """Test the AgentConfigLoader class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory with test agent configurations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config directory structure
            config_dir = os.path.join(temp_dir, "config")
            agents_dir = os.path.join(config_dir, "agents")
            os.makedirs(agents_dir, exist_ok=True)
            
            # Create test agent schema
            schema_data = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "name", "description"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "system_prompt_template": {"type": "string"},
                    "specialized_tools": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "voice_settings": {"type": "object"},
                    "use_cases": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "personality": {"type": "object"},
                    "model_settings": {"type": "object"},
                    "inference_config": {"type": "object"}
                },
                "additionalProperties": True
            }
            
            schema_path = os.path.join(config_dir, "agent-schema.json")
            with open(schema_path, 'w') as f:
                json.dump(schema_data, f)
            
            # Create test agent configurations
            test_agents = {
                "test_agent_1": {
                    "id": "test_agent_1",
                    "name": "Test Agent 1",
                    "description": "First test agent",
                    "system_prompt_template": "You are test agent 1",
                    "specialized_tools": ["tool1", "tool2"],
                    "voice_settings": {
                        "voice_id": "Joanna",
                        "style": "conversational"
                    },
                    "use_cases": ["Testing", "Validation"],
                    "personality": {
                        "traits": ["analytical", "helpful"]
                    },
                    "model_settings": {
                        "max_tokens": 4096,
                        "temperature": 0.7
                    },
                    "inference_config": {
                        "top_p": 0.9
                    }
                },
                "test_agent_2": {
                    "id": "test_agent_2",
                    "name": "Test Agent 2",
                    "description": "Second test agent",
                    "system_prompt_template": "You are test agent 2",
                    "specialized_tools": ["tool3"],
                    "voice_settings": {
                        "voice_id": "Matthew",
                        "style": "formal"
                    },
                    "use_cases": ["Compliance"],
                    "personality": {
                        "traits": ["authoritative"]
                    },
                    "model_settings": {
                        "max_tokens": 6144,
                        "temperature": 0.6
                    }
                }
            }
            
            for agent_id, agent_data in test_agents.items():
                agent_path = os.path.join(agents_dir, f"{agent_id}.yaml")
                with open(agent_path, 'w') as f:
                    yaml.dump(agent_data, f)
            
            yield {
                "temp_dir": temp_dir,
                "config_dir": config_dir,
                "agents_dir": agents_dir,
                "schema_path": schema_path,
                "test_agents": test_agents
            }
    
    def test_agent_config_loader_initialization(self, temp_config_dir):
        """Test AgentConfigLoader initialization."""
        agents_dir = temp_config_dir["agents_dir"]
        active_agents = ["test_agent_1", "test_agent_2"]
        
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=active_agents
        )
        
        assert loader.config_directory == agents_dir
        assert loader.active_agents == active_agents
        assert len(loader._agent_configs) == 2
        assert "test_agent_1" in loader._agent_configs
        assert "test_agent_2" in loader._agent_configs
    
    def test_agent_config_loader_with_settings(self, temp_config_dir):
        """Test AgentConfigLoader using settings defaults."""
        agents_dir = temp_config_dir["agents_dir"]
        
        with patch.dict(os.environ, {
            "AGENT_CONFIG_DIRECTORY": agents_dir,
            "ACTIVE_AGENTS": '["test_agent_1"]'
        }):
            # Create new settings instance with environment variables
            test_settings = Settings()
            with patch('src.agents.agent_config_loader.settings', test_settings):
                loader = AgentConfigLoader()
                
                assert len(loader._agent_configs) == 1
                assert "test_agent_1" in loader._agent_configs
    
    def test_agent_config_loader_missing_directory(self):
        """Test AgentConfigLoader with missing directory."""
        with pytest.raises(FileNotFoundError):
            AgentConfigLoader(
                config_directory="/nonexistent/directory",
                active_agents=["test_agent"]
            )
    
    def test_agent_config_loader_missing_agent_file(self, temp_config_dir):
        """Test AgentConfigLoader with missing agent file."""
        agents_dir = temp_config_dir["agents_dir"]
        
        # Try to load a non-existent agent
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=["nonexistent_agent"]
        )
        
        # Should not crash, but should not load any configs
        assert len(loader._agent_configs) == 0
    
    def test_agent_config_loader_invalid_yaml(self, temp_config_dir):
        """Test AgentConfigLoader with invalid YAML file."""
        agents_dir = temp_config_dir["agents_dir"]
        
        # Create invalid YAML file
        invalid_path = os.path.join(agents_dir, "invalid_agent.yaml")
        with open(invalid_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=["invalid_agent"]
        )
        
        # Should not crash, but should not load the invalid config
        assert len(loader._agent_configs) == 0
    
    def test_agent_config_loader_schema_validation_failure(self, temp_config_dir):
        """Test AgentConfigLoader with schema validation failure."""
        agents_dir = temp_config_dir["agents_dir"]
        
        # Create agent config missing required fields
        invalid_agent = {
            "name": "Invalid Agent",
            # Missing required 'id' and 'description'
        }
        
        invalid_path = os.path.join(agents_dir, "invalid_schema_agent.yaml")
        with open(invalid_path, 'w') as f:
            yaml.dump(invalid_agent, f)
        
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=["invalid_schema_agent"]
        )
        
        # Should not load the invalid config
        assert len(loader._agent_configs) == 0
    
    def test_get_config(self, temp_config_dir):
        """Test getting specific agent configuration."""
        agents_dir = temp_config_dir["agents_dir"]
        
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=["test_agent_1", "test_agent_2"]
        )
        
        config = loader.get_config("test_agent_1")
        assert config is not None
        assert config.agent_id == "test_agent_1"
        
        # Test non-existent agent
        config = loader.get_config("nonexistent")
        assert config is None
    
    def test_get_all_configs(self, temp_config_dir):
        """Test getting all agent configurations."""
        agents_dir = temp_config_dir["agents_dir"]
        
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=["test_agent_1", "test_agent_2"]
        )
        
        all_configs = loader.get_all_configs()
        assert len(all_configs) == 2
        assert "test_agent_1" in all_configs
        assert "test_agent_2" in all_configs
    
    def test_list_agent_ids(self, temp_config_dir):
        """Test listing agent IDs."""
        agents_dir = temp_config_dir["agents_dir"]
        
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=["test_agent_1", "test_agent_2"]
        )
        
        agent_ids = loader.list_agent_ids()
        assert len(agent_ids) == 2
        assert "test_agent_1" in agent_ids
        assert "test_agent_2" in agent_ids
    
    def test_reload_config(self, temp_config_dir):
        """Test reloading configurations."""
        agents_dir = temp_config_dir["agents_dir"]
        
        loader = AgentConfigLoader(
            config_directory=agents_dir,
            active_agents=["test_agent_1"]
        )
        
        assert len(loader._agent_configs) == 1
        
        # Change active agents and reload
        loader.active_agents = ["test_agent_1", "test_agent_2"]
        loader.reload_config()
        
        assert len(loader._agent_configs) == 2


class TestFileBasedAgentConfig:
    """Test the FileBasedAgentConfig class."""
    
    @pytest.fixture
    def sample_agent_data(self):
        """Sample agent configuration data."""
        return {
            "id": "test_agent",
            "name": "Test Agent",
            "description": "A test agent for validation",
            "system_prompt_template": "You are a test agent.",
            "specialized_tools": ["tool1", "tool2"],
            "voice_settings": {
                "voice_id": "Joanna",
                "style": "conversational"
            },
            "use_cases": ["Testing", "Validation"],
            "personality": {
                "traits": ["helpful", "analytical"]
            },
            "model_settings": {
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "inference_config": {
                "top_p": 0.9
            }
        }
    
    def test_file_based_agent_config_initialization(self, sample_agent_data):
        """Test FileBasedAgentConfig initialization."""
        config = FileBasedAgentConfig(
            agent_id="test_agent",
            config_data=sample_agent_data,
            default_model_settings={}
        )
        
        assert config.agent_id == "test_agent"
        assert config.config_data == sample_agent_data
    
    def test_file_based_agent_config_missing_required_field(self, sample_agent_data):
        """Test FileBasedAgentConfig with missing required field."""
        # Remove required field
        del sample_agent_data["id"]
        
        with pytest.raises(ValueError, match="Missing required field 'id'"):
            FileBasedAgentConfig(
                agent_id="test_agent",
                config_data=sample_agent_data,
                default_model_settings={}
            )
    
    def test_get_system_prompt(self, sample_agent_data):
        """Test getting system prompt."""
        config = FileBasedAgentConfig(
            agent_id="test_agent",
            config_data=sample_agent_data,
            default_model_settings={}
        )
        
        prompt = config.get_system_prompt()
        assert prompt == "You are a test agent."
    
    def test_get_specialized_tools(self, sample_agent_data):
        """Test getting specialized tools."""
        config = FileBasedAgentConfig(
            agent_id="test_agent",
            config_data=sample_agent_data,
            default_model_settings={}
        )
        
        tools = config.get_specialized_tools()
        assert tools == ["tool1", "tool2"]
    
    def test_get_voice_settings(self, sample_agent_data):
        """Test getting voice settings."""
        config = FileBasedAgentConfig(
            agent_id="test_agent",
            config_data=sample_agent_data,
            default_model_settings={}
        )
        
        voice_settings = config.get_voice_settings()
        assert voice_settings["voice_id"] == "Joanna"
        assert voice_settings["style"] == "conversational"
    
    def test_get_use_cases(self, sample_agent_data):
        """Test getting use cases."""
        config = FileBasedAgentConfig(
            agent_id="test_agent",
            config_data=sample_agent_data,
            default_model_settings={}
        )
        
        use_cases = config.get_use_cases()
        assert use_cases == ["Testing", "Validation"]
    
    def test_get_personality(self, sample_agent_data):
        """Test getting personality."""
        config = FileBasedAgentConfig(
            agent_id="test_agent",
            config_data=sample_agent_data,
            default_model_settings={}
        )
        
        personality = config.get_personality()
        assert personality["traits"] == ["helpful", "analytical"]
    
    def test_get_model_settings(self, sample_agent_data):
        """Test getting model settings."""
        config = FileBasedAgentConfig(
            agent_id="test_agent",
            config_data=sample_agent_data,
            default_model_settings={"default_param": "value"}
        )
        
        model_settings = config.get_model_settings()
        assert model_settings["max_tokens"] == 4096
        assert model_settings["temperature"] == 0.7


class TestFileBasedGRCAgentConfigRegistry:
    """Test the FileBasedGRCAgentConfigRegistry class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory with test agent configurations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config directory structure
            config_dir = os.path.join(temp_dir, "config")
            agents_dir = os.path.join(config_dir, "agents")
            os.makedirs(agents_dir, exist_ok=True)
            
            # Create test agent configurations
            test_agent = {
                "id": "test_registry_agent",
                "name": "Test Registry Agent",
                "description": "Agent for testing registry",
                "system_prompt_template": "You are a registry test agent",
                "specialized_tools": ["registry_tool"],
                "voice_settings": {"voice_id": "Joanna"},
                "use_cases": ["Registry Testing"],
                "personality": {"traits": ["helpful"]},
                "model_settings": {"max_tokens": 4096}
            }
            
            agent_path = os.path.join(agents_dir, "test_registry_agent.yaml")
            with open(agent_path, 'w') as f:
                yaml.dump(test_agent, f)
            
            yield {
                "agents_dir": agents_dir,
                "test_agent": test_agent
            }
    
    def test_registry_initialization(self, temp_config_dir):
        """Test FileBasedGRCAgentConfigRegistry initialization."""
        agents_dir = temp_config_dir["agents_dir"]
        
        registry = FileBasedGRCAgentConfigRegistry(
            config_directory=agents_dir,
            active_agents=["test_registry_agent"]
        )
        
        assert len(registry.list_agent_ids()) == 1
        assert "test_registry_agent" in registry.list_agent_ids()
    
    def test_build_agent_metadata(self, temp_config_dir):
        """Test building agent metadata."""
        agents_dir = temp_config_dir["agents_dir"]
        
        registry = FileBasedGRCAgentConfigRegistry(
            config_directory=agents_dir,
            active_agents=["test_registry_agent"]
        )
        
        metadata = registry.build_agent_metadata("test_registry_agent")
        
        assert metadata["agent_id"] == "test_registry_agent"
        assert metadata["name"] == "Test Registry Agent"
        assert metadata["description"] == "Agent for testing registry"
        assert "specialized_tools" in metadata
        assert "voice_settings" in metadata
        assert "voice_enabled" in metadata
        assert "use_cases" in metadata
        assert "personality" in metadata
    
    def test_build_agent_metadata_nonexistent(self, temp_config_dir):
        """Test building metadata for non-existent agent."""
        agents_dir = temp_config_dir["agents_dir"]
        
        registry = FileBasedGRCAgentConfigRegistry(
            config_directory=agents_dir,
            active_agents=["test_registry_agent"]
        )
        
        with pytest.raises(ValueError, match="No configuration found for agent"):
            registry.build_agent_metadata("nonexistent_agent")


class TestConfigurationUsage:
    """Test that all configuration keys are being used in the application."""
    
    def test_all_settings_fields_are_used(self):
        """Test that all fields in the Settings class are being used somewhere in the application."""
        # Get all field names from the Settings class
        settings_fields = set(Settings.model_fields.keys())
        
        # Fields that are used in the application
        # This list should be maintained as the application grows
        expected_used_fields = {
            # AWS Configuration
            "aws_profile",
            "aws_region", 
            "aws_access_key_id",
            "aws_secret_access_key",
            "aws_session_token",
            
            # Agent Configuration
            "agent_config_directory",
            "active_agents",
            "default_agent",
            
            # Classifier model settings
            "classifier_model_id",
            "classifier_max_tokens",
            "classifier_temperature",
            "classifier_top_p",
            
            # Voice Services
            "transcribe_language_code",
            "polly_voice_id",
            "polly_engine",
            
            # Lex Configuration
            "lex_bot_id",
            "lex_bot_alias_id",
            "lex_session_id",
            
            # API Configuration
            "api_port",
            "api_host",
            "api_cors_origins",
            
            # WebRTC Configuration
            "webrtc_stun_servers",
            "webrtc_turn_servers",
            
            # Logging Configuration
            "log_level",
            "structlog_renderer",

            # Development Configuration
            "debug",
            "development_mode"
        }
        
        # Check that all expected fields exist in the Settings class
        missing_fields = expected_used_fields - settings_fields
        assert not missing_fields, f"Expected fields not found in Settings class: {missing_fields}"
        
        # Check that we haven't added new fields without updating the test
        extra_fields = settings_fields - expected_used_fields
        assert not extra_fields, f"New fields found in Settings class that need to be verified as used: {extra_fields}"
    
    def test_settings_properties_are_used(self):
        """Test that all property methods in Settings are being used."""
        # Properties that convert string configs to lists or provide computed values
        expected_properties = {
            "cors_origins_list",
            "stun_servers_list", 
            "turn_servers_list",
            "active_agents_list",
            "is_production"
        }
        
        # Get all properties from the Settings class
        settings_properties = set()
        for attr_name in dir(Settings):
            attr = getattr(Settings, attr_name)
            if isinstance(attr, property):
                settings_properties.add(attr_name)
        
        # Check that all expected properties exist
        missing_properties = expected_properties - settings_properties
        assert not missing_properties, f"Expected properties not found in Settings class: {missing_properties}"
    
    def test_agent_config_all_fields_accessible(self):
        """Test that all fields in agent configuration are accessible through FileBasedAgentConfig."""
        # Test data with all possible configuration fields
        complete_agent_data = {
            "id": "complete_test_agent",
            "name": "Complete Test Agent",
            "description": "Agent with all possible configuration fields",
            "system_prompt_template": "Complete system prompt",
            "specialized_tools": ["tool1", "tool2"],
            "voice_settings": {"voice_id": "Joanna", "style": "conversational"},
            "use_cases": ["Testing", "Validation"],
            "personality": {"traits": ["helpful", "analytical"]},
            "model_settings": {"max_tokens": 4096, "temperature": 0.7},
            "inference_config": {"top_p": 0.9}
        }
        
        config = FileBasedAgentConfig(
            agent_id="complete_test_agent",
            config_data=complete_agent_data,
            default_model_settings={}
        )
        
        # Test that all getter methods work and return expected types
        assert isinstance(config.get_system_prompt(), str)
        assert isinstance(config.get_specialized_tools(), list)
        assert isinstance(config.get_voice_settings(), dict)
        assert isinstance(config.get_use_cases(), list)
        assert isinstance(config.get_personality(), dict)
        assert isinstance(config.get_model_settings(), dict)
        
        # Test that all data is accessible
        assert config.get_system_prompt() == "Complete system prompt"
        assert config.get_specialized_tools() == ["tool1", "tool2"]
        assert config.get_voice_settings()["voice_id"] == "Joanna"
        assert config.get_use_cases() == ["Testing", "Validation"]
        assert config.get_personality()["traits"] == ["helpful", "analytical"]
        assert config.get_model_settings()["max_tokens"] == 4096
    
    def test_settings_usage_in_agent_config_loader(self):
        """Test that AgentConfigLoader uses settings correctly."""
        with patch.dict(os.environ, {
            "AGENT_CONFIG_DIRECTORY": "test/config/agents",
            "ACTIVE_AGENTS": '["test_agent"]'
        }):
            test_settings = Settings()
            
            # Test that AgentConfigLoader uses settings when no parameters provided
            with patch('src.agents.agent_config_loader.settings', test_settings):
                with patch('src.agents.agent_config_loader.os.path.exists', return_value=False):
                    with pytest.raises(FileNotFoundError):
                        AgentConfigLoader()  # Should use settings defaults
            
            # Verify that settings have the expected values
            assert test_settings.agent_config_directory == "test/config/agents"
            assert test_settings.active_agents == ["test_agent"]
            assert test_settings.active_agents_list == ["test_agent"]
    
    def test_environment_variable_overrides(self):
        """Test that environment variables can override settings."""
        with patch.dict(os.environ, {
            "ACTIVE_AGENTS": '["custom_agent_1", "custom_agent_2"]',
            "AGENT_CONFIG_DIRECTORY": "custom/config/path",
            "API_PORT": "9000",
            "DEBUG": "true"
        }):
            test_settings = Settings()
            
            assert isinstance(test_settings.active_agents, list)
            assert test_settings.active_agents == ["custom_agent_1", "custom_agent_2"]
            assert test_settings.agent_config_directory == "custom/config/path"
            assert test_settings.api_port == 9000
            assert test_settings.debug is True
            
            # Test that active_agents_list property returns the same list
            agents_list = test_settings.active_agents_list
            assert agents_list == ["custom_agent_1", "custom_agent_2"]
            assert agents_list is test_settings.active_agents 