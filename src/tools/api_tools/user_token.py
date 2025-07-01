"""
HighBond Token Exchange Tool

This tool allows agents to exchange a HighBond API token for a subdomain JWT,
which is required for authenticating with HighBond services.
"""

import structlog
import requests
import json
from typing import Dict, Any, Optional

# Import the agent-squad tools
from agent_squad.utils import AgentTool

# Import settings
from src.utils.settings import settings


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


def _highbond_token_exchange_func(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Exchange HighBond API token for subdomain JWT to authenticate with HighBond services.
    
    This function handles the token exchange process required to access HighBond APIs
    for governance, risk, and compliance data retrieval and management.
    
    Args:
        params: Parameters for the tool (not used as it uses environment variables)
        
    Returns:
        Dict containing the token exchange results
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
        return {
            "success": False,
            "error": f"Missing required HighBond settings: {', '.join(missing)}. Please make sure these are configured."
        }
    
    try:
        # Call the token exchange function
        result = exchange_highbond_token()
        
        if result is None:
            return {
                "success": False,
                "error": "Failed to exchange HighBond token. Check the logs for details."
            }
        
        return {
            "success": True,
            "token_info": result,
            "message": "Successfully exchanged HighBond token for subdomain JWT"
        }
        
    except Exception as e:
        logger.error("Error executing HighBond Token Exchange Tool", error=str(e))
        return {
            "success": False,
            "error": f"An error occurred during token exchange: {str(e)}"
        }


# global variable to expose the tool
highbond_token_exchange_api_tool = AgentTool(
    name="highbond_token_exchange_api_tool",
    description="Exchange HighBond Application token for subdomain JWT to authenticate with HighBond API",
    func=_highbond_token_exchange_func
)
