"""
GRC Agent Squad implementation using AWS Labs agent-squad framework.

This service provides specialized agents for Governance, Risk Management, and Compliance (GRC) tasks.
Uses Bedrock's built-in session memory for conversation persistence.

Key Features:
- Four specialized GRC agents with distinct personalities and expertise
- Automatic agent selection via agent-squad framework orchestration
- Bedrock built-in memory for seamless conversation continuity
- Tool registry integration for extensible functionality
"""

import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, UTC

from agent_squad.orchestrator import AgentSquad
from agent_squad.agents import BedrockLLMAgent, BedrockLLMAgentOptions
from agent_squad.classifiers import BedrockClassifier, BedrockClassifierOptions

from ..tools.tool_registry import ToolRegistry, get_default_registry
from ..models.agent_models import AgentCapability
from .aws_config import AWSConfig
from ..agents.grc_agent_configs import (
    EmpathicInterviewerConfig,
    ComplianceAuthorityConfig, 
    RiskAnalysisExpertConfig,
    GovernanceStrategistConfig
)


class GRCAgentSquad:
    """
    GRC Agent Squad using agent-squad framework with Bedrock built-in memory.
    
    Implements the four specialized GRC agents:
    1. Information Collector (empathetic_interviewer)
    2. Official Compliance Agent (authoritative_compliance)  
    3. Risk Expert Agent (analytical_risk_expert)
    4. Governance Specialist Agent (strategic_governance)
    
    Uses Bedrock's built-in session memory for conversation persistence.
    """
    
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """
        Initialize the GRC Agent Squad.
        
        Args:
            tool_registry: Tool registry for external capabilities
        """
        self.tool_registry = tool_registry or get_default_registry()
        self.logger = structlog.get_logger(__name__)
        
        # Agent squad will be initialized in _initialize_grc_agents
        self.squad = None
        
        # Agent configurations for GRC
        self.agent_configs = {}
        
        # Initialize GRC agents
        self._initialize_grc_agents()
        
        self.logger.info("GRC Agent Squad initialized with Bedrock built-in memory", 
                        agent_count=len(self.squad.agents) if self.squad else 0,
                        available_tools=len(self.tool_registry.list_tools()))
    
    def _initialize_grc_agents(self):
        """Initialize the four specialized GRC agents with Bedrock memory configuration."""
        
        # Configure memory settings via inference_config for Bedrock agents
        memory_inference_config = {
            "maxTokens": 4096,
            "temperature": 0.7,
            "topP": 0.9
        }
        
        # Configure AWS session using shared AWSConfig implementation
        try:
            bedrock_client = AWSConfig.create_aws_vault_client('bedrock-runtime')
            self.logger.info("AWS session and Bedrock client configured successfully using shared AWSConfig")
        except Exception as e:
            self.logger.error(f"Failed to configure AWS session or Bedrock client: {e}")
            raise
        
        # Create classifier first (needed for orchestrator)
        self.logger.info("Creating Bedrock classifier...")
        classifier = BedrockClassifier(BedrockClassifierOptions(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            client=bedrock_client,
            inference_config={'maxTokens': 100, 'temperature': 0.1}
        ))
        
        # 1. Information Collector Agent (Empathetic Interviewer)
        empathetic_interviewer = BedrockLLMAgent(BedrockLLMAgentOptions(
            name="Emma - Information Collector",
            description="Empathetic interviewer specialized in conducting thorough audit interviews, stakeholder consultations, and gathering detailed compliance information. I help with interviews, data collection, and creating comfortable environments for information gathering.",
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            streaming=False,
            inference_config=memory_inference_config,
            save_chat=True,  # Enables built-in conversation history
            client=bedrock_client  # Use programmatically extracted credentials
        ))
        
        # 2. Official Compliance Agent (Authoritative Compliance)
        authoritative_compliance = BedrockLLMAgent(BedrockLLMAgentOptions(
            name="Dr. Morgan - Compliance Authority",
            description="Official compliance agent providing definitive regulatory guidance, compliance interpretations, and formal documentation. I specialize in regulatory requirements, compliance standards, and official policy interpretations.",
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            streaming=False,
            inference_config=memory_inference_config,
            save_chat=True,
            client=bedrock_client  # Use programmatically extracted credentials
        ))
        
        # 3. Risk Expert Agent (Analytical Risk Expert)
        analytical_risk_expert = BedrockLLMAgent(BedrockLLMAgentOptions(
            name="Alex - Risk Analysis Expert",
            description="Analytical risk expert specializing in risk assessment, analysis, and mitigation strategies. I focus on risk modeling, threat analysis, control evaluation, and developing comprehensive risk management strategies.",
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            streaming=False,
            inference_config=memory_inference_config,
            save_chat=True,
            client=bedrock_client  # Use programmatically extracted credentials
        ))
        
        # 4. Governance Specialist Agent (Strategic Governance)
        strategic_governance = BedrockLLMAgent(BedrockLLMAgentOptions(
            name="Sam - Governance Strategist",
            description="Strategic governance specialist focused on governance frameworks, policy development, and board-level guidance. I provide strategic advice on governance structures, policy creation, and organizational governance best practices.",
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            streaming=False,
            inference_config=memory_inference_config,
            save_chat=True,
            client=bedrock_client  # Use programmatically extracted credentials
        ))
        
        # Create orchestrator with classifier and default agent
        self.logger.info("Creating agent squad orchestrator...")
        self.squad = AgentSquad(
            classifier=classifier,
            default_agent=empathetic_interviewer  # Default to the empathetic interviewer
        )
        
        # Set modular system prompts for each agent using capability-based components
        empathetic_interviewer.set_system_prompt(
            EmpathicInterviewerConfig.get_system_prompt()
        )
        
        authoritative_compliance.set_system_prompt(
            ComplianceAuthorityConfig.get_system_prompt()
        )
        
        analytical_risk_expert.set_system_prompt(
            RiskAnalysisExpertConfig.get_system_prompt()
        )
        
        strategic_governance.set_system_prompt(
            GovernanceStrategistConfig.get_system_prompt()
        )
        
        # Add agents to the squad
        self.squad.add_agent(empathetic_interviewer)
        self.squad.add_agent(authoritative_compliance)
        self.squad.add_agent(analytical_risk_expert)
        self.squad.add_agent(strategic_governance)
        
        self.logger.info("GRC agents added to squad", agent_count=len(self.squad.agents))
        
        # Store agent configurations using modular configs for API compatibility
        from ..agents.grc_agent_configs import GRCAgentConfigRegistry
        
        self.agent_configs = {
            "empathetic_interviewer": GRCAgentConfigRegistry.build_agent_metadata("empathetic_interviewer"),
            "authoritative_compliance": GRCAgentConfigRegistry.build_agent_metadata("authoritative_compliance"),
            "analytical_risk_expert": GRCAgentConfigRegistry.build_agent_metadata("analytical_risk_expert"),
            "strategic_governance": GRCAgentConfigRegistry.build_agent_metadata("strategic_governance")
        }
    
    async def process_request(self, user_input: str, session_id: str = "default", 
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user request through the agent squad.
        
        Args:
            user_input: User's input message
            session_id: Session identifier for conversation tracking (handled by Bedrock)
            context: Additional context for the request
            
        Returns:
            Response with agent selection and message
        """
        try:
            # Include response type in the user input for agent awareness
            enhanced_user_input = user_input
            if context and context.get("response_type"):
                response_type = context["response_type"]
                if response_type == "display":
                    enhanced_user_input = f"[DISPLAY_MODE] {user_input}"
                elif response_type == "voice":
                    enhanced_user_input = f"[VOICE_MODE] {user_input}"
            
            # Process through agent squad with session_id for Bedrock memory
            # The agent-squad framework and Bedrock will handle conversation history automatically
            response = await self.squad.route_request(
                user_input=enhanced_user_input,
                user_id="default_user",
                session_id=session_id
            )
            
            # Extract response text based on agent-squad response format
            response_text = ""
            selected_agent_name = "No Agent"
            confidence = None  # Initialize as None for API compatibility
            
            # Get agent selection metadata
            if hasattr(response, 'metadata') and response.metadata:
                selected_agent_name = getattr(response.metadata, 'agent_name', 'No Agent')
                # Convert confidence to float or None for API compatibility
                raw_confidence = getattr(response.metadata, 'confidence', None)
                if isinstance(raw_confidence, (int, float)):
                    confidence = float(raw_confidence)
                elif isinstance(raw_confidence, str) and raw_confidence.replace('.', '').isdigit():
                    confidence = float(raw_confidence)
                else:
                    confidence = None  # Default to None instead of "Unknown"
            
            # Extract response content
            if hasattr(response, 'output') and response.output:
                if hasattr(response.output, 'content') and response.output.content:
                    # Handle list of content items
                    if isinstance(response.output.content, list) and response.output.content:
                        response_text = response.output.content[0].get('text', 'No response text')
                    else:
                        response_text = str(response.output.content)
                elif isinstance(response.output, list):
                    # Handle list responses (like error messages)
                    if response.output and isinstance(response.output[0], dict) and 'text' in response.output[0]:
                        response_text = response.output[0]['text']
                    elif response.output:
                        # Join list items if they're strings
                        response_text = ' '.join(str(item) for item in response.output)
                    else:
                        response_text = "Empty response"
                else:
                    response_text = str(response.output)
            else:
                response_text = "No response from agent"
            
            return {
                "success": True,
                "agent_selection": {
                    "agent_id": "auto_selected",
                    "agent_name": selected_agent_name,
                    "confidence": confidence,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                },
                "agent_response": {"response": response_text},
                "session_id": session_id,
                "error": None
            }
            
        except Exception as e:
            self.logger.error("Failed to process request", 
                            error=str(e), 
                            session_id=session_id,
                            user_input=user_input[:100])
            return {
                "success": False,
                "agent_selection": None,
                "agent_response": None,
                "session_id": session_id,
                "error": f"Failed to process request: {str(e)}"
            }
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """Get list of all GRC agents."""
        return list(self.agent_configs.values())
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent."""
        return self.agent_configs.get(agent_id)
    
    async def get_squad_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent squad."""
        return {
            "total_agents": len(self.agent_configs),
            "active_agents": len([a for a in self.agent_configs.values() if a["status"] == "active"]),
            "memory_type": "bedrock_built_in",
            "available_tools": len(self.tool_registry.list_tools()),
            "agent_types": list(self.agent_configs.keys())
        }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return [
            {
                "name": tool_name,
                "description": tool.description,
                "category": getattr(tool, 'category', 'general')
            }
            for tool_name, tool in self.tool_registry.tools.items()
        ] 