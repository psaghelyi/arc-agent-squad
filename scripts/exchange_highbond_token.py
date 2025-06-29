#!/usr/bin/env python3
"""
Exchange HighBond API token for subdomain JWT
Usage: Ensure HIGHBOND_ORG_ID and HIGHBOND_API_TOKEN are set in environment
"""

import os
import sys
import requests
import json
from typing import Optional

# Add the project root to the Python path if running as a script
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

try:
    from src.utils.settings import settings
except ImportError:
    # Fallback to environment variables if running outside the main project structure
    settings = None


def exchange_highbond_token() -> Optional[dict]:
    """
    Exchange HighBond API token for subdomain JWT
    
    Returns:
        dict: Response from the API or None if error
    """
    # Get configuration from settings or environment variables
    if settings:
        # Get values from settings
        org_id = settings.highbond_org_id
        api_path = settings.highbond_api_path
        api_token = settings.highbond_api_token
    else:
        # Fallback to environment variables
        org_id = os.getenv('HIGHBOND_ORG_ID')
        api_path = os.getenv('HIGHBOND_API_PATH')
        api_token = os.getenv('HIGHBOND_API_TOKEN')
    
    if not org_id:
        print("Error: HIGHBOND_ORG_ID setting is not configured", file=sys.stderr)
        return None
        
    if not api_token:
        print("Error: HIGHBOND_API_TOKEN setting is not configured", file=sys.stderr)
        return None
    
    if not api_path:
        print("Error: HIGHBOND_API_PATH setting is not configured", file=sys.stderr)
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
        
        # Print the response
        if response.status_code == 200:
            api_result = response.json()
            if __name__ == "__main__":
                print(json.dumps(api_result, indent=2))
            return api_result
        else:
            print(f"Error: HTTP {response.status_code}", file=sys.stderr)
            print(f"Response: {response.text}", file=sys.stderr)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}", file=sys.stderr)
        if response:
            print(f"Raw response: {response.text}", file=sys.stderr)
        return None


if __name__ == "__main__":
    api_response = exchange_highbond_token()
    if api_response is None:
        sys.exit(1)
