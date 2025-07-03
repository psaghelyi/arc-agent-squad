"""
GRC Agent Squad API routes for agent management and chat functionality.
Uses agent-squad framework with Bedrock built-in memory for conversation persistence.
"""

import structlog
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends

from ...services.grc_agent_squad import GRCAgentSquad



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


@router.get("/config/stats")
async def get_squad_stats(grc_squad: GRCAgentSquad = Depends(get_grc_squad)):
    """Get statistics about the GRC Agent Squad."""
    try:
        stats = await grc_squad.get_squad_stats()
        
        # Ensure available_tools is a list for consistent API response
        if "available_tools" in stats and stats["available_tools"] is not None:
            # Make sure it's a list
            if not isinstance(stats["available_tools"], list):
                stats["available_tools"] = list(stats["available_tools"])
        else:
            stats["available_tools"] = []
            
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        # Instead of raising an exception, return a fallback response with empty stats
        return {
            "success": False,
            "stats": {
                "total_agents": 0,
                "active_agents": 0,
                "memory_type": "unknown",
                "agent_types": [],
                "available_tools": []
            },
            "error": f"Failed to get stats: {str(e)}"
        }


@router.get("/config/details")
async def get_detailed_agent_config():
    """Get detailed configuration information for all agents including model IDs, prompts, and settings."""
    try:
        from ...agents.agent_config_loader import get_default_config_registry
        
        # Try to get the GRC squad, but handle configuration errors gracefully
        grc_squad = None
        squad_error = None
        agents = []
        
        try:
            grc_squad = get_grc_squad()
            agents = await grc_squad.list_agents()
        except Exception as e:
            squad_error = str(e)
            logger.warning(f"GRC squad initialization failed: {squad_error}")
        
        detailed_configs = []
        
        # Get file-based configuration registry (this should work even if squad failed)
        config_registry = get_default_config_registry()
        
        # If squad failed, get agent configs directly from registry
        if not agents and config_registry:
            agent_ids = config_registry.list_agent_ids()
            agents = []
            for agent_id in agent_ids:
                config_class = config_registry.get_config(agent_id)
                if config_class:
                    agents.append({
                        "agent_id": agent_id,
                        "name": config_class.config_data.get("name", agent_id),
                        "description": config_class.config_data.get("description", "")
                    })
                else:
                    agents.append({
                        "agent_id": agent_id,
                        "name": f"Agent {agent_id}",
                        "description": "Configuration file not found"
                    })
        
        # Get detailed configuration for each agent
        for agent in agents:
            agent_id = agent.get("agent_id", "")
            config_class = config_registry.get_config(agent_id)
            
            if config_class:
                try:
                    # Get system prompt
                    system_prompt = config_class.get_system_prompt()
                    
                    # Get voice settings
                    voice_settings = config_class.get_voice_settings()
                    
                    # Get available tools
                    tools = config_class.get_tools()
                    
                    # Get model settings
                    model_settings = config_class.get_model_settings()
                    
                    # Check if this agent would have configuration errors
                    agent_error = None
                    agent_kind = model_settings.get("agent_kind", "BedrockLLMAgent")
                    
                    if agent_kind == "LexBotAgent":
                        # Check for required Lex environment variables
                        import os
                        missing_vars = []
                        if not os.environ.get('LEX_BOT_ID'):
                            missing_vars.append('LEX_BOT_ID')
                        if not os.environ.get('LEX_BOT_ALIAS_ID'):
                            missing_vars.append('LEX_BOT_ALIAS_ID')
                        
                        if missing_vars:
                            agent_error = f"Missing required environment variables: {', '.join(missing_vars)}"
                    
                    detailed_config = {
                        "id": agent.get("agent_id", ""),
                        "name": agent.get("name", config_class.config_data.get("name", agent_id)),
                        "description": agent.get("description", config_class.config_data.get("description", "")),
                        "status": "error" if agent_error else agent.get("status", "active"),
                        "created_at": agent.get("created_at", ""),
                        
                        # Error information
                        "error": agent_error,
                        "has_error": bool(agent_error),
                        
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
                        "voice_enabled": bool(voice_settings and voice_settings.get('voice_id')),
                        
                        # System prompt and role
                        "system_prompt": system_prompt,
                        "system_prompt_length": len(system_prompt),
                        
                        # Tools and capabilities
                        "tools": tools,
                        "tool_count": len(tools),
                        
                        # Role-specific information from config file
                        "use_cases": config_class.get_use_cases(),
                        
                        # Technical details
                        "conversation_memory": True,
                        "session_persistence": True,
                        "framework": model_settings.get("framework", "agent-squad"),
                        "agent_kind": agent_kind
                    }
                    
                except Exception as config_error:
                    # Handle individual agent configuration errors
                    detailed_config = {
                        "id": agent.get("agent_id", ""),
                        "name": agent.get("name", agent_id),
                        "description": agent.get("description", "Configuration error"),
                        "status": "error",
                        "created_at": "",
                        
                        # Error information
                        "error": str(config_error),
                        "has_error": True,
                        
                        # Safe defaults for required fields
                        "model_id": "N/A",
                        "model_provider": "N/A",
                        "inference_config": {
                            "maxTokens": 0,
                            "temperature": 0,
                            "topP": 0
                        },
                        "memory_enabled": False,
                        "streaming": False,
                        
                        # Voice configuration
                        "voice_settings": {},
                        "voice_enabled": False,
                        
                        # System prompt and role
                        "system_prompt": "",
                        "system_prompt_length": 0,
                        
                        # Tools and capabilities
                        "tools": [],
                        "tool_count": 0,
                        
                        # Role-specific information
                        "use_cases": [],
                        
                        # Technical details
                        "conversation_memory": False,
                        "session_persistence": False,
                        "framework": "unknown",
                        "agent_kind": "Unknown"
                    }
                
                detailed_configs.append(detailed_config)
        
        return {
            "success": True,
            "detailed_configs": detailed_configs,
            "total": len(detailed_configs),
            "timestamp": datetime.now().isoformat(),
            "squad_error": squad_error,
            "has_squad_error": bool(squad_error),
            "errors_count": sum(1 for config in detailed_configs if config.get("has_error", False))
        }
        
    except Exception as e:
        logger.error("Failed to get detailed agent config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get detailed agent config: {str(e)}")



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
            
            # Get voice settings
            voice_settings = agent_config.get_voice_settings()
            
            # Check if agent has voice capability based on voice settings having a voice_id
            has_voice = bool(voice_settings and voice_settings.get('voice_id'))
            
            if not has_voice:
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
                
                # Get voice settings
                voice_settings = agent_config.get_voice_settings()
                
                # Check if agent has voice capability based on voice settings having a voice_id
                has_voice = bool(voice_settings and voice_settings.get('voice_id'))
                
                if not has_voice:
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


 