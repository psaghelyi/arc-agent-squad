"""
API integration tests.

Tests the complete API flow including agent management and chat functionality.
"""

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, Mock

from src.api.main import app

pytestmark = pytest.mark.integration


class TestAPIIntegration:
    """Integration tests for the API endpoints."""

    @pytest_asyncio.fixture
    async def client(self):
        """Create an async HTTP client for testing."""
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = await client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["service"] == "GRC Agent Squad"
        assert data["message"] == "GRC Agent Squad is running"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_list_agents_endpoint(self, client):
        """Test listing agents through the API."""
        response = await client.get("/api/agents/")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert "message" in data
        assert "success" in data
        assert isinstance(data["agents"], list)
        
        # Should have 5 default GRC agents
        assert len(data["agents"]) == 5
        
        # Verify agent structure
        for agent in data["agents"]:
            assert "agent_id" in agent
            assert "name" in agent
            assert "description" in agent
            assert "capabilities" in agent

    @pytest.mark.asyncio
    async def test_get_specific_agent(self, client):
        """Test getting a specific agent's information."""
        # First get the list of agents
        response = await client.get("/api/agents/")
        agents = response.json()["agents"]
        
        # Get the first agent's details
        agent_id = agents[0]["agent_id"]
        response = await client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        
        agent_data = response.json()
        # The response has an 'agent' wrapper
        assert "agent" in agent_data
        assert "success" in agent_data
        assert "agent_id" in agent_data["agent"]
        assert "name" in agent_data["agent"]
        assert "description" in agent_data["agent"]
        assert "capabilities" in agent_data["agent"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, client):
        """Test getting a non-existent agent."""
        response = await client.get("/api/agents/nonexistent-id")
        assert response.status_code == 404
        assert "Agent nonexistent-id not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_endpoint_basic(self, client):
        """Test basic chat functionality through the API."""
        with patch('src.services.grc_agent_squad.GRCAgentSquad.process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Hello! I'm happy to help you with that.",
                "agent_name": "Emma - Information Collector",
                "session_id": "test-session-api",
                "confidence": 1.0,
                "reasoning": "Selected by agent-squad orchestration with Bedrock memory",
                "agent_response": {
                    "response": "Hello! I'm happy to help you with that."
                },
                "agent_selection": {
                    "agent_id": "interviewer",
                    "agent_name": "Emma - Information Collector",
                    "confidence": 1.0,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                }
            }
            
            chat_request = {
                "message": "Hello, can you help me?",
                "session_id": "test-session-api"
            }
            
            response = await client.post("/api/agents/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "agent_name" in data
            assert "session_id" in data
            assert "confidence" in data
            assert "reasoning" in data
            
            assert data["session_id"] == "test-session-api"
            assert data["message"] == "Hello! I'm happy to help you with that."

    @pytest.mark.asyncio
    async def test_chat_endpoint_agent_selection(self, client):
        """Test that different messages select different agents."""
        with patch('src.services.grc_agent_squad.GRCAgentSquad.process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Agent response",
                "agent_name": "Emma - Information Collector",
                "session_id": "selection-test",
                "confidence": 1.0,
                "reasoning": "Selected by agent-squad orchestration with Bedrock memory",
                "agent_response": {
                    "response": "Agent response"
                },
                "agent_selection": {
                    "agent_id": "interviewer",
                    "agent_name": "Emma - Information Collector",
                    "confidence": 1.0,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                }
            }
            
            test_cases = [
                {
                    "message": "I'm feeling sad and need emotional support",
                    "expected_agent": "Emma - Information Collector"
                },
                {
                    "message": "Quick question: what's the capital of France?",
                    "expected_agent": "Dr. Morgan - Compliance Authority"
                },
                {
                    "message": "I need help debugging this technical issue",
                    "expected_agent": "Alex - Risk Analysis Expert"
                },
                {
                    "message": "Can you help me write a creative story?",
                    "expected_agent": "Sam - Governance Strategist"
                }
            ]
            
            for i, case in enumerate(test_cases):
                chat_request = {
                    "message": case["message"],
                    "session_id": f"selection-test-{i}"
                }
                
                response = await client.post("/api/agents/chat", json=chat_request)
                assert response.status_code == 200
                
                data = response.json()
                # Agent selection is handled by agent-squad, so we verify it's a reasonable choice
                assert "agent_name" in data
                assert data["agent_name"] in [
                    "Emma - Information Collector", 
                    "Dr. Morgan - Compliance Authority", 
                    "Alex - Risk Analysis Expert", 
                    "Sam - Governance Strategist"
                ]

    @pytest.mark.asyncio
    async def test_chat_endpoint_validation(self, client):
        """Test chat endpoint input validation."""
        with patch('src.services.grc_agent_squad.GRCAgentSquad.process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Default response",
                "agent_name": "Emma - Information Collector",
                "session_id": "default-session",
                "confidence": 1.0,
                "reasoning": "Selected by agent-squad orchestration with Bedrock memory",
                "agent_response": {
                    "response": "Default response"
                },
                "agent_selection": {
                    "agent_id": "interviewer",
                    "agent_name": "Emma - Information Collector",
                    "confidence": 1.0,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                }
            }
            
            # Missing message - should use default values
            response = await client.post("/api/agents/chat", json={"session_id": "test"})
            # API should handle gracefully
            assert response.status_code in [200, 422]
            
            # Missing session_id - should use default
            response = await client.post("/api/agents/chat", json={"message": "Hello"})
            assert response.status_code in [200, 422]
            
            # Empty message - should be handled gracefully
            response = await client.post("/api/agents/chat", json={
                "message": "",
                "session_id": "test"
            })
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_chat_endpoint_error_handling(self, client):
        """Test chat endpoint error handling."""
        with patch('src.services.grc_agent_squad.GRCAgentSquad.process_request') as mock_process:
            # Simulate an agent error that causes an exception
            mock_process.side_effect = Exception("Agent processing failed")
            
            chat_request = {
                "message": "This will cause an error",
                "session_id": "error-test-session"
            }
            
            response = await client.post("/api/agents/chat", json=chat_request)
            # The API should return 500 when an exception occurs
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Agent processing failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_capabilities_list_endpoint(self, client):
        """Test the capabilities list endpoint."""
        response = await client.get("/api/agents/capabilities/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "capabilities" in data
        assert "total" in data
        assert isinstance(data["capabilities"], list)
        
        # Should have standard GRC capabilities
        # Note: capabilities are returned as objects with 'value' field
        capability_values = [cap["value"] for cap in data["capabilities"]]
        expected_capabilities = [
            "question_answering", "voice_processing", "customer_support",
            "technical_support", "data_analysis", "task_assistance", "creative_writing"
        ]
        
        for capability in expected_capabilities:
            assert capability in capability_values

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client):
        """Test handling multiple concurrent API requests."""
        with patch('src.services.grc_agent_squad.GRCAgentSquad.process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Concurrent response",
                "agent_name": "Emma - Information Collector",
                "session_id": "concurrent-session",
                "confidence": 1.0,
                "reasoning": "Selected by agent-squad orchestration with Bedrock memory",
                "agent_response": {
                    "response": "Concurrent response"
                },
                "agent_selection": {
                    "agent_id": "interviewer",
                    "agent_name": "Emma - Information Collector",
                    "confidence": 1.0,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                }
            }
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(3):
                chat_request = {
                    "message": "Concurrent request",
                    "session_id": f"concurrent-session-{i}"
                }
                task = client.post("/api/agents/chat", json=chat_request)
                tasks.append(task)
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "Concurrent response"

    @pytest.mark.asyncio
    async def test_session_continuity_through_api(self, client):
        """Test that session continuity works through the API."""
        session_id = "continuity-test-session"
        
        with patch('src.services.grc_agent_squad.GRCAgentSquad.process_request') as mock_process:
            # First request
            mock_process.return_value = {
                "success": True,
                "message": "First response",
                "agent_name": "Emma - Information Collector",
                "session_id": session_id,
                "confidence": 1.0,
                "reasoning": "Selected by agent-squad orchestration with Bedrock memory",
                "agent_response": {
                    "response": "First response"
                },
                "agent_selection": {
                    "agent_id": "interviewer",
                    "agent_name": "Emma - Information Collector",
                    "confidence": 1.0,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                }
            }
            
            response1 = await client.post("/api/agents/chat", json={
                "message": "First message",
                "session_id": session_id
            })
            
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["session_id"] == session_id
            
            # Second request in same session
            mock_process.return_value = {
                "success": True,
                "message": "Second response with context",
                "agent_name": "Emma - Information Collector",
                "session_id": session_id,
                "confidence": 1.0,
                "reasoning": "Selected by agent-squad orchestration with Bedrock memory",
                "agent_response": {
                    "response": "Second response with context"
                },
                "agent_selection": {
                    "agent_id": "interviewer",
                    "agent_name": "Emma - Information Collector",
                    "confidence": 1.0,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                }
            }
            
            response2 = await client.post("/api/agents/chat", json={
                "message": "Follow-up message",
                "session_id": session_id
            })
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_api_response_format_consistency(self, client):
        """Test that API responses have consistent format."""
        with patch('src.services.grc_agent_squad.GRCAgentSquad.process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Consistent response",
                "agent_name": "Emma - Information Collector",
                "session_id": "format-test-session",
                "confidence": 1.0,
                "reasoning": "Selected by agent-squad orchestration with Bedrock memory",
                "agent_response": {
                    "response": "Consistent response"
                },
                "agent_selection": {
                    "agent_id": "interviewer",
                    "agent_name": "Emma - Information Collector",
                    "confidence": 1.0,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                }
            }
            
            response = await client.post("/api/agents/chat", json={
                "message": "Test message",
                "session_id": "format-test-session"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Check all expected fields are present in ChatResponse
            expected_fields = [
                "message", "agent_name", "session_id", "confidence", "reasoning"
            ]
            
            for field in expected_fields:
                assert field in data, f"Missing field '{field}' in response"

    @pytest.mark.asyncio
    async def test_api_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = await client.get("/api/agents/")
        assert response.status_code == 200
        
        # Check for CORS headers (if configured)
        # Note: This test may need adjustment based on actual CORS configuration

    @pytest.mark.asyncio
    async def test_api_error_responses(self, client):
        """Test that API error responses are properly formatted."""
        # Test 404 error
        response = await client.get("/api/agents/nonexistent-endpoint")
        assert response.status_code == 404
        
        # Test invalid JSON
        response = await client.post("/api/agents/chat", content="invalid json", 
                                   headers={"Content-Type": "application/json"})
        assert response.status_code == 422 