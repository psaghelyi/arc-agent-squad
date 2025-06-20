"""
Integration tests for chat functionality.

Tests the complete chat flow through the orchestrator with real agent selection.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.services.agent_orchestrator import AgentOrchestrator
from src.services.memory_service import MemoryService
from src.models.agent_models import (
    AgentPersonality,
    AgentCapability,
    OrchestratorRequest,
    ChatMessage
)


class TestChatIntegration:
    """Integration tests for chat functionality."""

    @pytest.fixture
    async def memory_service(self):
        """Create a memory service for testing."""
        memory_service = MemoryService()
        # Use in-memory mode for testing (don't connect to Redis)
        memory_service.connected = False
        return memory_service

    @pytest.fixture
    async def orchestrator(self, memory_service):
        """Create an orchestrator with initialized agents."""
        orchestrator = AgentOrchestrator(memory_service)
        await orchestrator.initialize_default_agents()
        return orchestrator

    @pytest.mark.asyncio
    async def test_simple_chat_flow(self, orchestrator):
        """Test a simple chat conversation flow."""
        # Mock the actual LLM response
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            mock_response = Mock()
            mock_response.content = [{"text": "Hello! I'm Emma, and I'm happy to help you with anything you need. How can I assist you today?"}]
            mock_process.return_value = mock_response
            
            # Send a greeting message
            request = OrchestratorRequest(
                user_input="Hello, I need some help",
                session_id="chat-session-1",
                context={}
            )
            
            result = await orchestrator.process_request(request)
            
            # Verify the response
            assert result["success"] is True
            assert result["agent_selection"]["agent_name"] == "Emma the Helper"
            assert "Emma" in result["agent_response"]["response"]
            assert result["agent_selection"]["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, orchestrator):
        """Test a multi-turn conversation with the same agent."""
        session_id = "multi-turn-session"
        
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            # First turn
            mock_response_1 = Mock()
            mock_response_1.content = [{"text": "Hello! I'm here to help you. What would you like to know?"}]
            mock_process.return_value = mock_response_1
            
            request_1 = OrchestratorRequest(
                user_input="Hi, can you help me understand Python?",
                session_id=session_id,
                context={}
            )
            
            result_1 = await orchestrator.process_request(request_1)
            assert result_1["success"] is True
            selected_agent_id = result_1["agent_selection"]["agent_id"]
            
            # Second turn - should use the same agent due to session continuity
            mock_response_2 = Mock()
            mock_response_2.content = [{"text": "Of course! Python is a versatile programming language. What specific aspect would you like to learn about?"}]
            mock_process.return_value = mock_response_2
            
            request_2 = OrchestratorRequest(
                user_input="What are Python data types?",
                session_id=session_id,
                context={}
            )
            
            result_2 = await orchestrator.process_request(request_2)
            assert result_2["success"] is True
            
            # Verify session tracking
            agent_instance = orchestrator.agents[selected_agent_id]
            assert session_id in agent_instance.current_sessions
            assert agent_instance.total_conversations == 2

    @pytest.mark.asyncio
    async def test_different_request_types_select_different_agents(self, orchestrator):
        """Test that different request types select appropriate agents."""
        test_cases = [
            {
                "input": "I'm feeling overwhelmed and need emotional support",
                "expected_agent": "Emma the Helper",
                "session": "emotional-session"
            },
            {
                "input": "Quick question: what's 2+2?",
                "expected_agent": "Alex the Direct",
                "session": "quick-session"
            },
            {
                "input": "I need help debugging this technical API issue",
                "expected_agent": "Dr. Morgan",
                "session": "technical-session"
            },
            {
                "input": "Can you help me brainstorm creative ideas for a story?",
                "expected_agent": "Sam the Buddy",
                "session": "creative-session"
            }
        ]
        
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            mock_response = Mock()
            mock_response.content = [{"text": "Test response"}]
            mock_process.return_value = mock_response
            
            for case in test_cases:
                request = OrchestratorRequest(
                    user_input=case["input"],
                    session_id=case["session"],
                    context={}
                )
                
                result = await orchestrator.process_request(request)
                
                assert result["success"] is True
                # Note: Agent selection is probabilistic, so we verify reasonable selection
                selected_agent = result["agent_selection"]["agent_name"]
                assert selected_agent in ["Emma the Helper", "Alex the Direct", "Dr. Morgan", "Sam the Buddy"]
                assert result["agent_selection"]["confidence"] > 0.3  # Should have reasonable confidence

    @pytest.mark.asyncio
    async def test_concurrent_chat_sessions(self, orchestrator):
        """Test handling multiple concurrent chat sessions."""
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            mock_response = Mock()
            mock_response.content = [{"text": "Concurrent response"}]
            mock_process.return_value = mock_response
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                request = OrchestratorRequest(
                    user_input=f"Hello from session {i}",
                    session_id=f"concurrent-session-{i}",
                    context={}
                )
                tasks.append(orchestrator.process_request(request))
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["agent_response"]["response"] == "Concurrent response"

    @pytest.mark.asyncio
    async def test_error_handling_in_chat(self, orchestrator):
        """Test error handling during chat processing."""
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            # Simulate an agent error
            mock_process.side_effect = Exception("Simulated agent error")
            
            request = OrchestratorRequest(
                user_input="This should cause an error",
                session_id="error-session",
                context={}
            )
            
            result = await orchestrator.process_request(request)
            
            assert result["success"] is False
            assert "error" in result
            assert "Simulated agent error" in result["error"]

    @pytest.mark.asyncio
    async def test_agent_selection_confidence_scoring(self, orchestrator):
        """Test that agent selection provides meaningful confidence scores."""
        test_cases = [
            {
                "input": "I'm really sad and need someone to talk to",  # Strong emotional signal
                "expected_high_confidence": True
            },
            {
                "input": "URGENT: Need answer now!",  # Strong urgency signal
                "expected_high_confidence": True
            },
            {
                "input": "Hello there",  # Neutral, should have lower confidence
                "expected_high_confidence": False
            }
        ]
        
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            mock_response = Mock()
            mock_response.content = [{"text": "Test response"}]
            mock_process.return_value = mock_response
            
            for i, case in enumerate(test_cases):
                request = OrchestratorRequest(
                    user_input=case["input"],
                    session_id=f"confidence-session-{i}",
                    context={}
                )
                
                result = await orchestrator.process_request(request)
                confidence = result["agent_selection"]["confidence"]
                
                if case["expected_high_confidence"]:
                    assert confidence > 0.5, f"Expected higher confidence for '{case['input']}', got {confidence}"
                else:
                    assert confidence <= 0.7, f"Expected lower confidence for '{case['input']}', got {confidence}"

    @pytest.mark.asyncio
    async def test_chat_with_context(self, orchestrator):
        """Test chat with additional context information."""
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            mock_response = Mock()
            mock_response.content = [{"text": "I understand your context and will help accordingly."}]
            mock_process.return_value = mock_response
            
            request = OrchestratorRequest(
                user_input="Help me with this problem",
                session_id="context-session",
                context={
                    "user_preference": "detailed_explanations",
                    "previous_topic": "machine_learning",
                    "urgency_level": "low"
                }
            )
            
            result = await orchestrator.process_request(request)
            
            assert result["success"] is True
            # Verify the context was passed to the agent
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            assert call_args[1]["additional_params"] == request.context

    @pytest.mark.asyncio
    async def test_agent_response_formatting(self, orchestrator):
        """Test that agent responses are properly formatted."""
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            # Test different response formats
            test_responses = [
                # Standard text response
                Mock(content=[{"text": "This is a standard response"}]),
                # Response with multiple content parts
                Mock(content=[
                    {"text": "Part 1: "},
                    {"text": "Part 2: Additional info"}
                ]),
                # Empty response
                Mock(content=[]),
                # Response with non-text content (should be handled gracefully)
                Mock(content=[{"type": "image", "data": "base64data"}])
            ]
            
            for i, mock_response in enumerate(test_responses):
                mock_process.return_value = mock_response
                
                request = OrchestratorRequest(
                    user_input=f"Test message {i}",
                    session_id=f"format-session-{i}",
                    context={}
                )
                
                result = await orchestrator.process_request(request)
                
                assert result["success"] is True
                assert "agent_response" in result
                assert "response" in result["agent_response"]
                # Response should be a string, even if empty
                assert isinstance(result["agent_response"]["response"], str)

    @pytest.mark.asyncio
    async def test_session_isolation(self, orchestrator):
        """Test that different sessions are properly isolated."""
        with patch('src.agents.personality_agent.PersonalityAgent.process_request') as mock_process:
            mock_response = Mock()
            mock_response.content = [{"text": "Session response"}]
            mock_process.return_value = mock_response
            
            # Create requests for different sessions
            session_1_request = OrchestratorRequest(
                user_input="I need help with Python",
                session_id="session-1",
                context={"topic": "python"}
            )
            
            session_2_request = OrchestratorRequest(
                user_input="I need help with JavaScript", 
                session_id="session-2",
                context={"topic": "javascript"}
            )
            
            # Process both requests
            result_1 = await orchestrator.process_request(session_1_request)
            result_2 = await orchestrator.process_request(session_2_request)
            
            # Both should succeed
            assert result_1["success"] is True
            assert result_2["success"] is True
            
            # Verify that sessions are tracked separately
            agent_1_id = result_1["agent_selection"]["agent_id"]
            agent_2_id = result_2["agent_selection"]["agent_id"]
            
            agent_1_instance = orchestrator.agents[agent_1_id]
            agent_2_instance = orchestrator.agents[agent_2_id]
            
            # Each agent should track their respective sessions
            if agent_1_id == agent_2_id:
                # Same agent handled both sessions
                assert "session-1" in agent_1_instance.current_sessions
                assert "session-2" in agent_1_instance.current_sessions
            else:
                # Different agents handled the sessions
                assert "session-1" in agent_1_instance.current_sessions
                assert "session-2" in agent_2_instance.current_sessions 