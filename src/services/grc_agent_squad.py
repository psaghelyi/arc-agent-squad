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
from ..agents.agent_config_loader import get_default_config_registry


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
        """Initialize the four specialized GRC agents using YAML configurations."""
        
        # Configure AWS session using shared AWSConfig implementation
        try:
            bedrock_client = AWSConfig.create_aws_vault_client('bedrock-runtime')
            self.logger.info("AWS session and Bedrock client configured successfully using shared AWSConfig")
        except Exception as e:
            self.logger.error(f"Failed to configure AWS session or Bedrock client: {e}")
            raise
        
        # Get file-based configuration registry
        config_registry = get_default_config_registry()
        
        # Create classifier first (needed for orchestrator)
        # Use default agent's model settings for classifier
        default_config = config_registry.get_config("empathetic_interviewer_executive")
        default_model_settings = default_config.get_model_settings() if default_config else {}
        classifier_model_id = default_model_settings.get('model_id', "anthropic.claude-3-5-sonnet-20241022-v2:0")
        
        self.logger.info("Creating Bedrock classifier...")
        classifier = BedrockClassifier(BedrockClassifierOptions(
            model_id=classifier_model_id,
            client=bedrock_client,
            inference_config={'maxTokens': 100, 'temperature': 0.1}
        ))
        
        # Create agents using their YAML configurations
        agents = {}
        agent_configs = [
            ("empathetic_interviewer_executive", "empathetic_interviewer"),
            ("authoritative_compliance_executive", "authoritative_compliance"), 
            ("analytical_risk_expert_executive", "analytical_risk_expert"),
            ("strategic_governance_executive", "strategic_governance")
        ]
        
        for config_id, agent_key in agent_configs:
            config = config_registry.get_config(config_id)
            if not config:
                self.logger.error(f"No configuration found for agent: {config_id}")
                continue
                
            # Extract model settings from YAML configuration
            model_settings = config.get_model_settings()
            model_id = model_settings.get('model_id', "anthropic.claude-3-5-sonnet-20241022-v2:0")
            inference_config = model_settings.get('inference_config', {
                "maxTokens": 4096,
                "temperature": 0.7,
                "topP": 0.9
            })
            streaming = model_settings.get('streaming', False)
            memory_enabled = model_settings.get('memory_enabled', True)
            
            # Create agent using configuration from YAML
            agent = BedrockLLMAgent(BedrockLLMAgentOptions(
                name=config.config_data.get('name', config_id),
                description=config.config_data.get('description', ''),
                model_id=model_id,
                streaming=streaming,
                inference_config=inference_config,
                save_chat=memory_enabled,  # Use memory_enabled from config
                client=bedrock_client
            ))
            
            # Set system prompt from configuration
            agent.set_system_prompt(config.get_system_prompt())
            
            agents[agent_key] = agent
            self.logger.info(f"Created agent '{config_id}' with model '{model_id}'")
        
        # Create orchestrator with classifier and default agent
        self.logger.info("Creating agent squad orchestrator...")
        self.squad = AgentSquad(
            classifier=classifier,
            default_agent=agents.get("empathetic_interviewer")  # Default to the empathetic interviewer
        )
        
        # Add agents to the squad
        for agent in agents.values():
            self.squad.add_agent(agent)
        
        self.logger.info("GRC agents added to squad", agent_count=len(self.squad.agents))
        
        # Store agent configurations using file-based configs for API compatibility
        self.agent_configs = {}
        for agent_id in config_registry.loader.list_agent_ids():
            self.agent_configs[agent_id] = config_registry.build_agent_metadata(agent_id)
    
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
            "active_agents": len(self.agent_configs),  # All loaded agents are considered active
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