"""
Agent orchestrator service for managing and selecting agents.

This service acts as the single point of contact for all agent interactions,
managing multiple personality agents and selecting the most appropriate one
for each request based on context and user preferences.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
from agent_squad.orchestrator import AgentSquad
from agent_squad.agents import Agent

from ..models.agent_models import (
    AgentConfiguration,
    AgentInstance,
    AgentSelectionCriteria,
    OrchestratorRequest,
    OrchestratorResponse,
    AgentPersonality,
    AgentCapability,
    AgentStatus,
    PERSONALITY_PRESETS
)
from ..agents.personality_agent import PersonalityAgent
from ..services.memory_service import MemoryService


class AgentOrchestrator:
    """Orchestrator for managing multiple personality agents."""
    
    def __init__(self, memory_service: MemoryService):
        """
        Initialize the agent orchestrator.
        
        Args:
            memory_service: Service for managing conversation memory
        """
        self.memory_service = memory_service
        self.logger = structlog.get_logger(__name__)
        
        # Agent management
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_configs: Dict[str, AgentConfiguration] = {}
        
        # Agent squad orchestrator from agent-squad
        self.agent_squad = AgentSquad()
        
        # Default selection weights
        self.selection_weights = {
            "personality_match": 0.3,
            "capability_match": 0.4,
            "availability": 0.2,
            "performance": 0.1
        }
        
        self.logger.info("Agent orchestrator initialized")
    
    async def initialize_default_agents(self) -> None:
        """Initialize default personality agents."""
        default_agents = [
            {
                "name": "Emma the Helper",
                "description": "A kind and helpful assistant who loves to provide detailed explanations",
                "personality": AgentPersonality.KIND_HELPFUL,
                "capabilities": [AgentCapability.QUESTION_ANSWERING, AgentCapability.TASK_ASSISTANCE, AgentCapability.VOICE_PROCESSING]
            },
            {
                "name": "Alex the Direct",
                "description": "A straightforward assistant focused on quick, efficient answers",
                "personality": AgentPersonality.TO_THE_POINT,
                "capabilities": [AgentCapability.QUESTION_ANSWERING, AgentCapability.TECHNICAL_SUPPORT]
            },
            {
                "name": "Dr. Morgan",
                "description": "A professional assistant for formal business interactions",
                "personality": AgentPersonality.PROFESSIONAL,
                "capabilities": [AgentCapability.QUESTION_ANSWERING, AgentCapability.DATA_ANALYSIS, AgentCapability.CUSTOMER_SUPPORT]
            },
            {
                "name": "Sam the Buddy",
                "description": "A casual, friendly assistant who makes conversations feel natural",
                "personality": AgentPersonality.CASUAL_FRIENDLY,
                "capabilities": [AgentCapability.TEXT_CHAT, AgentCapability.CREATIVE_WRITING, AgentCapability.VOICE_PROCESSING]
            }
        ]
        
        for agent_config in default_agents:
            await self.create_agent(
                name=agent_config["name"],
                description=agent_config["description"],
                personality_type=agent_config["personality"],
                capabilities=agent_config["capabilities"]
            )
        
        self.logger.info("Default agents initialized", count=len(default_agents))
    
    async def create_agent(
        self,
        name: str,
        description: str,
        personality_type: AgentPersonality,
        capabilities: List[AgentCapability],
        **kwargs
    ) -> str:
        """
        Create a new agent with specified configuration.
        
        Args:
            name: Agent name
            description: Agent description
            personality_type: Personality type
            capabilities: List of agent capabilities
            **kwargs: Additional configuration options
            
        Returns:
            Agent ID
        """
        try:
            # Get personality preset
            personality_config = PERSONALITY_PRESETS.get(personality_type)
            if not personality_config:
                raise ValueError(f"Unknown personality type: {personality_type}")
            
            # Create agent configuration
            config = AgentConfiguration(
                name=name,
                description=description,
                personality=personality_config,
                capabilities=capabilities,
                **kwargs
            )
            
            # Create personality agent
            personality_agent = PersonalityAgent(
                config=config,
                memory_service=self.memory_service
            )
            
            # Create agent instance
            instance = AgentInstance(
                config=config,
                status=AgentStatus.ACTIVE
            )
            
            # Store agent
            self.agents[config.id] = instance
            self.agent_configs[config.id] = config
            
            # Add to agent squad orchestrator
            self.agent_squad.add_agent(personality_agent)
            
            self.logger.info("Agent created successfully",
                           agent_id=config.id,
                           name=name,
                           personality=personality_type.value)
            
            return config.id
            
        except Exception as e:
            self.logger.error("Failed to create agent", 
                            name=name,
                            error=str(e))
            raise
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            if agent_id not in self.agents:
                return False
            
            # Remove from orchestrator
            # Note: agent-squad doesn't have a direct remove method in the current version
            # In a real implementation, you might need to recreate the orchestrator
            
            # Remove from local storage
            del self.agents[agent_id]
            del self.agent_configs[agent_id]
            
            self.logger.info("Agent deleted", agent_id=agent_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to delete agent", 
                            agent_id=agent_id,
                            error=str(e))
            return False
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all available agents.
        
        Returns:
            List of agent information
        """
        agents_info = []
        
        for agent_id, instance in self.agents.items():
            config = instance.config
            agents_info.append({
                "id": agent_id,
                "name": config.name,
                "description": config.description,
                "personality": config.personality.personality_type.value,
                "tone": config.personality.tone.value,
                "capabilities": [cap.value for cap in config.capabilities],
                "status": instance.status.value,
                "current_sessions": len(instance.current_sessions),
                "total_conversations": instance.total_conversations,
                "last_interaction": instance.last_interaction.isoformat() if instance.last_interaction else None,
                "memory_enabled": config.memory_enabled,
                "voice_enabled": config.voice_enabled,
                "created_at": config.created_at.isoformat() if config.created_at else ""
            })
        
        return agents_info
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent information or None if not found
        """
        if agent_id not in self.agents:
            return None
        
        instance = self.agents[agent_id]
        config = instance.config
        
        # Get conversation statistics
        conversations = await self.memory_service.get_recent_conversations(agent_id)
        
        return {
            "id": agent_id,
            "name": config.name,
            "description": config.description,
            "personality": {
                "type": config.personality.personality_type.value,
                "tone": config.personality.tone.value,
                "greeting": config.personality.greeting_message,
                "traits": {
                    "politeness_level": config.personality.politeness_level,
                    "enthusiasm_level": config.personality.enthusiasm_level,
                    "uses_emojis": config.personality.use_emojis,
                    "asks_follow_up_questions": config.personality.asks_follow_up_questions,
                    "provides_examples": config.personality.provides_examples,
                    "shows_empathy": config.personality.shows_empathy,
                    "is_proactive": config.personality.is_proactive
                }
            },
            "capabilities": [cap.value for cap in config.capabilities],
            "status": instance.status.value,
            "statistics": {
                "current_sessions": len(instance.current_sessions),
                "total_conversations": instance.total_conversations,
                "recent_conversations": len(conversations),
                "last_interaction": instance.last_interaction
            },
            "configuration": {
                "memory_enabled": config.memory_enabled,
                "voice_enabled": config.voice_enabled,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "model_id": config.model_id
            },
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
    
    async def select_agent(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """
        Select the best agent for a request.
        
        Args:
            request: Orchestrator request
            
        Returns:
            Orchestrator response with selected agent
        """
        try:
            # Analyze request to determine requirements
            analysis = await self._analyze_request(request)
            
            # Score all available agents
            agent_scores = {}
            for agent_id, instance in self.agents.items():
                if instance.status == AgentStatus.ACTIVE:
                    score = await self._score_agent(instance, analysis, request)
                    agent_scores[agent_id] = score
            
            if not agent_scores:
                raise Exception("No active agents available")
            
            # Select best agent
            best_agent_id = max(agent_scores, key=agent_scores.get)
            best_score = agent_scores[best_agent_id]
            
            # Get alternative agents
            sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
            alternatives = [agent_id for agent_id, _ in sorted_agents[1:4]]  # Top 3 alternatives
            
            config = self.agent_configs[best_agent_id]
            
            response = OrchestratorResponse(
                selected_agent_id=best_agent_id,
                agent_name=config.name,
                confidence_score=best_score,
                reasoning=self._generate_selection_reasoning(config, analysis),
                alternative_agents=alternatives
            )
            
            self.logger.info("Agent selected",
                           selected_agent=best_agent_id,
                           agent_name=config.name,
                           confidence=best_score,
                           alternatives=len(alternatives))
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to select agent", error=str(e))
            raise
    
    async def _analyze_request(self, request: OrchestratorRequest) -> Dict[str, Any]:
        """Analyze request to determine requirements."""
        analysis = {
            "text_length": len(request.user_input),
            "is_question": "?" in request.user_input,
            "is_urgent": any(word in request.user_input.lower() for word in ["urgent", "asap", "quickly", "fast"]),
            "is_emotional": any(word in request.user_input.lower() for word in ["help", "please", "frustrated", "confused"]),
            "is_technical": any(word in request.user_input.lower() for word in ["code", "api", "technical", "debug", "error"]),
            "is_creative": any(word in request.user_input.lower() for word in ["write", "create", "story", "poem", "creative"]),
            "requires_empathy": any(word in request.user_input.lower() for word in ["sad", "upset", "worried", "anxious"]),
            "prefers_brief": any(word in request.user_input.lower() for word in ["brief", "short", "quick", "summary"])
        }
        
        return analysis
    
    async def _score_agent(self, instance: AgentInstance, analysis: Dict[str, Any], request: OrchestratorRequest) -> float:
        """Score an agent for a specific request."""
        score = 0.0
        config = instance.config
        personality = config.personality
        
        # Personality matching
        personality_score = 0.0
        
        if analysis["is_urgent"] or analysis["prefers_brief"]:
            if personality.personality_type == AgentPersonality.TO_THE_POINT:
                personality_score += 0.8
            elif personality.personality_type == AgentPersonality.PROFESSIONAL:
                personality_score += 0.6
        
        if analysis["requires_empathy"] or analysis["is_emotional"]:
            if personality.personality_type == AgentPersonality.KIND_HELPFUL:
                personality_score += 0.9
            elif personality.personality_type == AgentPersonality.CASUAL_FRIENDLY:
                personality_score += 0.7
        
        if analysis["is_technical"]:
            if personality.personality_type == AgentPersonality.PROFESSIONAL:
                personality_score += 0.8
            elif personality.personality_type == AgentPersonality.TO_THE_POINT:
                personality_score += 0.7
        
        if analysis["is_creative"]:
            if personality.personality_type == AgentPersonality.CASUAL_FRIENDLY:
                personality_score += 0.8
            elif personality.personality_type == AgentPersonality.KIND_HELPFUL:
                personality_score += 0.6
        
        # Capability matching
        capability_score = 0.0
        required_caps = request.selection_criteria.required_capabilities if request.selection_criteria else []
        
        if required_caps:
            matching_caps = set(config.capabilities) & set(required_caps)
            capability_score = len(matching_caps) / len(required_caps)
        else:
            # Default capability scoring based on analysis
            if analysis["is_technical"] and AgentCapability.TECHNICAL_SUPPORT in config.capabilities:
                capability_score += 0.3
            if analysis["is_creative"] and AgentCapability.CREATIVE_WRITING in config.capabilities:
                capability_score += 0.3
            if AgentCapability.QUESTION_ANSWERING in config.capabilities:
                capability_score += 0.2
            if AgentCapability.VOICE_PROCESSING in config.capabilities:
                capability_score += 0.2
        
        # Availability scoring
        availability_score = 1.0 - (len(instance.current_sessions) * 0.1)  # Penalty for busy agents
        availability_score = max(0.0, availability_score)
        
        # Performance scoring (based on usage and success)
        performance_score = min(1.0, instance.total_conversations / 100.0)  # More experienced = higher score
        
        # Calculate weighted final score
        final_score = (
            personality_score * self.selection_weights["personality_match"] +
            capability_score * self.selection_weights["capability_match"] +
            availability_score * self.selection_weights["availability"] +
            performance_score * self.selection_weights["performance"]
        )
        
        return min(1.0, final_score)
    
    def _generate_selection_reasoning(self, config: AgentConfiguration, analysis: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for agent selection."""
        reasons = []
        
        personality = config.personality.personality_type
        
        if analysis["is_urgent"] and personality == AgentPersonality.TO_THE_POINT:
            reasons.append("direct communication style for urgent request")
        elif analysis["requires_empathy"] and personality == AgentPersonality.KIND_HELPFUL:
            reasons.append("empathetic and supportive personality")
        elif analysis["is_technical"] and personality == AgentPersonality.PROFESSIONAL:
            reasons.append("professional tone suitable for technical queries")
        elif analysis["is_creative"] and personality == AgentPersonality.CASUAL_FRIENDLY:
            reasons.append("creative and friendly approach")
        
        if not reasons:
            reasons.append(f"{personality.value} personality matches the request context")
        
        return f"Selected {config.name} due to " + ", ".join(reasons)
    
    async def process_request(self, request: OrchestratorRequest) -> Dict[str, Any]:
        """
        Process a request through the orchestrator.
        
        Args:
            request: Orchestrator request
            
        Returns:
            Processing result with agent response
        """
        try:
            # Select best agent
            selection = await self.select_agent(request)
            
            # Get the selected agent
            agent_instance = self.agents[selection.selected_agent_id]
            
            # Update agent session tracking
            if request.session_id not in agent_instance.current_sessions:
                agent_instance.current_sessions.append(request.session_id)
            
            agent_instance.last_interaction = datetime.utcnow()
            
            # Create agent request (this would need to be adapted based on agent-squad's actual interface)
            # For now, we'll simulate the response
            
            # Get the personality agent
            personality_agent = None
            for agent_id, agent in self.agent_squad.agents.items():
                if hasattr(agent, 'config') and agent.config.id == selection.selected_agent_id:
                    personality_agent = agent
                    break
            
            if personality_agent:
                # Process request with the selected agent using agent-squad compatible method
                conversation_history = await self.memory_service.get_conversation(request.session_id)
                chat_history = []
                if conversation_history:
                    from agent_squad.types import ConversationMessage, ParticipantRole
                    for msg in conversation_history.messages[-10:]:  # Last 10 messages
                        role = ParticipantRole.USER if msg.role == "user" else ParticipantRole.ASSISTANT
                        chat_history.append(ConversationMessage(role=role, content=[{"text": msg.content}]))
                
                # Call the agent-squad compatible process_request method
                response_message = await personality_agent.process_request(
                    input_text=request.user_input,
                    user_id="default_user",  # Could be extracted from context if needed
                    session_id=request.session_id,
                    chat_history=chat_history,
                    additional_params=request.context
                )
                
                # Extract response text from ConversationMessage
                response_text = ""
                if hasattr(response_message, 'content') and response_message.content:
                    if isinstance(response_message.content, list) and len(response_message.content) > 0:
                        response_text = response_message.content[0].get("text", "")
                    else:
                        response_text = str(response_message.content)
                
                agent_response = type('AgentResponse', (), {
                    'success': True,
                    'data': {"response": response_text},
                    'error': None
                })()
                
                # Update statistics
                agent_instance.total_conversations += 1
                
                return {
                    "success": True,
                    "agent_selection": {
                        "agent_id": selection.selected_agent_id,
                        "agent_name": selection.agent_name,
                        "confidence": selection.confidence_score,
                        "reasoning": selection.reasoning
                    },
                    "agent_response": agent_response.data if agent_response.success else None,
                    "error": agent_response.error if not agent_response.success else None
                }
            else:
                raise Exception(f"Selected agent {selection.selected_agent_id} not found")
                
        except Exception as e:
            self.logger.error("Failed to process request", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        total_agents = len(self.agents)
        active_agents = sum(1 for instance in self.agents.values() if instance.status == AgentStatus.ACTIVE)
        total_conversations = sum(instance.total_conversations for instance in self.agents.values())
        
        # Get memory stats
        memory_stats = await self.memory_service.get_memory_stats()
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_conversations": total_conversations,
            "memory_stats": memory_stats,
            "selection_weights": self.selection_weights
        } 