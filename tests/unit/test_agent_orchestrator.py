"""
Unit tests for the GRC Agent Squad.

Tests GRC agent functionality, selection logic, and orchestration capabilities.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from src.services.grc_agent_squad import GRCAgentSquad
from src.tools.tool_registry import ToolRegistry
from src.models.agent_models import AgentCapability


class TestGRCAgentSquad:
    """Test suite for GRCAgentSquad functionality."""
    
    def create_mock_response(self, response_text: str, agent_name: str = "GRC Agent Squad") -> Mock:
        """Create a mock response that matches agent-squad response structure."""
        mock_response = Mock()
        mock_response.output = response_text
        mock_response.streaming = False
        mock_response.metadata = Mock()
        mock_response.metadata.agent_name = agent_name
        return mock_response

    @pytest.fixture
    def tool_registry(self):
        """Create a mock tool registry."""
        registry = Mock(spec=ToolRegistry)
        registry.get_tools = Mock(return_value=[])
        registry.list_tools = Mock(return_value=[])
        registry.tools = {}  # Add tools attribute for get_available_tools test
        return registry

    @pytest.fixture
    def grc_squad(self, tool_registry):
        """Create a GRC Agent Squad instance."""
        squad = GRCAgentSquad(tool_registry=tool_registry)
        return squad

    @pytest.mark.asyncio
    async def test_list_agents(self, grc_squad):
        """Test listing all GRC agents."""
        agents = await grc_squad.list_agents()
        
        assert isinstance(agents, list)
        assert len(agents) == 4  # Should have 4 GRC agents
        
        # Verify all expected agents are present
        agent_personalities = [agent["agent_id"] for agent in agents]
        expected_personalities = [
                    "empathetic_interviewer_executive",
        "authoritative_compliance_executive",
        "analytical_risk_expert_executive",
        "strategic_governance_executive"
        ]
        
        for personality in expected_personalities:
            assert personality in agent_personalities

    @pytest.mark.asyncio
    async def test_agent_names_and_descriptions(self, grc_squad):
        """Test that agents have proper names and descriptions."""
        agents = await grc_squad.list_agents()
        
        # Check Emma - Information Collector
        emma = next((a for a in agents if a["agent_id"] == "empathetic_interviewer_executive"), None)
        assert emma is not None
        assert "Emma" in emma["name"]
        assert "Information Collector" in emma["name"] or "Senior Information Collector" in emma["name"]
        assert "empathetic" in emma["description"].lower() or "interview" in emma["description"].lower()

        # Check Dr. Morgan - Compliance Authority
        morgan = next((a for a in agents if a["agent_id"] == "authoritative_compliance_executive"), None)
        assert morgan is not None
        assert "Morgan" in morgan["name"]
        assert "Compliance" in morgan["name"]
        assert "compliance" in morgan["description"].lower() or "authority" in morgan["description"].lower()

        # Check Alex - Risk Expert
        alex = next((a for a in agents if a["agent_id"] == "analytical_risk_expert_executive"), None)
        assert alex is not None
        assert "Alex" in alex["name"]
        assert "Risk" in alex["name"]
        assert "risk" in alex["description"].lower() or "analytical" in alex["description"].lower()

        # Check Sam - Governance Strategist
        sam = next((a for a in agents if a["agent_id"] == "strategic_governance_executive"), None)
        assert sam is not None
        assert "Sam" in sam["name"]
        assert "Governance" in sam["name"]
        assert "governance" in sam["description"].lower() or "strategic" in sam["description"].lower()

    @pytest.mark.asyncio
    async def test_get_agent_info(self, grc_squad):
        """Test getting information about a specific agent."""
        # Test with empathetic interviewer
        agent_info = await grc_squad.get_agent_info("empathetic_interviewer_executive")
        
        assert agent_info is not None
        assert agent_info["agent_id"] == "empathetic_interviewer_executive"
        assert "Emma" in agent_info["name"]
        assert agent_info["agent_id"] == "empathetic_interviewer_executive"
        assert isinstance(agent_info["capabilities"], list)

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent_info(self, grc_squad):
        """Test getting info for a non-existent agent."""
        agent_info = await grc_squad.get_agent_info("non-existent-agent")
        assert agent_info is None

    @pytest.mark.asyncio
    async def test_process_request_interview_scenario(self, grc_squad):
        """Test processing a request that should go to the empathetic interviewer."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self.create_mock_response(
                "I'd be happy to help you with your compliance interview. Let's start with some basic questions about your current processes.",
                "Emma - Information Collector"
            )
            
            response = await grc_squad.process_request(
                user_input="I need help preparing for a compliance audit interview",
                session_id="test-session"
            )
            
            assert response["success"] is True
            assert "agent_response" in response
            assert "agent_selection" in response
            assert response["session_id"] == "test-session"
            
            # Verify the route_request was called with correct parameters
            mock_route.assert_called_once()
            call_args = mock_route.call_args[1]
            assert call_args["user_input"] == "I need help preparing for a compliance audit interview"
            assert call_args["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_process_request_compliance_scenario(self, grc_squad):
        """Test processing a request that should go to the compliance authority."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self.create_mock_response(
                "According to GDPR Article 32, you must implement appropriate technical and organizational measures...",
                "Dr. Morgan - Compliance Authority"
            )
            
            response = await grc_squad.process_request(
                user_input="What are the GDPR requirements for data security?",
                session_id="test-session"
            )
            
            assert response["success"] is True
            assert "GDPR" in response["agent_response"]["response"]

    @pytest.mark.asyncio
    async def test_process_request_risk_scenario(self, grc_squad):
        """Test processing a request that should go to the risk expert."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self.create_mock_response(
                "Let me analyze the risk factors in your scenario. First, we need to assess the likelihood and impact...",
                "Alex - Risk Analysis Expert"
            )
            
            response = await grc_squad.process_request(
                user_input="Can you help me assess the risks of implementing a new payment system?",
                session_id="test-session"
            )
            
            assert response["success"] is True
            assert "risk" in response["agent_response"]["response"].lower()

    @pytest.mark.asyncio
    async def test_process_request_governance_scenario(self, grc_squad):
        """Test processing a request that should go to the governance strategist."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self.create_mock_response(
                "For effective board governance, I recommend establishing clear committee structures...",
                "Sam - Governance Strategist"
            )
            
            response = await grc_squad.process_request(
                user_input="How should we structure our board committees for better governance?",
                session_id="test-session"
            )
            
            assert response["success"] is True
            assert "governance" in response["agent_response"]["response"].lower()

    @pytest.mark.asyncio
    async def test_get_squad_stats(self, grc_squad):
        """Test getting squad statistics."""
        stats = await grc_squad.get_squad_stats()
        
        assert isinstance(stats, dict)
        assert "total_agents" in stats
        assert stats["total_agents"] == 4
        assert "agent_types" in stats
        assert len(stats["agent_types"]) == 4

    @pytest.mark.asyncio
    async def test_get_available_tools(self, grc_squad):
        """Test getting available tools."""
        tools = grc_squad.get_available_tools()
        
        assert isinstance(tools, list)
        # Tools list might be empty in test environment, but should be a list

    @pytest.mark.asyncio
    async def test_process_request_error_handling(self, grc_squad):
        """Test error handling in request processing."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_route.side_effect = Exception("Test error")
            
            response = await grc_squad.process_request(
                user_input="Test message",
                session_id="test-session"
            )
            
            assert response["success"] is False
            assert "error" in response

    @pytest.mark.asyncio
    async def test_agent_capabilities(self, grc_squad):
        """Test that agents have appropriate capabilities."""
        agents = await grc_squad.list_agents()
        
        for agent in agents:
            assert "capabilities" in agent
            assert isinstance(agent["capabilities"], list)
            assert len(agent["capabilities"]) > 0
            
            # All GRC agents should have these basic capabilities
            capabilities = agent["capabilities"]
            assert "question_answering" in capabilities

    @pytest.mark.asyncio
    async def test_session_id_handling(self, grc_squad):
        """Test session ID handling in requests."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self.create_mock_response(
                "Test response",
                "Emma - Information Collector"
            )
            
            # Test with explicit session ID
            response1 = await grc_squad.process_request(
                user_input="Test message",
                session_id="custom-session-123"
            )
            
            assert response1["session_id"] == "custom-session-123"
            
            # Test with default session ID
            response2 = await grc_squad.process_request(
                user_input="Test message"
            )
            
            assert "session_id" in response2
            assert response2["session_id"] == "default"

    @pytest.mark.asyncio
    async def test_context_handling(self, grc_squad):
        """Test context handling in requests."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self.create_mock_response(
                "Test response with context",
                "Emma - Information Collector"
            )
            
            test_context = {"company": "ACME Corp", "industry": "Financial Services"}
            
            response = await grc_squad.process_request(
                user_input="Test message",
                session_id="test-session",
                context=test_context
            )
            
            assert response["success"] is True
            
            # Verify route_request was called with user_input and session_id
            # Note: Our current implementation doesn't pass context to agent-squad
            mock_route.assert_called_once()
            call_args = mock_route.call_args[1]
            assert call_args["user_input"] == "Test message"
            assert call_args["session_id"] == "test-session" 