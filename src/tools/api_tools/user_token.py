"""
HighBond Token Exchange Tool

This tool allows agents to exchange a HighBond API token for a subdomain JWT,
which is required for authenticating with HighBond services.
"""

import structlog
import requests
import json
import os
import yaml
from typing import Dict, Any, Optional, Union

# Import the agent-squad tools
from agent_squad.utils import AgentTool

# Import settings
from src.utils.settings import settings


def _get_tool_config(tool_name: str) -> Dict[str, Any]:
    """
    Get tool configuration from YAML file directly.
    
    Args:
        tool_name: Name of the tool to get configuration for
        
    Returns:
        Tool configuration dictionary or empty dict if not found
    """
    logger = structlog.get_logger(__name__)
    
    # Determine the path to the tools.yaml file
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        'config', 'common', 'tools.yaml'
    )
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            if isinstance(config, dict) and 'tools' in config:
                tool_definitions = config['tools']
                if tool_name in tool_definitions:
                    return tool_definitions[tool_name]
    except Exception as e:
        logger.error(f"Error loading tool configuration: {e}")
    
    return {}


def exchange_highbond_token() -> Optional[dict]:
    """
    Exchange HighBond API token for subdomain JWT
    
    Returns:
        dict: Response from the API or None if error
    """
    logger = structlog.get_logger(__name__)
    
    # Get configuration from settings
    org_id = settings.highbond_org_id
    api_path = settings.highbond_api_path
    api_token = settings.highbond_api_token
    
    if not org_id:
        logger.error("Error: highbond_org_id setting is not configured")
        return None
        
    if not api_token:
        logger.error("Error: highbond_api_token setting is not configured")
        return None
    
    if not api_path:
        logger.error("Error: highbond_api_path setting is not configured")
        return None
    
    # Prepare the request
    url = f"{api_path}/api/token_info/subdomain_jwt?org_id={org_id}"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/vnd.api+json",
        "Target-METHOD": "POST",
        "Target-URL": ""
    }
    
    response = None
    try:
        # Make the POST request with empty JSON body (30 second timeout)
        response = requests.post(url, headers=headers, json={}, timeout=30)
        
        # Process the response
        if response.status_code == 200:
            api_result = response.json()
            return api_result
        else:
            logger.error(f"Error: HTTP {response.status_code}", response_text=response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}", raw_response=response.text if response else None)
        return None


def _highbond_token_exchange_func(params: Dict[str, Any]) -> str:
    """
    Exchange HighBond API token for subdomain JWT to authenticate with HighBond services.
    
    This function handles the token exchange process required to access HighBond APIs
    for governance, risk, and compliance data retrieval and management.
    
    Args:
        params: Parameters for the tool (not used as it uses environment variables)
        
    Returns:
        String containing the token exchange result or error message
    """
    logger = structlog.get_logger(__name__)
    logger.info("Executing HighBond Token Exchange Tool")
    
    # Validate settings before execution
    missing = []
    if not settings.highbond_org_id:
        missing.append("highbond_org_id")
    if not settings.highbond_api_path:
        missing.append("highbond_api_path")
    if not settings.highbond_api_token:
        missing.append("highbond_api_token")
        
    if missing:
        error_message = f"ERROR: Missing required HighBond settings: {', '.join(missing)}. Please make sure these are configured."
        logger.error(error_message)
        return error_message
    
    try:
        # Call the token exchange function
        result = exchange_highbond_token()
        
        if result is None:
            error_message = "ERROR: Failed to exchange HighBond token. Check the logs for details."
            logger.error(error_message)
            return error_message
        
        # Format the result as a clean plain text string (no Markdown)
        token_value = result.get('token', 'No token found')
        token_preview = f"{token_value[:20]}...{token_value[-20:]}" if len(token_value) > 40 else token_value
        
        success_message = (
            "[TOKEN EXCHANGE SUCCESSFUL]\n\n"
            f"HighBond JWT Token: {token_preview}\n\n"
            "Token Usage Information:\n"
            "- Use this JWT token to authenticate with HighBond API endpoints\n"
            "- The token is configured for your HighBond subdomain\n"
            "- Include it in API requests with header: Authorization: Bearer <token>\n\n"
            "The token is ready for use with HighBond API operations."
        )
        
        logger.info("Token exchange successful")
        return success_message
        
    except Exception as e:
        error_message = f"ERROR: An error occurred during token exchange: {str(e)}"
        logger.error(error_message, error=str(e))
        return error_message


# Get tool configuration from YAML directly
tool_name = "highbond_token_exchange_api_tool"
tool_config = _get_tool_config(tool_name)

# Create the tool using configuration from YAML if available
# IMPORTANT: Use the exact tool_name as the name parameter to match what agents expect
highbond_token_exchange_api_tool = AgentTool(
    name=tool_name,  # Use the exact name expected by agent configurations
    description=tool_config.get("description", "Exchange HighBond Application token for subdomain JWT to authenticate with HighBond API"),
    func=_highbond_token_exchange_func
)
