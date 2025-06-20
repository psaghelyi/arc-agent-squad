"""
Agent management endpoints for the Voice Agent Swarm API.
"""

import asyncio
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.models.agent_models import (
    AgentPersonality,
    AgentCapability,
    AgentConfiguration,
    OrchestratorRequest,
    AgentSelectionCriteria
)
from src.services.agent_orchestrator import AgentOrchestrator
from src.services.memory_service import MemoryService

router = APIRouter()

# Global services (in a real app, these would be dependency injected)
memory_service = None
orchestrator = None
initialization_lock = asyncio.Lock()


async def get_orchestrator() -> AgentOrchestrator:
    """Get the agent orchestrator instance."""
    global orchestrator, memory_service
    
    if not orchestrator:
        async with initialization_lock:
            # Double-check after acquiring lock
            if not orchestrator:
                try:
                    if not memory_service:
                        memory_service = MemoryService()
                        try:
                            await memory_service.connect()
                        except Exception as e:
                            # Continue without Redis connection
                            pass
                    orchestrator = AgentOrchestrator(memory_service)
                    await orchestrator.initialize_default_agents()
                except Exception as e:
                    # Log the error but don't let it crash the app
                    import structlog
                    logger = structlog.get_logger(__name__)
                    logger.error("Failed to initialize orchestrator", error=str(e))
                    raise HTTPException(status_code=500, detail=f"Failed to initialize orchestrator: {str(e)}")
    return orchestrator


class AgentInfo(BaseModel):
    """Agent information model."""
    id: str
    name: str
    description: str
    type: str
    personality: str  # Add personality field for UI compatibility
    status: str
    created_at: str
    capabilities: List[str] = []


class AgentCreateRequest(BaseModel):
    """Agent creation request model."""
    name: str
    description: str
    personality_type: AgentPersonality
    capabilities: List[AgentCapability] = []
    voice_enabled: bool = True
    memory_enabled: bool = True


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str = "default"
    agent_id: Optional[str] = None  # If None, orchestrator will select
    selection_criteria: Optional[AgentSelectionCriteria] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    agent_id: str
    agent_name: str
    session_id: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None


class AgentListResponse(BaseModel):
    """Agent list response model."""
    agents: List[AgentInfo]
    total: int


@router.get("/", response_model=AgentListResponse)
async def list_agents(orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
    """List all available agents."""
    agents_data = await orchestrator.list_agents()
    
    # Transform data to match AgentInfo model
    agents = []
    for agent_data in agents_data:
        agent_info = AgentInfo(
            id=agent_data["id"],
            name=agent_data["name"],
            description=agent_data["description"],
            type=agent_data["personality"],  # Use personality as type
            personality=agent_data["personality"],  # Add personality field for UI
            status=agent_data["status"],
            created_at=agent_data.get("created_at", ""),  # Handle missing created_at
            capabilities=agent_data["capabilities"]
        )
        agents.append(agent_info)
    
    return AgentListResponse(
        agents=agents,
        total=len(agents)
    )


@router.get("/stats")
async def get_orchestrator_stats(orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
    """Get orchestrator statistics."""
    stats = await orchestrator.get_orchestrator_stats()
    return stats


@router.get("/tools")
async def get_available_tools():
    """Get list of available tools for agents."""
    from src.tools.tool_registry import get_default_registry
    
    registry = get_default_registry()
    
    # Initialize some default tools if none exist
    if len(registry.list_tools()) == 0:
        from src.tools.external_api_tool import ExternalApiTool, UserManagementTool
        from src.tools.mcp_client_tool import MCPServerManager
        
        # External API tool for company APIs
        api_tool = ExternalApiTool(
            base_url="https://api.yourcompany.com",
            default_headers={"Authorization": "Bearer YOUR_API_TOKEN"}
        )
        registry.register_tool(api_tool)
        
        # User management tool
        user_tool = UserManagementTool(
            base_url="https://api.yourcompany.com", 
            default_headers={"Authorization": "Bearer YOUR_API_TOKEN"}
        )
        registry.register_tool(user_tool)
        
        # MCP server manager for connecting to MCP servers
        mcp_manager = MCPServerManager()
        registry.register_tool(mcp_manager)
    
    return {
        "tools": registry.get_tool_schemas(),
        "total": len(registry.list_tools()),
        "registry_stats": registry.get_registry_stats()
    }


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
            "description": config.system_prompt[:100] + "..." if len(config.system_prompt) > 100 else config.system_prompt,
            "traits": {
                "politeness_level": config.politeness_level,
                "enthusiasm_level": config.enthusiasm_level,
                "uses_emojis": config.use_emojis,
                "asks_follow_up_questions": config.asks_follow_up_questions,
                "provides_examples": config.provides_examples,
                "shows_empathy": config.shows_empathy,
                "is_proactive": config.is_proactive
            }
        }
    
    return {
        "presets": presets,
        "total": len(presets)
    }


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str, orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
    """Get information about a specific agent."""
    agent_data = await orchestrator.get_agent_info(agent_id)
    if not agent_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Transform data to match AgentInfo model
    created_at = agent_data.get("created_at", "")
    if hasattr(created_at, 'isoformat'):
        created_at = created_at.isoformat()
    
    personality_value = agent_data["personality"]["type"] if isinstance(agent_data.get("personality"), dict) else agent_data.get("personality", "")
    agent_info = AgentInfo(
        id=agent_data["id"],
        name=agent_data["name"],
        description=agent_data["description"],
        type=personality_value,
        personality=personality_value,  # Add personality field for UI
        status=agent_data["status"],
        created_at=str(created_at),
        capabilities=agent_data["capabilities"]
    )
    return agent_info


@router.post("/", response_model=AgentInfo)
async def create_agent(
    agent_request: AgentCreateRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Create a new agent."""
    try:
        agent_id = await orchestrator.create_agent(
            name=agent_request.name,
            description=agent_request.description,
            personality_type=agent_request.personality_type,
            capabilities=agent_request.capabilities,
            voice_enabled=agent_request.voice_enabled,
            memory_enabled=agent_request.memory_enabled
        )
        
        # Get the created agent info
        agent_info = await orchestrator.get_agent_info(agent_id)
        return {
            "message": "Agent created successfully",
            "agent": agent_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
    """Delete an agent."""
    success = await orchestrator.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": f"Agent {agent_id} deleted successfully"}


@router.post("/{agent_id}/activate")
async def activate_agent(agent_id: str, orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
    """Activate an agent."""
    # Implementation would set agent status to active
    return {"message": f"Agent {agent_id} activated"}


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(agent_id: str, orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
    """Deactivate an agent."""
    # Implementation would set agent status to inactive
    return {"message": f"Agent {agent_id} deactivated"}


@router.post("/chat")
async def chat_with_agents(
    request: ChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Chat with agents through the orchestrator."""
    try:
        if request.agent_id:
            # Direct chat with specific agent
            agent_info = await orchestrator.get_agent_info(request.agent_id)
            if not agent_info:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # Process request directly with the agent
            # This would need to be implemented to get the actual agent instance
            return ChatResponse(
                message="Direct agent chat not yet implemented",
                agent_id=request.agent_id,
                agent_name=agent_info["name"],
                session_id=request.session_id
            )
        else:
            # Use orchestrator to select best agent
            orchestrator_request = OrchestratorRequest(
                user_input=request.message,
                session_id=request.session_id,
                selection_criteria=request.selection_criteria
            )
            
            result = await orchestrator.process_request(orchestrator_request)
            
            if result["success"]:
                agent_selection = result["agent_selection"]
                agent_response = result["agent_response"]
                
                return ChatResponse(
                    message=agent_response.get("response", "No response generated"),
                    agent_id=agent_selection["agent_id"],
                    agent_name=agent_selection["agent_name"],
                    session_id=request.session_id,
                    confidence=agent_selection["confidence"],
                    reasoning=agent_selection["reasoning"]
                )
            else:
                raise HTTPException(status_code=500, detail=result["error"])
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/conversations")
async def get_agent_conversations(
    agent_id: str,
    limit: int = 10,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Get recent conversations for an agent."""
    # This would need to be implemented to access the agent's memory service
    return {
        "agent_id": agent_id,
        "conversations": [],
        "message": "Conversation history retrieval not yet implemented"
    }


@router.get("/{agent_id}/personality")
async def get_agent_personality(
    agent_id: str,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Get agent personality configuration."""
    agent_info = await orchestrator.get_agent_info(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "personality": agent_info["personality"]
    }


 