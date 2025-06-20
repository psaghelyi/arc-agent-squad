"""
Personality-aware agent with memory capabilities.

This agent extends the base VoiceAgent with personality configuration,
memory management, and conversation history.
"""

import json
from typing import Dict, List, Optional, Any, Union, AsyncIterable

import boto3
import structlog
from agent_squad.agents import Agent, AgentOptions
from agent_squad.agents.agent import AgentOutputType
from agent_squad.types import ConversationMessage, ParticipantRole

from ..models.agent_models import (
    AgentConfiguration, 
    ConversationHistory,
    ChatMessage,
    AgentPersonality,
    AgentRequest,
    AgentResponse,
    PERSONALITY_PRESETS
)
from ..services.memory_service import MemoryService


class PersonalityAgent(Agent):
    """Agent with configurable personality and memory capabilities."""
    
    def __init__(
        self,
        config: AgentConfiguration,
        memory_service: MemoryService,
        region: str = "us-west-2"
    ):
        """
        Initialize the personality agent.
        
        Args:
            config: Agent configuration including personality
            memory_service: Service for managing conversation memory
            region: AWS region
        """
        # Create AgentOptions for the parent class
        agent_options = AgentOptions(
            name=config.name,
            description=config.description,
            save_chat=True,
            LOG_AGENT_DEBUG_TRACE=True
        )
        super().__init__(agent_options)
        
        self.config = config
        self.memory_service = memory_service
        self.region = region
        self.logger = structlog.get_logger(__name__)
        
        # Initialize AWS clients
        self._initialize_aws_clients()
        
        # Build system prompt from personality configuration
        self.system_prompt = self._build_system_prompt()
        
        self.logger.info("Personality agent initialized",
                        agent_id=self.config.id,
                        agent_name=self.config.name,
                        personality=self.config.personality.personality_type.value,
                        tone=self.config.personality.tone.value,
                        memory_enabled=self.config.memory_enabled)
    
    def _initialize_aws_clients(self) -> None:
        """Initialize AWS service clients."""
        try:
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
            self.transcribe_client = boto3.client('transcribe', region_name=self.region)
            self.polly_client = boto3.client('polly', region_name=self.region)
            
            self.logger.debug("AWS clients initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize AWS clients", error=str(e))
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from personality configuration."""
        personality = self.config.personality
        
        prompt_parts = [
            f"You are {self.config.name}, {self.config.description}",
            "",
            f"PERSONALITY: {personality.system_prompt}",
            "",
            f"COMMUNICATION STYLE:",
            f"- Tone: {personality.tone.value}",
            f"- Response style: {personality.response_style}",
            f"- Politeness level: {personality.politeness_level}/10",
            f"- Enthusiasm level: {personality.enthusiasm_level}/10",
            f"- Use emojis: {'Yes' if personality.use_emojis else 'No'}",
            f"- Max response length: {personality.max_response_length} characters",
            "",
            "BEHAVIORAL TRAITS:",
            f"- Ask follow-up questions: {'Yes' if personality.asks_follow_up_questions else 'No'}",
            f"- Provide examples: {'Yes' if personality.provides_examples else 'No'}",
            f"- Show empathy: {'Yes' if personality.shows_empathy else 'No'}",
            f"- Be proactive: {'Yes' if personality.is_proactive else 'No'}",
            "",
            "Always stay in character and maintain your personality throughout the conversation."
        ]
        
        return "\n".join(prompt_parts)
    
    async def process_request(
        self,
        input_text: str,
        user_id: str,
        session_id: str,
        chat_history: List[ConversationMessage],
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Union[ConversationMessage, AsyncIterable[AgentOutputType]]:
        """
        Process a user request and generate a response (required by Agent base class).
        
        Args:
            input_text: The user's input text
            user_id: Identifier for the user
            session_id: Identifier for the current session
            chat_history: List of previous messages in the conversation
            additional_params: Optional additional parameters
            
        Returns:
            ConversationMessage with the agent's response
        """
        self.logger.info("Processing request",
                        agent_id=self.config.id,
                        session_id=session_id,
                        user_id=user_id,
                        personality=self.config.personality.personality_type.value)
        
        try:
            # Get or create conversation history
            conversation = await self._get_or_create_conversation(session_id)
            
            # Add user message to conversation
            if input_text:
                await self.memory_service.add_message(session_id, "user", input_text)
            
            # Process with personality-aware response
            response_text = await self._generate_personality_response(conversation, input_text)
            
            # Add assistant response to conversation
            if response_text:
                await self.memory_service.add_message(session_id, "assistant", response_text)
            
            # Update agent statistics
            self.config.metadata["total_interactions"] = self.config.metadata.get("total_interactions", 0) + 1
            
            # Return ConversationMessage as expected by agent_squad
            return ConversationMessage(
                role=ParticipantRole.ASSISTANT,
                content=[{"text": response_text}]
            )
            
        except Exception as e:
            self.logger.error("Error processing request", 
                            agent_id=self.config.id,
                            error=str(e))
            # Return error message as ConversationMessage
            return ConversationMessage(
                role=ParticipantRole.ASSISTANT,
                content=[{"text": f"I apologize, but I encountered an error: {str(e)}"}]
            )
    
    async def process_agent_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process an incoming agent request with personality and memory.
        
        Args:
            request: The incoming agent request
            
        Returns:
            AgentResponse with processed result
        """
        session_id = getattr(request, 'session_id', 'default')
        user_input = getattr(request, 'content', '') or getattr(request, 'text', '')
        
        self.logger.info("Processing request with personality",
                        agent_id=self.config.id,
                        session_id=session_id,
                        personality=self.config.personality.personality_type.value)
        
        try:
            # Get or create conversation history
            conversation = await self._get_or_create_conversation(session_id)
            
            # Add user message to conversation
            if user_input:
                await self.memory_service.add_message(session_id, "user", user_input)
            
            # Process with personality-aware response
            response_text = await self._generate_personality_response(conversation, user_input)
            
            # Add assistant response to conversation
            if response_text:
                await self.memory_service.add_message(session_id, "assistant", response_text)
            
            # Update agent statistics
            self.config.metadata["total_interactions"] = self.config.metadata.get("total_interactions", 0) + 1
            
            return AgentResponse(
                success=True,
                data={
                    "response": response_text,
                    "agent_id": self.config.id,
                    "agent_name": self.config.name,
                    "personality": self.config.personality.personality_type.value,
                    "session_id": session_id,
                    "greeting": self.config.personality.greeting_message if not conversation.messages else None
                },
                agent_name=self.config.name
            )
            
        except Exception as e:
            self.logger.error("Error processing request", 
                            agent_id=self.config.id,
                            error=str(e))
            return AgentResponse(
                success=False,
                error=f"Agent {self.config.name} encountered an error: {str(e)}",
                agent_name=self.config.name
            )
    
    async def _get_or_create_conversation(self, session_id: str) -> ConversationHistory:
        """Get existing conversation or create a new one."""
        conversation = await self.memory_service.get_conversation(session_id)
        
        if not conversation:
            # Create new conversation with greeting
            conversation = await self.memory_service.create_conversation(
                session_id=session_id,
                agent_id=self.config.id,
                initial_message=self.system_prompt
            )
            
            # Add greeting message
            await self.memory_service.add_message(
                session_id, 
                "assistant", 
                self.config.personality.greeting_message
            )
        
        return conversation
    
    async def _generate_personality_response(self, conversation: ConversationHistory, user_input: str) -> str:
        """Generate response using personality configuration and conversation history."""
        try:
            # Get recent conversation context
            recent_messages = conversation.get_recent_messages(limit=self.config.max_memory_messages)
            
            # Build context for LLM
            context_messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            for msg in recent_messages:
                if msg.role != "system":  # Skip system messages in context
                    context_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add current user input if provided
            if user_input:
                context_messages.append({"role": "user", "content": user_input})
            
            # Generate response with Bedrock (mock implementation)
            response = await self._call_bedrock(context_messages)
            
            # Apply personality filters
            response = self._apply_personality_filters(response)
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to generate personality response", error=str(e))
            return self._get_fallback_response()
    
    async def _call_bedrock(self, messages: List[Dict]) -> str:
        """Call Amazon Bedrock for text generation."""
        # Mock implementation - replace with actual Bedrock call
        self.logger.debug("Calling Bedrock for response generation",
                         model_id=self.config.model_id,
                         message_count=len(messages))
        
        # In a real implementation, you would:
        # 1. Format messages for the specific model
        # 2. Call bedrock_client.invoke_model()
        # 3. Parse and return the response
        
        # Mock response based on personality
        personality = self.config.personality.personality_type
        
        if personality == AgentPersonality.KIND_HELPFUL:
            return "I'd be happy to help you with that! Let me provide you with a detailed explanation and some examples to make sure everything is clear. 😊"
        elif personality == AgentPersonality.TO_THE_POINT:
            return "Here's the answer to your question."
        elif personality == AgentPersonality.PROFESSIONAL:
            return "Thank you for your inquiry. I shall provide you with a comprehensive response to address your requirements."
        elif personality == AgentPersonality.CASUAL_FRIENDLY:
            return "Hey! Sure thing, I can totally help you out with that. Let me break it down for you! 👍"
        else:
            return "I understand your request and I'm here to assist you."
    
    def _apply_personality_filters(self, response: str) -> str:
        """Apply personality-specific filters to the response."""
        personality = self.config.personality
        
        # Apply length limit
        if len(response) > personality.max_response_length:
            response = response[:personality.max_response_length - 3] + "..."
        
        # Remove emojis if not allowed
        if not personality.use_emojis:
            # Simple emoji removal (in production, use a proper emoji library)
            import re
            response = re.sub(r'[😀-🙏🌀-🗿🚀-🛿☀-⭕]', '', response)
        
        return response.strip()
    
    def _get_fallback_response(self) -> str:
        """Get a fallback response based on personality."""
        personality = self.config.personality.personality_type
        
        fallback_responses = {
            AgentPersonality.KIND_HELPFUL: "I apologize, but I'm having trouble processing your request right now. Please try again, and I'll do my best to help you! 😊",
            AgentPersonality.TO_THE_POINT: "Error processing request. Please try again.",
            AgentPersonality.PROFESSIONAL: "I apologize for the inconvenience. There appears to be a technical issue. Please retry your request.",
            AgentPersonality.CASUAL_FRIENDLY: "Oops! Something went wrong on my end. Mind trying that again? 😅"
        }
        
        return fallback_responses.get(personality, "I'm sorry, but I encountered an error. Please try again.")
    
    async def get_conversation_history(self, session_id: str) -> Optional[ConversationHistory]:
        """Get conversation history for a session."""
        return await self.memory_service.get_conversation(session_id)
    
    async def get_recent_conversations(self, limit: int = 10) -> List[ConversationHistory]:
        """Get recent conversations for this agent."""
        return await self.memory_service.get_recent_conversations(self.config.id, limit)
    
    async def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        return await self.memory_service.delete_conversation(session_id)
    
    def get_personality_info(self) -> Dict[str, Any]:
        """Get personality configuration information."""
        return {
            "agent_id": self.config.id,
            "name": self.config.name,
            "personality_type": self.config.personality.personality_type.value,
            "tone": self.config.personality.tone.value,
            "greeting": self.config.personality.greeting_message,
            "traits": {
                "politeness_level": self.config.personality.politeness_level,
                "enthusiasm_level": self.config.personality.enthusiasm_level,
                "uses_emojis": self.config.personality.use_emojis,
                "asks_follow_up_questions": self.config.personality.asks_follow_up_questions,
                "provides_examples": self.config.personality.provides_examples,
                "shows_empathy": self.config.personality.shows_empathy,
                "is_proactive": self.config.personality.is_proactive
            },
            "capabilities": [cap.value for cap in self.config.capabilities],
            "memory_enabled": self.config.memory_enabled
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the agent and its dependencies."""
        health_status = {
            "agent_id": self.config.id,
            "agent_name": self.config.name,
            "status": "healthy",
            "personality": self.config.personality.personality_type.value,
            "memory_enabled": self.config.memory_enabled,
            "total_interactions": self.config.metadata.get("total_interactions", 0)
        }
        
        # Check memory service
        try:
            memory_stats = await self.memory_service.get_memory_stats()
            health_status["memory_service"] = "healthy" if memory_stats.get("redis_connected") else "unhealthy"
        except Exception as e:
            health_status["memory_service"] = "error"
            health_status["memory_error"] = str(e)
        
        return health_status 