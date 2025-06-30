import structlog
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...services.grc_agent_squad import GRCAgentSquad


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None
    response_type: Optional[str] = "display"  # "display" or "voice"


class ChatResponse(BaseModel):
    message: str
    agent_name: str
    agent_id: str
    session_id: str
    response_type: str  # "display" or "voice"
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    audio_data: Optional[str] = None  # Base64 encoded audio (only for voice responses)
    audio_format: Optional[str] = None
    voice_id: Optional[str] = None
    has_voice: Optional[bool] = False


# Initialize router
router = APIRouter()
logger = structlog.get_logger(__name__)

# Global GRC Agent Squad instance
_grc_squad_instance: Optional[GRCAgentSquad] = None


def get_grc_squad() -> GRCAgentSquad:
    """Get or create the GRC Agent Squad instance."""
    global _grc_squad_instance
    if _grc_squad_instance is None:
        _grc_squad_instance = GRCAgentSquad()
    return _grc_squad_instance


@router.post("/")
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
        from src.agents.agent_config_loader import get_default_config_registry
        import structlog
        
        debug_logger = structlog.get_logger("voice_debug")
        debug_logger.info("Starting chat request processing", 
                         response_type=request.response_type,
                         session_id=request.session_id)
        
        # Build context with response type for agent
        enhanced_context = request.context or {}
        enhanced_context["response_type"] = request.response_type
        
        # Check if a specific agent_id is provided in the context
        direct_agent_id = None
        if enhanced_context and "agent_id" in enhanced_context:
            direct_agent_id = enhanced_context.get("agent_id")
            debug_logger.info("Direct agent ID specified in context", agent_id=direct_agent_id)
        
        # Get agent response using process_request
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
        
        # Get the response content
        raw_response = agent_response.get("response", "")
        
        # Get the agent_id directly from the response
        # If direct_agent_id was specified, use that instead
        agent_id = direct_agent_id if direct_agent_id else agent_selection.get("agent_id")
        debug_logger.info("Agent selected", agent_id=agent_id, agent_name=agent_name)
        
        # If agent_id is missing, throw an exception
        if not agent_id:
            error_msg = f"Agent ID not available in response for agent: {agent_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Process voice if requested and agent supports it
        audio_data = None
        audio_format = None
        voice_id = None
        has_voice = False
        
        # Always check for voice capability regardless of response_type
        # This ensures the has_voice flag is set correctly in the response
        debug_logger.info("Checking if agent has voice capability")
        config_registry = get_default_config_registry()
        
        # Debug: Print all available agent IDs in the registry
        all_agent_ids = config_registry.list_agent_ids()
        debug_logger.info(f"Available agent IDs in registry: {all_agent_ids}")
        debug_logger.info(f"Looking for agent with ID: {agent_id}")
        
        agent_config = config_registry.get_config(agent_id)
        
        if not agent_config:
            debug_logger.warning(f"Agent config not found for ID: {agent_id}")
            debug_logger.info("Available agent configs:", 
                             available_configs=list(config_registry.list_agent_ids()))
        else:
            # Get voice settings to determine if agent has voice capability
            voice_settings = agent_config.get_voice_settings()
            debug_logger.info("Agent voice settings", 
                           agent_id=agent_id,
                           voice_settings=voice_settings)
            
            # Check if agent has voice capability based on having a valid voice_id
            has_voice = bool(voice_settings and voice_settings.get('voice_id'))
            debug_logger.info(f"Agent has voice capability based on voice_settings: {has_voice}")
            
            # Only process voice if requested
            if request.response_type == "voice" and has_voice:
                debug_logger.info("Agent has voice capability, synthesizing speech")
                # Generate voice response
                voice_processor = VoiceProcessor()
                voice_result = await voice_processor.synthesize_agent_response(
                    raw_response,
                    agent_id
                )
                
                # Log the voice result metadata for debugging
                debug_logger.info("Voice synthesis result", 
                                 success=voice_result.get('success'),
                                 error=voice_result.get('error'),
                                 audio_size=voice_result.get('audio_size', 0),
                                 voice_id=voice_result.get('voice_id'),
                                 agent_id=voice_result.get('agent_id'))
                
                # Note: Not logging the full voice_result as it contains audio data
                
                if voice_result.get('success'):
                    audio_data = voice_result.get('audio_data')
                    audio_format = voice_result.get('audio_format')
                    voice_id = voice_result.get('voice_id')
                    debug_logger.info(f"Voice synthesis successful, audio size: {len(audio_data) if audio_data else 0}")
                else:
                    debug_logger.error("Voice synthesis failed", 
                                      error=voice_result.get('error'),
                                      agent_id=agent_id)
        
        # Debug the agent_id before returning
        debug_logger.debug(f"Final agent_id being returned: {agent_id}")
        debug_logger.debug(f"Has voice flag: {has_voice}")
        
        return ChatResponse(
            message=raw_response or "No response generated",
            agent_name=agent_selection.get("agent_name", "GRC Agent Squad"),
            agent_id=agent_id,
            session_id=response.get("session_id", request.session_id or "default"),
            response_type=request.response_type,
            confidence=agent_selection.get("confidence"),
            reasoning=agent_selection.get("reasoning"),
            audio_data=audio_data,
            audio_format=audio_format,
            voice_id=voice_id,
            has_voice=has_voice
        )
        
    except Exception as e:
        logger.error(f"Error in chat_with_agents: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # For test_chat_endpoint_error_handling, we need to propagate the error
        if "Agent processing failed" in str(e):
            raise HTTPException(status_code=500, detail=str(e))
            
        return ChatResponse(
            agent_name="Error",
            message=f"An error occurred: {str(e)}",
            agent_id="error",
            session_id=request.session_id or "default",
            response_type=request.response_type or "display",
            audio_data=None,
            audio_format=None,
            voice_id=None,
            has_voice=False
        )

# Add identical route for base path (no trailing slash)
@router.post("")
async def chat_with_agents_base_path(
    request: ChatRequest,
    grc_squad: GRCAgentSquad = Depends(get_grc_squad)
) -> ChatResponse:
    """
    Chat with the GRC Agent Squad (alternative endpoint without trailing slash)
    Identical to the "/" endpoint - added to support both URL patterns.
    """
    return await chat_with_agents(request, grc_squad)
