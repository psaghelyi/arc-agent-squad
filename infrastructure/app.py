#!/usr/bin/env python3
"""
AWS CDK application for Voice Agent Swarm infrastructure.
"""

import os

import aws_cdk as cdk

from stacks.voice_agent_stack import VoiceAgentStack


def main():
    """Main CDK application entry point."""
    app = cdk.App()
    
    # Get environment configuration
    env = cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-west-2')
    )
    
    # Create the main voice agent stack
    VoiceAgentStack(
        app, 
        "VoiceAgentSwarmStack",
        env=env,
        description="Voice-enabled AI agent swarm using AWS services"
    )
    
    app.synth()


if __name__ == "__main__":
    main() 