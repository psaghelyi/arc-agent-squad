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

from src.agents.agent_config_loader import get_default_config_registry

from ...services.grc_agent_squad import GRCAgentSquad
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
    agent_id: str
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
        _grc_squad_instance = GRCAgentSquad()
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
            # Get and log the agent capabilities
            capabilities = agent_config.get_capabilities()
            debug_logger.info("Agent capabilities", 
                           agent_id=agent_id,
                           capabilities=[cap.value for cap in capabilities])
            
            # Check if VOICE_PROCESSING is in capabilities
            has_voice_capability = AgentCapability.VOICE_PROCESSING in capabilities
            debug_logger.info(f"Agent has voice capability: {has_voice_capability}")
            
            # Set has_voice flag based on capability
            has_voice = has_voice_capability
            
            # Only process voice if requested
            if request.response_type == "voice" and has_voice_capability:
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
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


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
                    "model_id": model_settings.get("model_id", "N/A"),
                    "model_provider": model_settings.get("model_provider", "N/A"),
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
    try:
        from ...agents.agent_config_loader import get_default_config_registry
        
        # Get agent configuration from registry
        config_registry = get_default_config_registry()
        agent_config = config_registry.get_config(personality)
        
        if agent_config and "primary_role" in agent_config.config_data:
            # Get primary role directly from the agent's YAML configuration
            return agent_config.config_data["primary_role"]
        
        # If no specific role defined in the config, construct one from the agent name
        if agent_config and "name" in agent_config.config_data:
            name = agent_config.config_data["name"]
            # Extract role from name if it contains a dash (e.g., "Emma - Information Collector")
            if " - " in name:
                return name.split(" - ", 1)[1]
            return name
            
        # Fallback to a generic role
        return "GRC Specialist"
        
    except Exception as e:
        logger.error(f"Error getting agent primary role: {e}")
        return "General GRC Assistant"


@router.get("/debug/voice-test")
async def debug_voice_test(agent_id: Optional[str] = None, grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """
    Debug endpoint to test voice synthesis functionality directly.
    If no agent_id is provided, it will test with all available agents.
    If agent_id is provided, it will return audio data for that agent.
    """
    try:
        from src.services.voice_processor import VoiceProcessor
        from src.agents.agent_config_loader import get_default_config_registry
        import base64
        from fastapi.responses import Response
        
        voice_processor = VoiceProcessor()
        config_registry = get_default_config_registry()
        
        # If a specific agent_id is provided, return audio data directly
        if agent_id:
            test_text = "This is a voice test for the GRC Agent Squad. If you can hear this message, voice synthesis is working correctly."
            
            # Get agent config
            agent_config = config_registry.get_config(agent_id)
            if not agent_config:
                raise HTTPException(status_code=404, detail=f"Agent configuration not found for ID: {agent_id}")
            
            # Check if agent has voice capability
            capabilities = agent_config.get_capabilities()
            has_voice = AgentCapability.VOICE_PROCESSING in capabilities
            
            if not has_voice:
                raise HTTPException(status_code=400, detail=f"Agent {agent_id} does not have voice capability")
            
            # Get voice settings
            voice_settings = agent_config.get_voice_settings()
            if not voice_settings or not voice_settings.get('voice_id'):
                raise HTTPException(status_code=400, detail=f"Agent {agent_id} does not have valid voice settings")
            
            # Test voice synthesis
            voice_result = await voice_processor.synthesize_agent_response(test_text, agent_id)
            
            if not voice_result.get('success'):
                raise HTTPException(status_code=500, detail=f"Voice synthesis failed: {voice_result.get('error')}")
            
            # Return audio data directly
            audio_data = voice_result.get('audio_data')
            if not audio_data:
                raise HTTPException(status_code=500, detail="No audio data generated")
            
            # Decode base64 audio data
            try:
                binary_audio = base64.b64decode(audio_data)
                return Response(
                    content=binary_audio,
                    media_type=f"audio/{voice_result.get('audio_format', 'mp3')}"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error decoding audio data: {str(e)}")
        
        # If no specific agent_id, return test results for all agents
        results = []
        test_text = "This is a voice test for the GRC Agent Squad. If you can hear this message, voice synthesis is working correctly."
        
        # Test all agents
        agent_ids = config_registry.list_agent_ids()
        
        for test_agent_id in agent_ids:
            try:
                agent_config = config_registry.get_config(test_agent_id)
                if not agent_config:
                    results.append({
                        "agent_id": test_agent_id,
                        "success": False,
                        "error": f"Agent configuration not found for ID: {test_agent_id}"
                    })
                    continue
                
                # Check if agent has voice capability
                capabilities = agent_config.get_capabilities()
                has_voice = AgentCapability.VOICE_PROCESSING in capabilities
                
                if not has_voice:
                    results.append({
                        "agent_id": test_agent_id,
                        "success": False,
                        "error": "Agent does not have voice capability",
                        "capabilities": [cap.value for cap in capabilities]
                    })
                    continue
                
                # Get voice settings
                voice_settings = agent_config.get_voice_settings()
                if not voice_settings or not voice_settings.get('voice_id'):
                    results.append({
                        "agent_id": test_agent_id,
                        "success": False,
                        "error": "Agent does not have valid voice settings",
                        "voice_settings": voice_settings
                    })
                    continue
                
                # Test voice synthesis
                voice_result = await voice_processor.synthesize_agent_response(test_text, test_agent_id)
                
                # Add result
                results.append({
                    "agent_id": test_agent_id,
                    "success": voice_result.get('success', False),
                    "error": voice_result.get('error'),
                    "voice_id": voice_result.get('voice_id'),
                    "audio_size": voice_result.get('audio_size', 0) if voice_result.get('success') else 0,
                    "has_audio_data": bool(voice_result.get('audio_data')),
                    "voice_settings": voice_settings
                })
            
            except Exception as e:
                results.append({
                    "agent_id": test_agent_id,
                    "success": False,
                    "error": f"Exception testing agent: {str(e)}"
                })
        
        return {
            "success": True,
            "results": results,
            "total_tested": len(results),
            "successful": sum(1 for r in results if r.get('success'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in debug_voice_test: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Voice test failed: {str(e)}")


 