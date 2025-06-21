"""
AWS Configuration and Service Management.

This module handles AWS service configuration, credential validation,
and provides centralized access to AWS services using aws-vault for credential extraction.
"""

import asyncio
import json
import subprocess
from typing import Optional, Dict, Any

import boto3
import structlog
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.session import get_session


class AWSConfig:
    """AWS configuration and service manager with shared aws-vault credential extraction."""
    
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
        
        # Cache for aws-vault sessions to avoid repeated credential extraction
        self._aws_vault_session = None
        self._aws_vault_credentials = None
        
        # Initialize session (will use aws-vault if profile is provided)
        if profile:
            self.session = self._create_aws_vault_session(profile, region)
        else:
            self.session = boto3.Session()
        
        # Ensure region is set
        if not self.session.region_name:
            self.session = self.session
    
    def _create_aws_vault_session(self, profile: str = "acl-playground", region_name: str = "us-west-2") -> boto3.Session:
        """
        Create a boto3 session using aws-vault credential extraction.
        
        This is the shared implementation used across all services that need AWS access.
        
        Args:
            profile: AWS profile name for aws-vault
            region_name: AWS region
            
        Returns:
            Configured boto3 session
            
        Raises:
            Exception: If credential extraction fails
        """
        if self._aws_vault_session and self._aws_vault_credentials:
            # Return cached session if available
            return self._aws_vault_session
            
        self.logger.info(f"Extracting credentials from aws-vault profile: {profile}")
        
        try:
            # Run aws-vault exec with --json flag to get credentials
            result = subprocess.run(
                f"aws-vault exec {profile} --json", 
                shell=True, 
                capture_output=True, 
                check=True,
                text=True
            )
            
            credentials = json.loads(result.stdout)
            
            self.logger.info(f"Successfully extracted credentials from aws-vault for profile: {profile}",
                           access_key_prefix=credentials['AccessKeyId'][:10],
                           session_token_prefix=credentials['SessionToken'][:20])
            
            # Create a session with the retrieved credentials
            session = boto3.session.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region_name
            )
            
            # Cache the session and credentials
            self._aws_vault_session = session
            self._aws_vault_credentials = credentials
            
            return session
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"aws-vault command failed: {e}")
            raise Exception(f"Failed to extract credentials from aws-vault: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse aws-vault JSON output: {e}")
            raise Exception(f"Invalid JSON from aws-vault: {e}")
        except Exception as e:
            self.logger.error(f"Failed to create AWS session with aws-vault: {e}")
            raise
    
    @classmethod
    def create_aws_vault_session(cls, profile: str = "acl-playground", region_name: str = "us-west-2") -> boto3.Session:
        """
        Class method to create an aws-vault session without instantiating AWSConfig.
        
        This is useful for services that just need a session without the full config object.
        
        Args:
            profile: AWS profile name for aws-vault
            region_name: AWS region
            
        Returns:
            Configured boto3 session
        """
        temp_config = cls(profile=profile, region=region_name)
        return temp_config.session
    
    @classmethod
    def create_aws_vault_client(cls, service_name: str, profile: str = "acl-playground", region_name: str = "us-west-2"):
        """
        Class method to create an AWS service client using aws-vault credentials.
        
        Args:
            service_name: AWS service name (e.g., 'polly', 'bedrock-runtime', 'transcribe')
            profile: AWS profile name for aws-vault
            region_name: AWS region
            
        Returns:
            Configured AWS service client
        """
        session = cls.create_aws_vault_session(profile, region_name)
        return session.client(service_name)
    
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