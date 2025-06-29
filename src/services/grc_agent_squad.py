"""
GRC Agent Squad implementation using AWS Labs agent-squad framework.

This service provides specialized agents for Governance, Risk Management, and Compliance (GRC) tasks.
Uses Bedrock's built-in session memory for conversation persistence.

Key Features:
- Specialized GRC agents with distinct personas and expertise
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
from agent_squad.utils import AgentTools

from .aws_config import AWSConfig
from src.agents.agent_config_loader import get_default_config_registry
from src.utils.settings import settings
from src.tools.api_tools.highbond_token_tool import HighBondTokenExchangeTool


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
    
    def __init__(self):
        """
        Initialize the GRC Agent Squad.
        """
        self.logger = structlog.get_logger(__name__)
        
        # Agent squad will be initialized in _initialize_grc_agents
        self.squad = None
        
        # Agent configurations for GRC
        self.agent_configs = {}
        
        # Initialize GRC agents
        self._initialize_grc_agents()
        
        self.logger.info("GRC Agent Squad initialized with Bedrock built-in memory", 
                        agent_count=len(self.squad.agents) if self.squad else 0)
    
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
        
        # Create classifier using settings instead of hardcoded values
        self.logger.info("Creating Bedrock classifier with settings...")
        classifier = BedrockClassifier(BedrockClassifierOptions(
            model_id=settings.classifier_model_id,
            client=bedrock_client,
            inference_config={
                'maxTokens': settings.classifier_max_tokens,
                'temperature': settings.classifier_temperature,
                'topP': settings.classifier_top_p
            }
        ))
        
        # Create agents using their YAML configurations
        agents = {}
        
        # Get all available agent IDs from the config registry
        all_agent_ids = config_registry.list_agent_ids()
        self.logger.info(f"Found {len(all_agent_ids)} agent configurations: {all_agent_ids}")
        
        # Initialize the HighBond token exchange tool
        highbond_token_tool = HighBondTokenExchangeTool()
        self.logger.info(f"Created HighBond Token Exchange Tool: {highbond_token_tool.name}")
        
        # Create an agent for each configuration
        for agent_id in all_agent_ids:
            config = config_registry.get_config(agent_id)
            if not config:
                self.logger.error(f"No configuration found for agent: {agent_id}")
                continue
                
            # Extract model settings from YAML configuration
            model_settings = config.get_model_settings()
            model_id = model_settings['model_id']
            inference_config = model_settings.get('inference_config', {
                "maxTokens": 4096,
                "temperature": 0.7,
                "topP": 0.9
            })
            streaming = model_settings.get('streaming', False)
            memory_enabled = model_settings.get('memory_enabled', True)
            
            # Check if the agent has available tools configured
            tools = config.config_data.get('tools', [])
            tools_config = None
            
            # If the agent needs the HighBond token exchange tool, add it
            if 'highbond_token_exchange' in tools:
                self.logger.info(f"Adding HighBond Token Exchange Tool to agent: {agent_id}")
                tools_config = {
                    'tool': AgentTools([highbond_token_tool]),
                    'toolMaxRecursions': 5,
                }
            
            # Create agent using configuration from YAML
            agent = BedrockLLMAgent(BedrockLLMAgentOptions(
                name=config.config_data.get('name', agent_id),
                description=config.config_data.get('description', ''),
                model_id=model_id,
                streaming=streaming,
                inference_config=inference_config,
                save_chat=memory_enabled,  # Use memory_enabled from config
                client=bedrock_client,
                custom_system_prompt={
                    "template": config.get_system_prompt(),
                    "variables": config.get_system_prompt_variables() or {}
                },  # Pass as dict with template key
                tool_config=tools_config  # Add tools if configured for this agent
            ))
            
            # Set the agent ID to the YAML config ID
            agent.id = agent_id
            
            agents[agent_id] = agent
            self.logger.info(f"Created agent '{agent_id}' with model '{model_id}'")
            if tools_config:
                self.logger.info(f"Added tools to agent '{agent_id}' with max recursions: {tools_config['toolMaxRecursions']}")
        
        # Create orchestrator with classifier and default agent
        self.logger.info("Creating agent squad orchestrator...")
        
        # Use the configured default agent if available, otherwise fall back to the first agent
        default_agent_id = settings.default_agent if settings.default_agent in agents else next(iter(agents.keys())) if agents else None
        default_agent = agents.get(default_agent_id) if default_agent_id else None
        
        if not default_agent:
            self.logger.error("No agents created, cannot initialize squad")
            raise ValueError("No agents available for GRC Agent Squad")
            
        self.logger.info(f"Using '{default_agent_id}' as default agent")
        
        self.squad = AgentSquad(
            classifier=classifier,
            default_agent=default_agent
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
            # Check if a direct agent_id is specified in the context
            direct_agent_id = None
            if context and "agent_id" in context:
                direct_agent_id = context["agent_id"]
                self.logger.info(f"Direct agent ID specified in context: {direct_agent_id}")
            
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
            selected_agent_id = direct_agent_id if direct_agent_id else "N/A"  # Use direct_agent_id if specified
            confidence = None  # Initialize as None for API compatibility
            
            # Get agent selection metadata
            if hasattr(response, 'metadata') and response.metadata:
                selected_agent_name = getattr(response.metadata, 'agent_name', 'No Agent')
                
                # Use the agent ID directly from the metadata if available and not overridden by direct_agent_id
                if not direct_agent_id and hasattr(response.metadata, 'agent_id'):
                    selected_agent_id = getattr(response.metadata, 'agent_id', 'N/A')
                    self.logger.info(f"Selected agent ID from metadata: {selected_agent_id}")
                
                # Convert confidence to float or None for API compatibility
                raw_confidence = response.metadata.additional_params.get('confidence', None)
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
            
            self.logger.info(f"Processed request with agent ID: {selected_agent_id}, name: {selected_agent_name}")
            
            return {
                "success": True,
                "agent_selection": {
                    "agent_id": selected_agent_id,
                    "agent_name": selected_agent_name,
                    "confidence": confidence,
                    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
                },
                "agent_response": {"response": response_text},
                "session_id": session_id,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Failed to process request: {str(e)}"
            self.logger.error(error_msg, 
                            error=str(e), 
                            session_id=session_id,
                            user_input=user_input[:100])
            return {
                "success": False,
                "agent_selection": None,
                "agent_response": None,
                "session_id": session_id,
                "error": error_msg
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
            "agent_types": list(self.agent_configs.keys())
        }
