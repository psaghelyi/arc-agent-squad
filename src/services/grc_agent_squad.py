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
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, UTC

from agent_squad.orchestrator import AgentSquad
from agent_squad.agents import BedrockLLMAgent, BedrockLLMAgentOptions
from agent_squad.classifiers import BedrockClassifier, BedrockClassifierOptions
from agent_squad.utils import AgentTools

from .aws_config import AWSConfig
from src.agents.agent_config_loader import get_default_config_registry
from src.utils.settings import settings
from src.tools.tools_registry import tools_registry
from src.classifiers.hierarchical_classifier import HierarchicalClassifier
from src.routing.routing_strategy import HierarchicalRoutingStrategy


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
    
    def __init__(self, enable_hierarchical_routing: Optional[bool] = None, squad_config_path: Optional[str] = None):
        """
        Initialize the GRC Agent Squad.
        
        Args:
            enable_hierarchical_routing: Whether to use hierarchical routing (default: from settings)
            squad_config_path: Path to squad configuration file (default: from settings)
        """
        self.logger = structlog.get_logger(__name__)
        
        # Agent squad will be initialized in _initialize_grc_agents
        self.squad = None
        
        # Agent configurations for GRC
        self.agent_configs = {}
        
        # Routing configuration - use settings defaults if not provided
        self.enable_hierarchical_routing = enable_hierarchical_routing if enable_hierarchical_routing is not None else settings.enable_hierarchical_routing
        self.squad_config_path = squad_config_path or settings.squad_config_path
        
        # Initialize GRC agents
        self._initialize_grc_agents()
        
        routing_type = "hierarchical" if enable_hierarchical_routing else "standard"
        self.logger.info("GRC Agent Squad initialized with Bedrock built-in memory", 
                        agent_count=len(self.squad.agents) if self.squad else 0,
                        routing_type=routing_type)
    
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
        
        # Create classifier - hierarchical or standard based on configuration
        if self.enable_hierarchical_routing:
            self.logger.info("Creating hierarchical classifier with settings...")
            
            # Load squad configuration
            try:
                squad_config = HierarchicalClassifier.load_squad_config(self.squad_config_path)
                self.logger.info("Loaded squad configuration", 
                                squad_name=squad_config.name,
                                tier_count=len(squad_config.tiers))
            except Exception as e:
                self.logger.warning(f"Failed to load squad config, falling back to standard classifier: {e}")
                self.enable_hierarchical_routing = False
                squad_config = None
            
            if squad_config:
                classifier = HierarchicalClassifier(
                    BedrockClassifierOptions(
                        model_id=settings.classifier_model_id,
                        client=bedrock_client,
                        inference_config={
                            'maxTokens': settings.classifier_max_tokens,
                            'temperature': settings.classifier_temperature,
                            'topP': settings.classifier_top_p
                        }
                    ),
                    squad_config
                )
            else:
                # Fallback to standard classifier
                classifier = BedrockClassifier(BedrockClassifierOptions(
                    model_id=settings.classifier_model_id,
                    client=bedrock_client,
                    inference_config={
                        'maxTokens': settings.classifier_max_tokens,
                        'temperature': settings.classifier_temperature,
                        'topP': settings.classifier_top_p
                    }
                ))
        else:
            self.logger.info("Creating standard Bedrock classifier with settings...")
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
            tools_config = None
            configured_tools = config.config_data.get('tools', [])
            
            if configured_tools:
                # Get tools from registry based on agent config
                agent_tools = tools_registry.get_tools_for_agent(configured_tools)
                
                if agent_tools:
                    tools_config = {
                        'tool': AgentTools(agent_tools),
                        'toolMaxRecursions': 5,
                    }
                    self.logger.info(f"Added {len(agent_tools)} tools to agent '{agent_id}'")
            
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
    
    def _get_routing_method(self, selected_agent_id: str, confidence: Optional[float]) -> Optional[str]:
        """
        Get the routing method for display in the agent header.
        
        Args:
            selected_agent_id: ID of the selected agent
            confidence: Confidence score from classification
            
        Returns:
            Routing method string (e.g., "specialist", "supervisor", "fallback")
        """
        if not self.enable_hierarchical_routing:
            return None
            
        # Determine routing method based on agent type and confidence
        if confidence is not None:
            # Determine routing tier based on confidence and agent
            if selected_agent_id == "supervisor_grc":
                if confidence >= 0.6:
                    return "supervisor"
                else:
                    return "fallback"
            else:
                # Specialist agents
                if confidence >= 0.8:
                    return "specialist"
                elif confidence >= 0.6:
                    return "escalated"
                else:
                    return "fallback"
        else:
            # No confidence available - likely direct routing or fallback
            if selected_agent_id == "supervisor_grc":
                return "fallback"
            else:
                return "direct"
    
    
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
                
                # Debug logging for confidence issues
                self.logger.debug(f"Confidence extraction: raw={raw_confidence}, processed={confidence}")
            
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
            
            # For hierarchical routing, modify the agent name to include routing method
            # This integrates with the existing header format in index.html
            response_mode = context.get("response_type", "display") if context else "display"
            if (self.enable_hierarchical_routing and 
                selected_agent_name != "No Agent" and 
                response_mode == "display"):
                routing_method = self._get_routing_method(selected_agent_id, confidence)
                if routing_method:
                    # Modify the agent name to include routing method
                    # This will appear in the single header line as: "🤖 Dr. Morgan • specialist"
                    selected_agent_name = f"{selected_agent_name} • {routing_method}"
            
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
        try:
            # Get the list of available tools from the tools registry
            available_tools = tools_registry.list_available_tools()
            
            return {
                "total_agents": len(self.agent_configs),
                "active_agents": len(self.agent_configs),  # All loaded agents are considered active
                "memory_type": "bedrock_built_in",
                "agent_types": list(self.agent_configs.keys()),
                "available_tools": available_tools
            }
        except Exception as e:
            self.logger.error(f"Error getting squad stats: {e}")
            # Return a minimal valid response instead of raising an exception
            return {
                "total_agents": 0,
                "active_agents": 0,
                "memory_type": "unknown",
                "agent_types": [],
                "available_tools": []
            }
