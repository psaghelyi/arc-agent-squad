"""
Configuration settings for the Voice Agent Swarm application.

This module handles all configuration through environment variables using Pydantic.
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = "development"
    debug: bool = False
    development_mode: bool = True  # Default to True for development
    
    # AWS Configuration
    aws_profile: str = "acl-playground"
    aws_region: str = "us-west-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    skip_aws_validation: bool = False  # Skip AWS validation for local dev
    
    # Bedrock Configuration
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_streaming_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Voice Services Configuration
    transcribe_language_code: str = "en-US"
    polly_voice_id: str = "Joanna"
    polly_engine: str = "neural"
    
    # Lex Configuration
    lex_bot_id: Optional[str] = None
    lex_bot_alias_id: str = "TSTALIASID"
    lex_session_id: str = "test-session"
    
    # Redis Configuration (for memory/state)
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    
    # API Configuration
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    api_cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # WebRTC Configuration
    webrtc_stun_servers: str = "stun:stun.l.google.com:19302"
    webrtc_turn_servers: Optional[str] = None
    
    # Logging Configuration
    log_level: str = "INFO"
    log_renderer: str = "json"
    enable_structured_logging: bool = True
    
    # Security Configuration
    cors_allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allowed_headers: List[str] = ["*"]
    
    # Agent Configuration
    max_concurrent_agents: int = 10
    agent_timeout_seconds: int = 300
    memory_retention_hours: int = 24
    
    def model_post_init(self, __context) -> None:
        """Post-initialization to set development mode based on environment."""
        if self.environment.lower() in ["development", "dev", "local"]:
            self.development_mode = True
        else:
            self.development_mode = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False 