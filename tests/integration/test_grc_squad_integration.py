"""
Integration tests for GRC Agent Squad core functionality.

Tests the complete GRC Agent Squad initialization, agent selection, and response generation
using real AWS Bedrock integration with mocked credentials for consistent testing.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from src.services.grc_agent_squad import GRCAgentSquad


class TestGRCSquadIntegration:
    """Integration tests for GRC Agent Squad core functionality."""

    @pytest.fixture
    def mock_bedrock_client(self):
        """Create a mock Bedrock client for testing."""
        client = Mock()
        client.converse = Mock(return_value={
            'output': {'message': {'content': [{'text': 'Test connection successful'}]}}
        })
        return client

    @pytest.fixture
    def grc_squad(self, mock_bedrock_client):
        """Create a GRC Agent Squad instance with mocked dependencies."""
        with patch('src.services.aws_config.AWSConfig.create_aws_vault_client') as mock_bedrock:
            mock_bedrock.return_value = mock_bedrock_client
            
            # Disable hierarchical routing for consistent test behavior
            squad = GRCAgentSquad(enable_hierarchical_routing=False)
            return squad

    def create_mock_agent_response(self, response_text: str, agent_name: str = "Emma - Information Collector", 
                                 confidence: float = 0.85):
        """Helper method to create a mock agent-squad response."""
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.content = [{'text': response_text}]
        mock_response.metadata = Mock()
        mock_response.metadata.agent_name = agent_name
        mock_response.metadata.additional_params = {'confidence': confidence}
        return mock_response

    @pytest.mark.asyncio
    async def test_grc_squad_initialization(self, mock_bedrock_client):
        """Test that GRC Agent Squad initializes correctly with all required agents."""
        with patch('src.services.aws_config.AWSConfig.create_aws_vault_client') as mock_bedrock:
            mock_bedrock.return_value = mock_bedrock_client
            
            grc_squad = GRCAgentSquad()
            
            # Verify initialization
            assert grc_squad.squad is not None
            assert len(grc_squad.agent_configs) == 5
            
            # Verify all required GRC agents are present
            expected_agents = [
                "empathetic_interviewer_executive",
                "authoritative_compliance_executive",
                "analytical_risk_expert_executive",
                "strategic_governance_executive",
                "supervisor_grc"
            ]
            
            for agent_id in expected_agents:
                assert agent_id in grc_squad.agent_configs
                agent_config = grc_squad.agent_configs[agent_id]
                assert "name" in agent_config
                assert "description" in agent_config

    @pytest.mark.asyncio
    async def test_grc_agent_selection_scenarios(self, grc_squad):
        """Test GRC-specific agent selection scenarios."""
        test_scenarios = [
            {
                "query": "I need help conducting an audit interview with our IT department about access controls.",
                "expected_agent": "Emma - Information Collector",
                "expected_response": "I'd be happy to help you prepare for the audit interview. Let's discuss the key areas we should cover with your IT team regarding access controls.",
                "confidence": 0.9
            },
            {
                "query": "What are the specific SOX compliance requirements for financial reporting controls?",
                "expected_agent": "Dr. Morgan - Compliance Authority", 
                "expected_response": "According to the Sarbanes-Oxley Act Section 404, companies must establish and maintain adequate internal control over financial reporting...",
                "confidence": 0.95
            },
            {
                "query": "Can you help me assess the cybersecurity risks in our cloud infrastructure?",
                "expected_agent": "Alex - Risk Analysis Expert",
                "expected_response": "I'll help you conduct a comprehensive cybersecurity risk assessment for your cloud infrastructure. Let's start by identifying the key risk factors...",
                "confidence": 0.88
            },
            {
                "query": "We need to develop a new governance framework for our board committees.",
                "expected_agent": "Sam - Governance Strategist",
                "expected_response": "I'll assist you in developing an effective governance framework for your board committees. Let's begin by examining your current governance structure...",
                "confidence": 0.92
            },
            {
                "query": "I have general questions about our compliance program.",
                "expected_agent": "Dr. Morgan - Compliance Authority",
                "expected_response": "I can help you with your compliance program questions. What specific aspects would you like to discuss?",
                "confidence": 0.75
            }
        ]
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            for i, scenario in enumerate(test_scenarios):
                # Create mock response
                mock_response = self.create_mock_agent_response(
                    scenario["expected_response"],
                    scenario["expected_agent"],
                    scenario["confidence"]
                )
                mock_route.return_value = mock_response
                
                # Process request
                response = await grc_squad.process_request(
                    user_input=scenario["query"],
                    session_id=f"grc_test_session_{i}"
                )
                
                # Verify response
                assert response["success"] is True
                assert response["agent_selection"]["agent_name"] == scenario["expected_agent"]
                assert response["agent_response"]["response"] == scenario["expected_response"]
                assert response["agent_selection"]["confidence"] == scenario["confidence"]
                assert response["session_id"] == f"grc_test_session_{i}"

    @pytest.mark.asyncio
    async def test_grc_agent_information_retrieval(self, grc_squad):
        """Test retrieval of GRC agent information."""
        # Test list_agents
        agents = await grc_squad.list_agents()
        assert len(agents) == 5
        
        # Verify each agent has required fields
        for agent in agents:
            assert "agent_id" in agent
            assert "name" in agent
            assert "description" in agent
            
        # Test get_agent_info for each agent
        expected_agents = {
            "empathetic_interviewer_executive": "Emma - Senior Information Collector",
            "authoritative_compliance_executive": "Dr. Morgan - Chief Compliance Officer",
            "analytical_risk_expert_executive": "Alex - Chief Risk Officer", 
            "strategic_governance_executive": "Sam - Chief Governance Officer",
            "supervisor_grc": "Director"
        }
        
        for agent_id, expected_name in expected_agents.items():
            agent_info = await grc_squad.get_agent_info(agent_id)
            assert agent_info is not None
            assert agent_info["name"] == expected_name
            assert agent_info["agent_id"] == agent_id

    @pytest.mark.asyncio
    async def test_grc_squad_statistics(self, grc_squad):
        """Test GRC squad statistics and metadata."""
        stats = await grc_squad.get_squad_stats()
        
        assert stats["total_agents"] == 5
        assert stats["active_agents"] == 5
        assert stats["memory_type"] == "bedrock_built_in"
        assert len(stats["agent_types"]) == 5
        
        expected_agent_types = [
            "empathetic_interviewer_executive",
            "authoritative_compliance_executive",
            "analytical_risk_expert_executive", 
            "strategic_governance_executive",
            "supervisor_grc"
        ]
        
        for agent_type in expected_agent_types:
            assert agent_type in stats["agent_types"]

    @pytest.mark.asyncio
    async def test_grc_session_continuity(self, grc_squad):
        """Test session continuity across multiple interactions."""
        session_id = "grc_continuity_session"
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            # First interaction - compliance question
            mock_response_1 = self.create_mock_agent_response(
                "I understand you need help with GDPR compliance. What specific area would you like to focus on?",
                "Dr. Morgan - Compliance Authority",
                0.9
            )
            mock_route.return_value = mock_response_1
            
            response_1 = await grc_squad.process_request(
                user_input="I need help with GDPR compliance",
                session_id=session_id
            )
            
            assert response_1["success"] is True
            assert response_1["session_id"] == session_id
            
            # Second interaction - follow-up in same session
            mock_response_2 = self.create_mock_agent_response(
                "For data breach notification under GDPR Article 33, you must notify the supervisory authority within 72 hours...",
                "Dr. Morgan - Compliance Authority",
                0.95
            )
            mock_route.return_value = mock_response_2
            
            response_2 = await grc_squad.process_request(
                user_input="What about data breach notification requirements?",
                session_id=session_id
            )
            
            assert response_2["success"] is True
            assert response_2["session_id"] == session_id
            # Verify the squad was called with the same session_id for continuity
            mock_route.assert_called_with(
                user_input="What about data breach notification requirements?",
                user_id="default_user",
                session_id=session_id
            )

    @pytest.mark.asyncio
    async def test_grc_error_handling(self, grc_squad):
        """Test error handling in GRC Agent Squad operations."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            # Simulate a processing error
            mock_route.side_effect = Exception("Simulated GRC processing error")
            
            response = await grc_squad.process_request(
                user_input="This should cause an error",
                session_id="error_test_session"
            )
            
            assert response["success"] is False
            assert response["error"] is not None
            assert "Failed to process request" in response["error"]
            assert "Simulated GRC processing error" in response["error"]
            assert response["session_id"] == "error_test_session"

    @pytest.mark.asyncio
    async def test_grc_concurrent_requests(self, grc_squad):
        """Test handling of concurrent GRC requests."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_response = self.create_mock_agent_response(
                "Concurrent GRC response",
                "Emma - Information Collector",
                0.8
            )
            mock_route.return_value = mock_response
            
            # Create multiple concurrent requests
            concurrent_requests = []
            for i in range(5):
                request = grc_squad.process_request(
                    user_input=f"Concurrent GRC query {i}",
                    session_id=f"concurrent_session_{i}"
                )
                concurrent_requests.append(request)
            
            # Execute all requests concurrently
            results = await asyncio.gather(*concurrent_requests)
            
            # Verify all requests succeeded
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["session_id"] == f"concurrent_session_{i}"
                assert result["agent_response"]["response"] == "Concurrent GRC response"

    @pytest.mark.asyncio
    async def test_confidence_value_handling(self, grc_squad):
        """Test proper handling of confidence values (avoiding the previous string issue)."""
        test_cases = [
            {"confidence": 0.95, "expected": 0.95},
            {"confidence": 1, "expected": 1.0},
            {"confidence": "0.75", "expected": 0.75},
            {"confidence": "Unknown", "expected": None},
            {"confidence": None, "expected": None},
            {"confidence": "invalid", "expected": None}
        ]
        
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            for i, case in enumerate(test_cases):
                # Create mock response with specific confidence value
                mock_response = Mock()
                mock_response.output = Mock()
                mock_response.output.content = [{'text': f"Test response {i}"}]
                mock_response.metadata = Mock()
                mock_response.metadata.agent_name = "Emma - Information Collector"
                mock_response.metadata.additional_params = {'confidence': case["confidence"]}
                
                mock_route.return_value = mock_response
                
                response = await grc_squad.process_request(
                    user_input=f"Test confidence handling {i}",
                    session_id=f"confidence_test_{i}"
                )
                
                assert response["success"] is True
                assert response["agent_selection"]["confidence"] == case["expected"]

    @pytest.mark.asyncio
    async def test_grc_response_format_consistency(self, grc_squad):
        """Test that all GRC responses follow consistent format."""
        with patch.object(grc_squad.squad, 'route_request', new_callable=AsyncMock) as mock_route:
            mock_response = self.create_mock_agent_response(
                "Consistent format test response",
                "Dr. Morgan - Compliance Authority",
                0.85
            )
            mock_route.return_value = mock_response
            
            response = await grc_squad.process_request(
                user_input="Test format consistency",
                session_id="format_test_session"
            )
            
            # Verify response structure
            assert isinstance(response, dict)
            assert "success" in response
            assert "agent_selection" in response
            assert "agent_response" in response
            assert "session_id" in response
            assert "error" in response
            
            # Verify agent_selection structure
            agent_selection = response["agent_selection"]
            assert "agent_id" in agent_selection
            assert "agent_name" in agent_selection
            assert "confidence" in agent_selection
            assert "reasoning" in agent_selection
            
            # Verify agent_response structure
            agent_response = response["agent_response"]
            assert "response" in agent_response
            
            # Verify data types
            assert isinstance(response["success"], bool)
            assert isinstance(agent_selection["confidence"], (float, type(None)))
            assert isinstance(agent_response["response"], str)

    @pytest.mark.asyncio
    async def test_hierarchical_routing_functionality(self):
        """Test hierarchical routing specific functionality."""
        print("\n🧪 Testing hierarchical routing functionality...")
        
        # Test with hierarchical routing enabled
        with patch('src.services.aws_config.AWSConfig.create_aws_vault_client') as mock_bedrock:
            mock_bedrock.return_value = Mock()
            hierarchical_squad = GRCAgentSquad(enable_hierarchical_routing=True)
            
            # Verify hierarchical classifier is used
            from src.classifiers.hierarchical_classifier import HierarchicalClassifier
            assert isinstance(hierarchical_squad.squad.classifier, HierarchicalClassifier)
            
            # Test configuration loading
            assert hierarchical_squad.squad.classifier.squad_config is not None
            assert len(hierarchical_squad.squad.classifier.squad_config.tiers) >= 2
            
            # Test tier structure
            tiers = hierarchical_squad.squad.classifier.squad_config.tiers
            specialist_tier = next((t for t in tiers if t.type == "specialist"), None)
            supervisor_tier = next((t for t in tiers if t.type == "supervisor"), None)
            
            assert specialist_tier is not None, "Should have specialist tier"
            assert supervisor_tier is not None, "Should have supervisor tier"
            assert specialist_tier.confidence_threshold > supervisor_tier.confidence_threshold, "Specialist threshold should be higher"
            
            print(f"✅ Specialist tier: {len(specialist_tier.agents)} agents, threshold: {specialist_tier.confidence_threshold}")
            print(f"✅ Supervisor tier: {len(supervisor_tier.agents)} agents, threshold: {supervisor_tier.confidence_threshold}")

    @pytest.mark.asyncio
    async def test_hierarchical_vs_standard_routing_comparison(self):
        """Test that hierarchical and standard routing can both be initialized."""
        with patch('src.services.aws_config.AWSConfig.create_aws_vault_client') as mock_bedrock:
            mock_bedrock.return_value = Mock()
            
            # Initialize both types
            hierarchical_squad = GRCAgentSquad(enable_hierarchical_routing=True)
            standard_squad = GRCAgentSquad(enable_hierarchical_routing=False)
            
            # Both should initialize successfully
            assert hierarchical_squad.squad is not None
            assert standard_squad.squad is not None
            
            # Should have same number of agents
            assert len(hierarchical_squad.squad.agents) == len(standard_squad.squad.agents)
            
            # Should use different classifiers
            from src.classifiers.hierarchical_classifier import HierarchicalClassifier
            assert isinstance(hierarchical_squad.squad.classifier, HierarchicalClassifier)
            assert not isinstance(standard_squad.squad.classifier, HierarchicalClassifier) 