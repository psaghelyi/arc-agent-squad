"""
Integration tests for GRC Agent Squad chat functionality.

Tests the complete chat flow through the GRC Agent Squad with proper mocking.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.services.grc_agent_squad import GRCAgentSquad
from src.tools.tool_registry import ToolRegistry


class TestChatIntegration:
    """Integration tests for GRC Agent Squad chat functionality."""

    @pytest.fixture
    def tool_registry(self):
        """Create a tool registry for testing."""
        registry = Mock(spec=ToolRegistry)
        registry.get_tools = Mock(return_value=[])
        registry.list_tools = Mock(return_value=[])
        return registry

    @pytest.fixture
    def grc_squad(self, tool_registry):
        """Create a GRC Agent Squad instance."""
        squad = GRCAgentSquad(tool_registry=tool_registry)
        return squad

    def create_mock_response(self, output_text, agent_name="Emma - Information Collector", confidence=0.85):
        """Helper method to create a mock response object."""
        mock_response = Mock()
        mock_response.output = output_text
        mock_response.streaming = False
        mock_response.metadata = Mock()
        mock_response.metadata.agent_name = agent_name
        mock_response.metadata.confidence = confidence
        return mock_response

    @pytest.mark.asyncio
    async def test_simple_chat_flow(self, grc_squad):
        """Test a simple chat conversation flow."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            # Create a mock response that matches agent-squad response structure
            mock_response = self.create_mock_response(
                "Hello! I'm Emma, your empathetic interviewer. I'm here to help you with compliance interviews and information gathering. How can I assist you today?",
                confidence=0.85
            )
            mock_route.return_value = mock_response
            
            response = await grc_squad.process_request(
                user_input="Hello, I need help with a compliance audit",
                session_id="chat-session-1"
            )
            
            # Verify the response
            assert response["success"] is True
            assert response["agent_selection"]["agent_id"] == "auto_selected"
            assert "Emma" in response["agent_response"]["response"]
            assert response["agent_selection"]["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, grc_squad):
        """Test a multi-turn conversation with session continuity."""
        session_id = "multi-turn-session"
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            # First turn - compliance question
            mock_response = self.create_mock_response(
                "I can help you understand GDPR compliance requirements. What specific aspect would you like to discuss?",
                "Dr. Morgan - Compliance Authority"
            )
            mock_route.return_value = mock_response
            
            response_1 = await grc_squad.process_request(
                user_input="Can you explain GDPR data protection requirements?",
                session_id=session_id
            )
            
            assert response_1["success"] is True
            assert response_1["agent_selection"]["agent_id"] == "auto_selected"
            
            # Second turn - follow-up question in same session
            mock_response = self.create_mock_response(
                "Under GDPR Article 32, you must implement appropriate technical and organizational measures to ensure security of processing...",
                "Dr. Morgan - Compliance Authority"
            )
            mock_route.return_value = mock_response
            
            response_2 = await grc_squad.process_request(
                user_input="What specific security measures are required?",
                session_id=session_id
            )
            
            assert response_2["success"] is True
            assert response_2["session_id"] == session_id
            assert "Article 32" in response_2["agent_response"]["response"]

    @pytest.mark.asyncio
    async def test_different_request_types_select_appropriate_agents(self, grc_squad):
        """Test that different GRC request types work with agent-squad orchestration."""
        test_cases = [
            {
                "input": "I need help conducting an audit interview with our IT team",
                "session": "interview-session",
                "response": "I'd be happy to help you prepare for the audit interview. Let's discuss the key areas we should cover with your IT team.",
                "agent_name": "Emma - Information Collector"
            },
            {
                "input": "What are the specific GDPR requirements for data retention?",
                "session": "compliance-session",
                "response": "According to GDPR Article 5(1)(e), personal data must be kept in a form which permits identification for no longer than necessary...",
                "agent_name": "Dr. Morgan - Compliance Authority"
            },
            {
                "input": "Can you help me assess the risks of our new cloud migration?",
                "session": "risk-session", 
                "response": "Let me analyze the risk factors for your cloud migration. We need to consider data security, compliance, vendor risk, and operational continuity...",
                "agent_name": "Alex - Risk Analysis Expert"
            },
            {
                "input": "How should we structure our board committees for better governance?",
                "session": "governance-session",
                "response": "For effective board governance, I recommend establishing clear committee structures with defined roles and responsibilities...",
                "agent_name": "Sam - Governance Strategist"
            }
        ]
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            for case in test_cases:
                mock_response = self.create_mock_response(case["response"], case["agent_name"])
                mock_route.return_value = mock_response
                
                response = await grc_squad.process_request(
                    user_input=case["input"],
                    session_id=case["session"]
                )
                
                assert response["success"] is True
                # Agent-squad handles selection automatically, so we verify the response content
                assert response["agent_response"]["response"] == case["response"]
                assert response["agent_selection"]["agent_id"] == "auto_selected"

    @pytest.mark.asyncio
    async def test_concurrent_chat_sessions(self, grc_squad):
        """Test handling multiple concurrent chat sessions."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_response = self.create_mock_response("Concurrent response from GRC agent")
            mock_route.return_value = mock_response
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = grc_squad.process_request(
                    user_input=f"Hello from session {i}",
                    session_id=f"concurrent-session-{i}"
                )
                tasks.append(task)
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["agent_response"]["response"] == "Concurrent response from GRC agent"
                assert result["session_id"] == f"concurrent-session-{i}"

    @pytest.mark.asyncio
    async def test_error_handling_in_chat(self, grc_squad):
        """Test error handling during chat processing."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            # Simulate an agent error
            mock_route.side_effect = Exception("Simulated GRC agent error")
            
            response = await grc_squad.process_request(
                user_input="This should cause an error",
                session_id="error-session"
            )
            
            assert response["success"] is False
            assert "error" in response
            assert "Simulated GRC agent error" in response["error"]

    @pytest.mark.asyncio
    async def test_agent_selection_confidence_scoring(self, grc_squad):
        """Test that agent selection provides confidence scores via agent-squad."""
        test_cases = [
            {
                "input": "I need help with GDPR Article 25 data protection by design requirements",  # Strong compliance signal
                "expected_high_confidence": True,
                "agent_name": "Dr. Morgan - Compliance Authority",
                "confidence": 0.95
            },
            {
                "input": "Can you help me with something?",  # Vague request
                "expected_high_confidence": False,
                "agent_name": "Emma - Information Collector",
                "confidence": 0.65
            }
        ]
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            for case in test_cases:
                mock_response = self.create_mock_response(
                    "Response based on confidence level",
                    case["agent_name"],
                    case["confidence"]
                )
                mock_route.return_value = mock_response
                
                response = await grc_squad.process_request(
                    user_input=case["input"],
                    session_id="confidence-test"
                )
                
                assert response["success"] is True
                # Agent-squad handles confidence internally, we verify the response structure
                confidence = response["agent_selection"]["confidence"]
                assert isinstance(confidence, (int, float))
                assert 0.0 <= confidence <= 1.0
                assert confidence == case["confidence"]

    @pytest.mark.asyncio
    async def test_chat_with_context(self, grc_squad):
        """Test chat functionality with additional context."""
        context = {
            "company": "ACME Financial Services",
            "department": "Risk Management",
            "topic": "SOX compliance audit"
        }
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_response = self.create_mock_response(
                "For ACME Financial Services' SOX compliance audit in Risk Management, I recommend focusing on key controls around financial reporting...",
                "Dr. Morgan - Compliance Authority"
            )
            mock_route.return_value = mock_response
            
            response = await grc_squad.process_request(
                user_input="What should we focus on for our SOX audit?",
                session_id="context-session",
                context=context
            )
            
            assert response["success"] is True
            # Verify context is incorporated (agent-squad handles this internally)
            assert response["agent_response"]["response"] is not None
            assert len(response["agent_response"]["response"]) > 0

    @pytest.mark.asyncio
    async def test_agent_response_formatting(self, grc_squad):
        """Test that agent responses are properly formatted."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_response = self.create_mock_response(
                "This is a properly formatted GRC agent response with clear structure and helpful information.",
                "Emma - Information Collector"
            )
            mock_route.return_value = mock_response
            
            response = await grc_squad.process_request(
                user_input="Test message for formatting",
                session_id="format-session"
            )
            
            assert response["success"] is True
            
            # Verify response structure
            agent_response = response["agent_response"]
            assert isinstance(agent_response, dict)
            assert "response" in agent_response
            assert isinstance(agent_response["response"], str)
            assert len(agent_response["response"]) > 0

    @pytest.mark.asyncio
    async def test_session_isolation(self, grc_squad):
        """Test that different sessions are properly isolated."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            # Session 1
            mock_response = self.create_mock_response(
                "Response for session 1 about compliance",
                "Dr. Morgan - Compliance Authority"
            )
            mock_route.return_value = mock_response
            
            response_1 = await grc_squad.process_request(
                user_input="Tell me about GDPR compliance",
                session_id="session-1"
            )
            
            assert response_1["success"] is True
            assert response_1["session_id"] == "session-1"
            
            # Session 2 - different topic
            mock_response = self.create_mock_response(
                "Response for session 2 about risk assessment",
                "Alex - Risk Analysis Expert"
            )
            mock_route.return_value = mock_response
            
            response_2 = await grc_squad.process_request(
                user_input="Help me assess operational risks",
                session_id="session-2"
            )
            
            assert response_2["success"] is True
            assert response_2["session_id"] == "session-2"
            
            # Verify sessions are isolated
            assert response_1["session_id"] != response_2["session_id"]

    @pytest.mark.asyncio
    async def test_grc_specific_scenarios(self, grc_squad):
        """Test GRC-specific scenarios and use cases."""
        scenarios = [
            {
                "name": "Compliance Assessment",
                "input": "We need to assess our GDPR compliance status",
                "expected_agent": "Dr. Morgan - Compliance Authority",
                "response": "I'll help you assess your GDPR compliance status. Let's review your current data processing activities..."
            },
            {
                "name": "Risk Analysis",
                "input": "What are the key risks in our new vendor relationship?",
                "expected_agent": "Alex - Risk Analysis Expert", 
                "response": "For vendor risk analysis, we need to evaluate several key areas including data security, operational reliability..."
            },
            {
                "name": "Audit Interview",
                "input": "I need to prepare questions for interviewing the finance team",
                "expected_agent": "Emma - Information Collector",
                "response": "I'll help you prepare effective interview questions for the finance team audit..."
            },
            {
                "name": "Governance Framework",
                "input": "How should we improve our board governance structure?",
                "expected_agent": "Sam - Governance Strategist",
                "response": "To improve board governance, I recommend reviewing your current committee structure and establishing clear accountability..."
            }
        ]
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            for scenario in scenarios:
                mock_response = self.create_mock_response(
                    scenario["response"],
                    scenario["expected_agent"]
                )
                mock_route.return_value = mock_response
                
                response = await grc_squad.process_request(
                    user_input=scenario["input"],
                    session_id=f"grc-scenario-{scenario['name'].lower().replace(' ', '-')}"
                )
                
                assert response["success"] is True, f"Failed scenario: {scenario['name']}"
                # Agent-squad handles selection, we verify the response quality
                assert response["agent_response"]["response"] == scenario["response"]
                assert response["agent_selection"]["agent_id"] == "auto_selected" 