"""
AWS Configuration and Service Management.

This module handles AWS service configuration, credential validation,
and provides centralized access to AWS services.
"""

import asyncio
from typing import Optional

import boto3
import structlog
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.session import get_session


class AWSConfig:
    """AWS configuration and service manager."""
    
    def __init__(self, profile: Optional[str] = None, region: str = "us-west-2"):
        """
        Initialize AWS configuration.
        
        Args:
            profile: AWS profile name (for aws-vault or local development)
            region: AWS region
        """
        self.profile = profile
        self.region = region
        self.logger = structlog.get_logger(__name__)
        
        # Initialize session
        if profile:
            self.session = boto3.Session(profile_name=profile)
        else:
            self.session = boto3.Session()
        
        # Ensure region is set
        if not self.session.region_name:
            self.session = self.session
    
    def get_session(self):
        """
        Get the boto3 session.
        
        Returns:
            The boto3 session instance
        """
        return self.session
    
    def validate_credentials_sync(self) -> bool:
        """
        Validate AWS credentials synchronously by making a simple STS call.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            sts_client = self.session.client('sts', region_name=self.region)
            response = sts_client.get_caller_identity()
            self.logger.info(
                "AWS credentials validated",
                account_id=response.get('Account'),
                user_arn=response.get('Arn'),
                region=self.region
            )
            return True
        except (NoCredentialsError, ClientError) as e:
            self.logger.error("AWS credentials validation failed", error=str(e))
            return False
    
    async def validate_credentials(self) -> bool:
        """
        Validate AWS credentials by making a simple STS call.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            sts_client = self.session.client('sts', region_name=self.region)
            response = sts_client.get_caller_identity()
            self.logger.info(
                "AWS credentials validated",
                account_id=response.get('Account'),
                user_arn=response.get('Arn'),
                region=self.region
            )
            return True
        except (NoCredentialsError, ClientError) as e:
            self.logger.error("AWS credentials validation failed", error=str(e))
            return False
    
    def get_bedrock_client(self):
        """Get a Bedrock client instance."""
        return self.session.client('bedrock', region_name=self.region)
    
    def get_bedrock_runtime_client(self):
        """Get a Bedrock Runtime client instance."""
        return self.session.client('bedrock-runtime', region_name=self.region)
    
    def get_transcribe_client(self):
        """Get a Transcribe client instance."""
        return self.session.client('transcribe', region_name=self.region)
    
    def get_polly_client(self):
        """Get a Polly client instance."""
        return self.session.client('polly', region_name=self.region)
    
    def get_lex_client(self):
        """Get a Lex Runtime V2 client instance."""
        return self.session.client('lexv2-runtime', region_name=self.region)
    
    def get_stepfunctions_client(self):
        """Get a Step Functions client instance."""
        return self.session.client('stepfunctions', region_name=self.region)
    
    def get_s3_client(self):
        """Get an S3 client instance."""
        return self.session.client('s3', region_name=self.region)
    
    def get_dynamodb_client(self):
        """Get a DynamoDB client instance."""
        return self.session.client('dynamodb', region_name=self.region)
    
    def get_lambda_client(self):
        """Get a Lambda client instance."""
        return self.session.client('lambda', region_name=self.region) 