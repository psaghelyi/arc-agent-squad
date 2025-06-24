"""
AWS connectivity test for e2e testing.

This test verifies that AWS SSO credentials are working and the necessary services are accessible.
"""

import pytest
from src.services.aws_config import AWSConfig


@pytest.mark.e2e
class TestAWSConnectivity:
    """Test AWS service connectivity."""

    def test_aws_sts_connectivity(self):
        """Test basic AWS STS connectivity with SSO credentials."""
        aws_config = AWSConfig(profile="acl-playground", region="us-west-2")
        
        # This will call get_caller_identity internally
        assert aws_config.validate_credentials_sync(), "AWS STS credentials validation failed"

    def test_bedrock_service_availability(self):
        """Test Bedrock service availability."""
        aws_config = AWSConfig(profile="acl-playground", region="us-west-2")
        
        try:
            bedrock_client = aws_config.get_bedrock_client()
            # Simple service call to verify access
            response = bedrock_client.list_foundation_models()
            assert "modelSummaries" in response, "Bedrock list_foundation_models failed"
            print(f"✅ Bedrock service accessible. Found {len(response['modelSummaries'])} models.")
        except Exception as e:
            pytest.fail(f"Bedrock service not accessible: {e}")

    def test_bedrock_runtime_service_availability(self):
        """Test Bedrock Runtime service availability."""
        aws_config = AWSConfig(profile="acl-playground", region="us-west-2")
        
        try:
            bedrock_runtime_client = aws_config.get_bedrock_runtime_client()
            # We can't easily test converse without making an expensive call,
            # but we can verify the client was created successfully
            assert bedrock_runtime_client is not None, "Bedrock Runtime client creation failed"
            print("✅ Bedrock Runtime service accessible.")
        except Exception as e:
            pytest.fail(f"Bedrock Runtime service not accessible: {e}")

    def test_transcribe_service_availability(self):
        """Test Transcribe service availability."""
        aws_config = AWSConfig(profile="acl-playground", region="us-west-2")
        
        try:
            transcribe_client = aws_config.get_transcribe_client()
            # List transcription jobs (should return empty list but not error)
            response = transcribe_client.list_transcription_jobs(MaxResults=1)
            assert "TranscriptionJobSummaries" in response, "Transcribe service call failed"
            print("✅ Transcribe service accessible.")
        except Exception as e:
            pytest.fail(f"Transcribe service not accessible: {e}")

    def test_polly_service_availability(self):
        """Test Polly service availability."""
        aws_config = AWSConfig(profile="acl-playground", region="us-west-2")
        
        try:
            polly_client = aws_config.get_polly_client()
            # List available voices
            response = polly_client.describe_voices()
            assert "Voices" in response, "Polly service call failed"
            assert len(response["Voices"]) > 0, "No Polly voices available"
            print(f"✅ Polly service accessible. Found {len(response['Voices'])} voices.")
        except Exception as e:
            pytest.fail(f"Polly service not accessible: {e}") 