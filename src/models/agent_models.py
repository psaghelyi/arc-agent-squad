"""
Data models for agent management and configuration.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentPersonality(str, Enum):
    """Predefined agent personality types."""
    KIND_HELPFUL = "kind_helpful"
    TO_THE_POINT = "to_the_point" 
    PROFESSIONAL = "professional"
    CASUAL_FRIENDLY = "casual_friendly"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SUPPORTIVE = "supportive"
    DIRECT = "direct"


class AgentTone(str, Enum):
    """Agent communication tone."""
    WARM = "warm"
    NEUTRAL = "neutral"
    FORMAL = "formal"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    ASSERTIVE = "assertive"


class AgentCapability(str, Enum):
    """Agent capabilities."""
    VOICE_PROCESSING = "voice_processing"
    TEXT_CHAT = "text_chat"
    QUESTION_ANSWERING = "question_answering"
    TASK_ASSISTANCE = "task_assistance"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    CUSTOMER_SUPPORT = "customer_support"
    TECHNICAL_SUPPORT = "technical_support"


class ChatMessage(BaseModel):
    """Individual chat message in conversation history."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Complete conversation history for an agent."""
    session_id: str
    agent_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> ChatMessage:
        """Add a new message to the conversation."""
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Get the most recent messages."""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages


class AgentPersonalityConfig(BaseModel):
    """Configuration for agent personality and behavior."""
    personality_type: AgentPersonality
    tone: AgentTone
    greeting_message: str
    system_prompt: str
    response_style: str
    max_response_length: int = 500
    use_emojis: bool = True
    politeness_level: int = Field(ge=1, le=10, default=7)  # 1=very direct, 10=very polite
    enthusiasm_level: int = Field(ge=1, le=10, default=5)  # 1=monotone, 10=very enthusiastic
    
    # Behavioral traits
    asks_follow_up_questions: bool = True
    provides_examples: bool = True
    shows_empathy: bool = True
    is_proactive: bool = False


class AgentConfiguration(BaseModel):
    """Complete agent configuration."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    personality: AgentPersonalityConfig
    capabilities: List[AgentCapability]
    
    # Technical configuration
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    max_tokens: int = 1000
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    
    # Memory and context
    memory_enabled: bool = True
    max_memory_messages: int = 50
    context_window_size: int = 4000
    
    # Voice settings (if voice-enabled)
    voice_enabled: bool = True
    voice_id: str = "Joanna"
    speech_rate: str = "medium"
    
    # Status and metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentStatus(str, Enum):
    """Agent operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentInstance(BaseModel):
    """Runtime instance of an agent."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    config: AgentConfiguration
    status: AgentStatus = AgentStatus.ACTIVE
    current_sessions: List[str] = Field(default_factory=list)
    total_conversations: int = 0
    last_interaction: Optional[datetime] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


class AgentSelectionCriteria(BaseModel):
    """Criteria for agent selection by orchestrator."""
    required_capabilities: List[AgentCapability] = Field(default_factory=list)
    preferred_personality: Optional[AgentPersonality] = None
    preferred_tone: Optional[AgentTone] = None
    session_context: Dict[str, Any] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)


class OrchestratorRequest(BaseModel):
    """Request to the orchestrator for agent selection."""
    user_input: str
    session_id: str
    selection_criteria: Optional[AgentSelectionCriteria] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class OrchestratorResponse(BaseModel):
    """Response from orchestrator with selected agent."""
    selected_agent_id: str
    agent_name: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    alternative_agents: List[str] = Field(default_factory=list)


class AgentRequest(BaseModel):
    """Simple agent request model."""
    session_id: str = "default"
    content: str = ""
    text: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    audio_data: Optional[bytes] = None


class AgentResponse(BaseModel):
    """Simple agent response model."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_name: str = ""


# Predefined personality configurations
PERSONALITY_PRESETS = {
    AgentPersonality.KIND_HELPFUL: AgentPersonalityConfig(
        personality_type=AgentPersonality.KIND_HELPFUL,
        tone=AgentTone.WARM,
        greeting_message="Hello! I'm here to help you with anything you need. How can I assist you today? 😊",
        system_prompt="You are a kind, helpful, and patient assistant. Always be encouraging and supportive. Take time to understand the user's needs and provide thorough, caring responses.",
        response_style="warm, encouraging, detailed explanations with examples",
        use_emojis=True,
        politeness_level=9,
        enthusiasm_level=7,
        asks_follow_up_questions=True,
        provides_examples=True,
        shows_empathy=True,
        is_proactive=True
    ),
    
    AgentPersonality.TO_THE_POINT: AgentPersonalityConfig(
        personality_type=AgentPersonality.TO_THE_POINT,
        tone=AgentTone.NEUTRAL,
        greeting_message="Hi. What do you need help with?",
        system_prompt="You are direct and efficient. Provide concise, accurate answers without unnecessary elaboration. Focus on solving the user's problem quickly.",
        response_style="brief, direct, solution-focused",
        use_emojis=False,
        politeness_level=4,
        enthusiasm_level=2,
        asks_follow_up_questions=False,
        provides_examples=False,
        shows_empathy=False,
        is_proactive=False
    ),
    
    AgentPersonality.PROFESSIONAL: AgentPersonalityConfig(
        personality_type=AgentPersonality.PROFESSIONAL,
        tone=AgentTone.FORMAL,
        greeting_message="Good day. I am here to provide professional assistance. How may I help you?",
        system_prompt="You are a professional, knowledgeable assistant. Maintain a formal tone while being helpful and thorough. Provide well-structured, authoritative responses.",
        response_style="formal, structured, comprehensive",
        use_emojis=False,
        politeness_level=8,
        enthusiasm_level=4,
        asks_follow_up_questions=True,
        provides_examples=True,
        shows_empathy=False,
        is_proactive=False
    ),
    
    AgentPersonality.CASUAL_FRIENDLY: AgentPersonalityConfig(
        personality_type=AgentPersonality.CASUAL_FRIENDLY,
        tone=AgentTone.CASUAL,
        greeting_message="Hey there! What's up? How can I help you out today? 👋",
        system_prompt="You are casual, friendly, and approachable. Use conversational language and be relatable. Make the interaction feel like talking to a good friend.",
        response_style="conversational, relatable, friendly",
        use_emojis=True,
        politeness_level=6,
        enthusiasm_level=8,
        asks_follow_up_questions=True,
        provides_examples=True,
        shows_empathy=True,
        is_proactive=True
    )
} 