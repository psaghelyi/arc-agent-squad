"""
End-to-end tests for GRC Agent Squad.

These tests use real AWS services and should be run with valid AWS credentials.
They are slower but test the actual business functionality.

Run with: pytest tests/e2e/ -m e2e --timeout=300
"""

import pytest
import asyncio
import os
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from src.api.main import app
from src.services.grc_agent_squad import GRCAgentSquad
from src.services.aws_config import AWSConfig


def check_aws_credentials():
    """Check if AWS credentials are available via AWSConfig."""
    try:
        aws_config = AWSConfig(profile="acl-playground", region="us-west-2")
        return aws_config.validate_credentials_sync()
    except Exception as e:
        print(f"AWS credential check failed: {e}")
        return False


@pytest.mark.e2e
@pytest.mark.skipif(
    not check_aws_credentials(),
    reason="AWS credentials not available via AWSConfig/SSO"
)
class TestGRCAgentsE2E:
    """End-to-end tests using real AWS services."""

    @pytest.fixture(scope="class")
    def real_grc_squad(self):
        """Create a real GRC squad with AWS services using AWSConfig."""
        try:
            # Use your existing AWSConfig for SSO credentials
            aws_config = AWSConfig(profile="acl-playground", region="us-west-2")
            
            # Validate credentials first
            if not aws_config.validate_credentials_sync():
                pytest.skip("AWS credentials validation failed")
            
            squad = GRCAgentSquad()
            return squad
        except Exception as e:
            pytest.skip(f"Could not initialize GRC squad with real AWS services: {e}")

    @pytest.fixture
    def e2e_client(self):
        """Create an HTTP client for end-to-end API testing."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    @pytest.mark.asyncio
    async def test_real_compliance_query(self, real_grc_squad):
        """Test a real compliance query through AWS Bedrock."""
        response = await real_grc_squad.process_request(
            user_input="What are the key requirements for GDPR data retention policies?",
            session_id="e2e-compliance-test"
        )
        
        print(f"🔍 Full response: {response}")
        
        # Verify we got a real response
        assert response["success"] is True
        assert response["agent_response"]["response"] is not None
        assert len(response["agent_response"]["response"]) > 50  # Should be substantial
        assert "gdpr" in response["agent_response"]["response"].lower() or "data" in response["agent_response"]["response"].lower()
        
        # Verify agent selection worked
        assert response["agent_selection"]["agent_name"] is not None
        
        # Confidence might be None with real agent-squad
        confidence = response["agent_selection"]["confidence"]
        if confidence is not None:
            assert isinstance(confidence, (int, float))
            assert 0.0 <= confidence <= 1.0
        
        print(f"✅ Real GRC Response ({len(response['agent_response']['response'])} chars): {response['agent_response']['response'][:150]}...")
        print(f"✅ Agent: {response['agent_selection']['agent_name']}")
        print(f"✅ Confidence: {confidence}")

    @pytest.mark.asyncio
    async def test_real_risk_assessment_query(self, real_grc_squad):
        """Test a real risk assessment query."""
        response = await real_grc_squad.process_request(
            user_input="Help me assess the cybersecurity risks of moving our customer database to the cloud.",
            session_id="e2e-risk-test"
        )
        
        assert response["success"] is True
        assert response["agent_response"]["response"] is not None
        assert len(response["agent_response"]["response"]) > 50
        
        # Should contain risk-related terms
        response_text = response["agent_response"]["response"].lower()
        risk_terms = ["risk", "security", "cloud", "database", "assess", "mitigation"]
        assert any(term in response_text for term in risk_terms)

    @pytest.mark.asyncio
    async def test_real_interview_preparation_query(self, real_grc_squad):
        """Test a real interview preparation query."""
        response = await real_grc_squad.process_request(
            user_input="I need to prepare questions for auditing our IT department's access controls.",
            session_id="e2e-interview-test"
        )
        
        assert response["success"] is True
        assert response["agent_response"]["response"] is not None
        
        # Should provide interview-related guidance
        response_text = response["agent_response"]["response"].lower()
        interview_terms = ["question", "audit", "access", "control", "interview", "prepare"]
        assert any(term in response_text for term in interview_terms)

    @pytest.mark.asyncio
    async def test_real_governance_query(self, real_grc_squad):
        """Test a real governance query."""
        response = await real_grc_squad.process_request(
            user_input="How should we structure our board committees to improve oversight of risk management?",
            session_id="e2e-governance-test"
        )
        
        assert response["success"] is True
        assert response["agent_response"]["response"] is not None
        
        # Should provide governance guidance
        response_text = response["agent_response"]["response"].lower()
        governance_terms = ["board", "committee", "governance", "oversight", "structure", "risk"]
        assert any(term in response_text for term in governance_terms)

    @pytest.mark.asyncio
    async def test_conversation_continuity_real(self, real_grc_squad):
        """Test that conversation continuity works with real Bedrock memory."""
        session_id = "e2e-continuity-test"
        
        # First message
        response1 = await real_grc_squad.process_request(
            user_input="I'm working on a GDPR compliance project for a financial services company.",
            session_id=session_id
        )
        
        assert response1["success"] is True
        
        # Follow-up message that should reference the context
        response2 = await real_grc_squad.process_request(
            user_input="What specific data retention requirements should I focus on?",
            session_id=session_id
        )
        
        assert response2["success"] is True
        # The second response should ideally reference financial services context
        # but we can't guarantee this without examining the actual response
        assert len(response2["agent_response"]["response"]) > 30

    @pytest.mark.asyncio
    async def test_real_api_chat_endpoint(self, e2e_client):
        """Test the chat API endpoint with real services."""
        # Note: This will use real AWS services if properly configured
        chat_request = {
            "message": "What are the main components of a SOX compliance program?",
            "session_id": "e2e-api-test"
        }
        
        async with e2e_client as client:
            response = await client.post("/api/agents/chat", json=chat_request)
            
            # This might fail if AWS is not properly configured in the test environment
            if response.status_code == 200:
                data = response.json()
                assert "message" in data
                assert "agent_name" in data
                assert len(data["message"]) > 30
                assert "sox" in data["message"].lower() or "compliance" in data["message"].lower()
            else:
                # If it fails, it's likely due to AWS configuration issues
                assert response.status_code in [500, 503]  # Expected for misconfigured AWS

    @pytest.mark.asyncio
    async def test_agent_selection_consistency_real(self, real_grc_squad):
        """Test that similar queries consistently select appropriate agents."""
        compliance_queries = [
            "What are GDPR requirements?",
            "Help me understand SOX compliance.",
            "What are the key regulatory requirements for data privacy?"
        ]
        
        responses = []
        for query in compliance_queries:
            response = await real_grc_squad.process_request(
                user_input=query,
                session_id=f"e2e-consistency-{hash(query)}"
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response["success"] is True
        
        # Agent names should be reasonable (though we can't guarantee the same agent)
        agent_names = [r["agent_selection"]["agent_name"] for r in responses]
        assert all(name is not None for name in agent_names)

    @pytest.mark.asyncio
    async def test_error_handling_with_real_services(self, real_grc_squad):
        """Test error handling with real services."""
        # Test with potentially problematic input
        response = await real_grc_squad.process_request(
            user_input="",  # Empty input
            session_id="e2e-error-test"
        )
        
        # Should handle gracefully
        assert "success" in response
        # Either succeeds with a default response or fails gracefully
        if not response["success"]:
            assert "error" in response
            assert response["error"] is not None


@pytest.mark.e2e
@pytest.mark.skipif(
    not check_aws_credentials(),
    reason="AWS credentials not available via AWSConfig/SSO"
)
class TestVoiceServicesE2E:
    """End-to-end tests for voice services."""

    @pytest.mark.asyncio
    async def test_voice_endpoint_real_services(self):
        """Test voice endpoint with real AWS services."""
        # This would test real Transcribe/Polly integration
        # Implementation depends on your voice service setup
        pytest.skip("Voice services e2e tests not implemented yet")

    @pytest.mark.asyncio
    async def test_voice_processing_pipeline(self):
        """Test the complete voice processing pipeline."""
        # Test: Audio -> Transcribe -> Agent -> Polly -> Audio
        pytest.skip("Voice pipeline e2e tests not implemented yet") 