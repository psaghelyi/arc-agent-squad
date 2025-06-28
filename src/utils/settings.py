"""
Configuration settings for the GRC Agent Squad application.

This module handles all configuration through environment variables using Pydantic.
All important parameters can be overwritten with environment variables and have sensible defaults.
"""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables with fallback defaults."""
    
    # AWS Configuration - Critical for AWS services
    aws_profile: str = Field(default="acl-playground", description="AWS Profile to use")
    aws_region: str = Field(default="us-west-2", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    aws_session_token: Optional[str] = Field(default=None, description="AWS Session Token")
    
    # Agent Configuration - Dynamic Squad Composition
    agent_config_directory: str = Field(
        default="config/agents", 
        description="Directory containing individual agent configuration files"
    )
    active_agents: List[str] = Field(
        default=["supervisor_grc", 
                "empathetic_interviewer_executive", 
                "authoritative_compliance_executive", 
                "analytical_risk_expert_executive", 
                "strategic_governance_executive"],
        description="List of agent IDs to include in the squad"
    )
    default_agent: str = Field(
        default="supervisor_grc",
        description="Default agent to use when no specific agent is selected"
    )
    
    # Classifier model settings
    classifier_model_id: str = Field(
        default="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        description="Model ID for agent classifier/orchestrator"
    )
    classifier_max_tokens: int = Field(
        default=4096, 
        description="Maximum tokens for classifier/orchestrator responses"
    )
    classifier_temperature: float = Field(
        default=0.5, 
        description="Temperature for classifier/orchestrator"
    )
    classifier_top_p: float = Field(
        default=0.9,
        description="Top P for classifier/orchestrator"
    )
    
    # Voice Services Configuration - Speech processing
    transcribe_language_code: str = Field(default="en-US", description="Language code for transcription")
    polly_voice_id: str = Field(default="Joanna", description="Polly voice ID for TTS")
    polly_engine: str = Field(default="neural", description="Polly engine type")
    
    # Lex Configuration - Dialog management
    lex_bot_id: Optional[str] = Field(default=None, description="Lex Bot ID (required for production)")
    lex_bot_alias_id: str = Field(default="TSTALIASID", description="Lex Bot Alias ID")
    lex_session_id: str = Field(default="test-session", description="Lex Session ID")
    
    # Memory Configuration - Handled by Bedrock built-in memory
    
    # API Configuration - Web server settings
    api_port: int = Field(default=8000, description="API server port")
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="CORS allowed origins (comma-separated)"
    )
    
    # WebRTC Configuration - Real-time communication
    webrtc_stun_servers: str = Field(
        default="stun:stun.l.google.com:19302",
        description="STUN servers for WebRTC"
    )
    webrtc_turn_servers: Optional[str] = Field(default=None, description="TURN servers for WebRTC")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    structlog_renderer: str = Field(default="json", description="Structured logging renderer")
    
    # Development Configuration
    debug: bool = Field(default=False, description="Enable debug mode")
    development_mode: bool = Field(default=True, description="Enable development mode")  # Default to development
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list."""
        return [origin.strip() for origin in str(self.api_cors_origins).split(",")]
    
    @property
    def stun_servers_list(self) -> List[str]:
        """Convert STUN servers string to list."""
        return [server.strip() for server in str(self.webrtc_stun_servers).split(",")]
    
    @property
    def turn_servers_list(self) -> List[str]:
        """Convert TURN servers string to list."""
        if self.webrtc_turn_servers:
            return [server.strip() for server in str(self.webrtc_turn_servers).split(",")]
        return []
    
    @property
    def active_agents_list(self) -> List[str]:
        """Return the active agents list."""
        return self.active_agents
    

    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        # Explicitly check for production environment variables
        env_production = os.getenv("ENVIRONMENT", "").lower() in ["production", "prod"]
        explicit_production = os.getenv("PRODUCTION", "").lower() == "true"
        return (not self.development_mode and not self.debug) or env_production or explicit_production
    
    def validate_required_for_production(self) -> None:
        """Validate that required settings are provided for production."""
        if self.is_production:
            missing = []
            if not self.lex_bot_id:
                missing.append("LEX_BOT_ID")
            if not self.aws_access_key_id and not os.getenv("AWS_PROFILE"):
                missing.append("AWS_ACCESS_KEY_ID or AWS_PROFILE")
            
            if missing:
                raise ValueError(f"Missing required production settings: {', '.join(missing)}")
    
    def should_validate_production(self) -> bool:
        """Determine if we should validate production requirements."""
        # Skip validation for local development scenarios
        if self.development_mode or self.debug:
            return False
        
        # Only validate if explicitly marked as production
        env_production = os.getenv("ENVIRONMENT", "").lower() in ["production", "prod"]
        explicit_production = os.getenv("PRODUCTION", "").lower() == "true"
        skip_validation = os.getenv("SKIP_AWS_VALIDATION", "").lower() == "true"
        
        return (env_production or explicit_production) and not skip_validation
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global settings instance
settings = Settings()

# Only validate production requirements when explicitly required
if settings.should_validate_production():
    settings.validate_required_for_production()


# Usage example:
# from src.utils.settings import settings
# 
# print(f"API running on {settings.api_host}:{settings.api_port}")
# print(f"Using AWS region: {settings.aws_region}")
# print(f"CORS origins: {settings.cors_origins_list}")
# print(f"Is production: {settings.is_production}") 