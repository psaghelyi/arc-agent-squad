"""
GRC Agent Squad API routes for agent management and chat functionality.
Uses agent-squad framework with Bedrock built-in memory for conversation persistence.
"""

import structlog
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


class ChatResponse(BaseModel):
    message: str
    agent_name: str
    session_id: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None


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
        agents = await grc_squad.list_agents()
        agent_types = []
        
        for agent in agents:
            agent_types.append({
                "id": agent["id"],
                "name": agent["name"], 
                "personality": agent["personality"],
                "description": agent["description"],
                "capabilities": agent["capabilities"],
                "use_cases": _get_agent_use_cases(agent["personality"])
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
    """Chat with the GRC Agent Squad. The system will automatically select the best agent."""
    try:
        response = await grc_squad.process_request(
            user_input=request.message,
            session_id=request.session_id or "default",
            context=request.context
        )
        
        if not response.get("success"):
            raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
        
        agent_selection = response.get("agent_selection", {})
        agent_response = response.get("agent_response", {})
        
        return ChatResponse(
            message=agent_response.get("response", "No response generated"),
            agent_name=agent_selection.get("agent_name", "GRC Agent Squad"),
            session_id=response.get("session_id", request.session_id or "default"),
            confidence=agent_selection.get("confidence"),
            reasoning=agent_selection.get("reasoning")
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


 