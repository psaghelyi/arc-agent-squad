"""
GRC Agent Squad API routes for agent management and chat functionality.
Uses agent-squad framework with Bedrock built-in memory for conversation persistence.
"""

import structlog
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...services.grc_agent_squad import GRCAgentSquad
from ...tools.tool_registry import get_default_registry
from ...models.agent_models import AgentCapability





# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None
    response_type: Optional[str] = "display"  # "display" or "voice"


class ChatResponse(BaseModel):
    message: str
    agent_name: str
    session_id: str
    response_type: str  # "display" or "voice"
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    audio_data: Optional[str] = None  # Base64 encoded audio (only for voice responses)
    audio_format: Optional[str] = None
    voice_id: Optional[str] = None
    has_voice: Optional[bool] = False


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    personality: str
    capabilities: List[str]
    status: str
    created_at: str


# Initialize router
router = APIRouter()
logger = structlog.get_logger(__name__)

# Global GRC Agent Squad instance
_grc_squad_instance: Optional[GRCAgentSquad] = None


def get_grc_squad() -> GRCAgentSquad:
    """Get or create the GRC Agent Squad instance."""
    global _grc_squad_instance
    if _grc_squad_instance is None:
        tool_registry = get_default_registry()
        _grc_squad_instance = GRCAgentSquad(tool_registry=tool_registry)
    return _grc_squad_instance


@router.get("/")
async def list_agents(grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """Get list of all available GRC agents."""
    try:
        agents = await grc_squad.list_agents()
        return {
            "success": True,
            "agents": agents,
            "message": f"Found {len(agents)} GRC agents"
        }
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/grc/agent-types") 
async def get_grc_agent_types(grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """Get information about GRC agent types and their specializations."""
    try:
        from ...agents.agent_config_loader import get_default_config_registry
        
        agents = await grc_squad.list_agents()
        agent_types = []
        
        # Get file-based configuration registry
        config_registry = get_default_config_registry()
        
        for agent in agents:
            agent_id = agent.get("personality", "")
            config_class = config_registry.get_config(agent_id)
            
            agent_types.append({
                "id": agent["id"],
                "name": agent["name"], 
                "personality": agent["personality"],
                "description": agent["description"],
                "capabilities": agent["capabilities"],
                "use_cases": config_class.get_use_cases() if config_class else _get_agent_use_cases(agent["personality"])
            })
        
        return {
            "success": True,
            "agent_types": agent_types,
            "total": len(agent_types)
        }
    except Exception as e:
        logger.error("Failed to get GRC agent types", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get agent types: {str(e)}")


def _get_agent_use_cases(personality: str) -> List[str]:
    """Get use cases for each agent personality."""
    use_cases_map = {
        "empathetic_interviewer": [
            "Compliance interviews",
            "Risk assessment sessions", 
            "Stakeholder consultations",
            "Documentation reviews",
            "Control testing interviews"
        ],
        "authoritative_compliance": [
            "Regulatory interpretation",
            "Compliance status assessments",
            "Policy guidance",
            "Formal compliance reporting", 
            "Regulatory change analysis"
        ],
        "analytical_risk_expert": [
            "Risk modeling",
            "Control gap analysis",
            "Threat assessment",
            "Business impact analysis",
            "Risk register maintenance",
            "Mitigation strategy development"
        ],
        "strategic_governance": [
            "Governance framework design",
            "Policy development",
            "Board reporting",
            "Stakeholder engagement",
            "Governance maturity assessment",
            "Strategic planning"
        ]
    }
    return use_cases_map.get(personality, [])


@router.get("/{agent_id}")
async def get_agent(agent_id: str, grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """Get information about a specific GRC agent."""
    try:
        agent_info = await grc_squad.get_agent_info(agent_id)
        if not agent_info:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "agent": agent_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.post("/chat")
async def chat_with_agents(
    request: ChatRequest,
    grc_squad: GRCAgentSquad = Depends(get_grc_squad)
) -> ChatResponse:
    """
    Chat with the GRC Agent Squad in two-phase communication:
    - response_type='display': Get rich markdown for visual display
    - response_type='voice': Get clean text for voice synthesis
    """
    try:
        from src.services.voice_processor import VoiceProcessor
        from src.models.agent_models import AgentCapability
        
        # Build context with response type for agent
        enhanced_context = request.context or {}
        enhanced_context["response_type"] = request.response_type
        
        response = await grc_squad.process_request(
            user_input=request.message,
            session_id=request.session_id or "default",
            context=enhanced_context
        )
        
        if not response.get("success"):
            raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
        
        agent_selection = response.get("agent_selection", {})
        agent_response = response.get("agent_response", {})
        agent_name = agent_selection.get("agent_name", "")
        
        # Map agent name to agent ID for voice processing
        agent_id_map = {
            "Emma - Information Collector": "empathetic_interviewer",
            "Dr. Morgan - Compliance Authority": "authoritative_compliance", 
            "Alex - Risk Analysis Expert": "analytical_risk_expert",
            "Sam - Governance Strategist": "strategic_governance",
            # Also handle potential variations
            "Emma": "empathetic_interviewer",
            "Dr. Morgan": "authoritative_compliance",
            "Alex": "analytical_risk_expert", 
            "Sam": "strategic_governance"
        }
        agent_id = agent_id_map.get(agent_name)
        
        # If we didn't find a mapping, try to extract from the agent_selection
        if not agent_id and agent_selection.get("agent_id") != "auto_selected":
            agent_id = agent_selection.get("agent_id")
        
        # Get the response content
        raw_response = agent_response.get("response", "")
        
        # Check if agent has voice processing capability
        has_voice = False
        audio_data = None
        audio_format = None
        voice_id = None
        
        if agent_id:
            agent_info = await grc_squad.get_agent_info(agent_id)
            if agent_info:
                capabilities = agent_info.get("capabilities", [])
                # Check for voice processing capability (handle both enum and string formats)
                has_voice = (
                    AgentCapability.VOICE_PROCESSING in capabilities or
                    "voice_processing" in capabilities or
                    "VOICE_PROCESSING" in capabilities
                )
                
                # Only synthesize voice for voice responses
                if request.response_type == "voice" and has_voice:
                    try:
                        voice_processor = VoiceProcessor()
                        tts_result = await voice_processor.synthesize_agent_response(
                            text=raw_response,
                            agent_personality=agent_id,
                            session_id=request.session_id or "default"
                        )
                        
                        if tts_result.get('success'):
                            audio_data = tts_result['audio_data']
                            audio_format = tts_result['audio_format']
                            voice_id = tts_result['voice_id']
                        else:
                            logger.warning(f"TTS failed for agent {agent_id}: {tts_result.get('error')}")
                            
                    except Exception as voice_error:
                        logger.error(f"Voice synthesis error for agent {agent_id}: {voice_error}")
                        # Continue without voice - don't fail the entire request
        
        return ChatResponse(
            message=raw_response or "No response generated",
            agent_name=agent_selection.get("agent_name", "GRC Agent Squad"),
            session_id=response.get("session_id", request.session_id or "default"),
            response_type=request.response_type,
            confidence=agent_selection.get("confidence"),
            reasoning=agent_selection.get("reasoning"),
            audio_data=audio_data,
            audio_format=audio_format,
            voice_id=voice_id,
            has_voice=has_voice
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process chat request", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.get("/stats")
async def get_squad_stats(grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """Get statistics about the GRC Agent Squad."""
    try:
        stats = await grc_squad.get_squad_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error("Failed to get squad stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/tools")
async def get_available_tools(grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """Get list of available tools for the GRC agents."""
    try:
        tools = grc_squad.get_available_tools()
        return {
            "success": True,
            "tools": tools,
            "total": len(tools)
        }
    except Exception as e:
        logger.error("Failed to get available tools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")


# Legacy endpoints for API compatibility (simplified)
@router.get("/{agent_id}/conversations")
async def get_agent_conversations(
    agent_id: str,
    limit: int = 10,
    grc_squad: GRCAgentSquad = Depends(get_grc_squad)
):
    """Get conversation history for a specific agent (legacy endpoint - now handled by Bedrock)."""
    try:
        # Note: Conversation history is now managed by Bedrock's built-in memory
        # This endpoint returns a simplified response for API compatibility
        agent_info = await grc_squad.get_agent_info(agent_id)
        if not agent_info:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            
        return {
            "agent_id": agent_id,
            "conversations": [],  # Bedrock manages session history internally
            "total": 0,
            "message": "Conversation history is now managed by Bedrock's built-in memory system",
            "memory_type": "bedrock_built_in"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversations", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")


@router.get("/capabilities/list")
async def get_agent_capabilities():
    """Get list of available agent capabilities."""
    capabilities = [
        {
            "value": cap.value,
            "name": cap.value.replace("_", " ").title(),
            "description": f"Agent capability for {cap.value.replace('_', ' ')}"
        }
        for cap in AgentCapability
    ]
    
    return {
        "capabilities": capabilities,
        "total": len(capabilities)
    }


@router.get("/personalities/presets")
async def get_personality_presets():
    """Get available personality presets."""
    from src.models.agent_models import PERSONALITY_PRESETS
    
    presets = {}
    for personality_type, config in PERSONALITY_PRESETS.items():
        presets[personality_type.value] = {
            "type": personality_type.value,
            "tone": config.tone.value,
            "greeting": config.greeting_message,
            "style": config.response_style,
            "politeness": config.politeness_level,
            "enthusiasm": config.enthusiasm_level,
            "uses_emojis": config.use_emojis,
            "asks_follow_ups": config.asks_follow_up_questions,
            "provides_examples": config.provides_examples,
            "shows_empathy": config.shows_empathy,
            "is_proactive": config.is_proactive
        }
    
    return {
        "presets": presets,
        "total": len(presets)
    }


@router.get("/config/details")
async def get_detailed_agent_config(grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """Get detailed configuration information for all agents including model IDs, prompts, and settings."""
    try:
        from ...agents.agent_config_loader import get_default_config_registry
        
        agents = await grc_squad.list_agents()
        detailed_configs = []
        
        # Get file-based configuration registry
        config_registry = get_default_config_registry()
        
        # Get detailed configuration for each agent
        for agent in agents:
            agent_id = agent.get("agent_id", "")
            config_class = config_registry.get_config(agent_id)
            
            if config_class:
                # Get system prompt
                system_prompt = config_class.get_system_prompt()
                
                # Get voice settings
                voice_settings = config_class.get_voice_settings()
                
                # Get specialized tools
                specialized_tools = config_class.get_specialized_tools()
                
                # Get model settings
                model_settings = config_class.get_model_settings()
                
                detailed_config = {
                    "id": agent.get("agent_id", ""),
                    "name": agent["name"],
                    "description": agent["description"],
                    "personality": agent.get("personality", {}), 
                    "capabilities": agent["capabilities"],
                    "status": agent.get("status", "active"),
                    "created_at": agent.get("created_at", ""),
                    
                    # Detailed configuration from file
                    "model_id": model_settings.get("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
                    "model_provider": model_settings.get("model_provider", "AWS Bedrock"),
                    "inference_config": model_settings.get("inference_config", {
                        "maxTokens": 4096,
                        "temperature": 0.7,
                        "topP": 0.9
                    }),
                    "memory_enabled": model_settings.get("memory_enabled", True),
                    "streaming": model_settings.get("streaming", False),
                    
                    # Voice configuration
                    "voice_settings": voice_settings,
                    "voice_enabled": (
                        "VOICE_PROCESSING" in agent["capabilities"] or 
                        "voice_processing" in agent["capabilities"]
                    ),
                    
                    # System prompt and role
                    "system_prompt": system_prompt,
                    "system_prompt_length": len(system_prompt),
                    
                    # Tools and capabilities
                    "specialized_tools": specialized_tools,
                    "tool_count": len(specialized_tools),
                    
                    # Role-specific information from config file
                    "use_cases": config_class.get_use_cases(),
                    "primary_role": _get_agent_primary_role(agent_id),
                    
                    # Technical details
                    "conversation_memory": True,
                    "session_persistence": True,
                    "framework": model_settings.get("framework", "agent-squad"),
                    "llm_framework": model_settings.get("llm_framework", "BedrockLLMAgent")
                }
                
                detailed_configs.append(detailed_config)
        
        return {
            "success": True,
            "detailed_configs": detailed_configs,
            "total": len(detailed_configs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get detailed agent config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get detailed agent config: {str(e)}")


def _get_agent_primary_role(personality: str) -> str:
    """Get the primary role description for each agent personality."""
    role_map = {
        "empathetic_interviewer": "Information Collection & Interview Specialist",
        "empathetic_interviewer_executive": "Senior Information Collection & Executive Interview Specialist",
        "authoritative_compliance": "Regulatory Compliance Authority",
        "authoritative_compliance_executive": "Chief Compliance Officer & Regulatory Authority",
        "analytical_risk_expert": "Risk Assessment & Analysis Expert",
        "analytical_risk_expert_executive": "Chief Risk Officer & Strategic Risk Management Expert", 
        "strategic_governance": "Governance Strategy & Policy Specialist",
        "strategic_governance_executive": "Chief Governance Officer & Strategic Governance Authority"
    }
    return role_map.get(personality, "General GRC Assistant")


 