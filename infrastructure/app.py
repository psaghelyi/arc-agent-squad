#!/usr/bin/env python3
"""
AWS CDK application for GRC Agent Squad infrastructure.
"""

import os

import aws_cdk as cdk

from stacks.grc_agent_stack import GRCAgentStack


def main():
    """Main CDK application entry point."""
    app = cdk.App()
    
    # Get environment configuration
    env = cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT', '891067072053'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-west-2')
    )
    
    # Create the main GRC agent squad stack
    GRCAgentStack(
        app, 
        "GRCAgentSquadStack",
        env=env,
        description="GRC Agent Squad - AI agents specialized for Governance, Risk Management, and Compliance"
    )
    
    app.synth()


if __name__ == "__main__":
    main() 