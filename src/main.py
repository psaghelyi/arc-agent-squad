#!/usr/bin/env python3
"""
GRC Agent Squad - Main Application Entry Point

This is the main entry point for the GRC Agent Squad application specialized
for Governance, Risk Management, and Compliance using AWS services and the agent-squad framework.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.main import app
from src.services.aws_config import AWSConfig
from src.services.logger import setup_logging
from src.utils.config import settings


def main() -> None:
    """Main application entry point."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = structlog.get_logger(__name__)
    
    try:
        # Load configuration (using global settings instance)
        logger.info("Application starting", version="0.1.0", debug=settings.debug, development_mode=settings.development_mode)
        
        # Initialize AWS configuration (for reference only)
        # Note: Services use programmatic credential extraction via aws-vault
        aws_config = AWSConfig(
            profile=settings.aws_profile,
            region=settings.aws_region
        )
        
        # Skip credential validation - services handle their own credentials
        # using programmatic aws-vault extraction which is more reliable
        logger.info("AWS credential validation skipped - services use programmatic extraction")
        
        # Use the configured application
        # app is already imported and configured
        
        # Start the application based on mode
        if settings.development_mode:
            logger.info("Starting in development mode")
            import uvicorn
            uvicorn.run(
                "src.api.main:app",  # Use import string for reload to work
                host=settings.api_host,
                port=settings.api_port,
                reload=True,
                log_config=None  # Use our custom logging
            )
        else:
            logger.info("Starting in production mode")
            # For production, we'll use gunicorn or similar
            # This is mainly for local testing
            import uvicorn
            uvicorn.run(
                app,
                host=settings.api_host,
                port=settings.api_port,
                log_config=None
            )
    
    except Exception as e:
        logger.error("Application startup failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 