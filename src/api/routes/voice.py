"""
Voice processing endpoints for the GRC Agent Squad API.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from src.services.grc_agent_squad import GRCAgentSquad
from src.utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize configuration
config = settings

# Global GRC Agent Squad instance
grc_squad: Optional[GRCAgentSquad] = None


async def get_grc_squad() -> GRCAgentSquad:
    """Get or create GRC Agent Squad instance."""
    global grc_squad
    if grc_squad is None:
        grc_squad = GRCAgentSquad(config)
    return grc_squad


class VoiceRequest(BaseModel):
    """Voice processing request model."""
    session_id: str
    text: Optional[str] = None
    audio_format: str = "wav"
    language: str = "en-US"


class VoiceResponse(BaseModel):
    """Voice processing response model."""
    session_id: str
    text: str
    audio_url: Optional[str] = None
    agent_id: str
    processing_time: float


@router.post("/process", response_model=VoiceResponse)
async def process_voice(request: VoiceRequest) -> VoiceResponse:
    """
    Process voice input (text or audio) and return agent response.
    
    This endpoint handles both text and audio input, processes it through
    the appropriate GRC agent, and returns a text response with optional
    audio output.
    """
    try:
        squad = await get_grc_squad()
        
        # For now, process as text input
        if not request.text:
            raise HTTPException(
                status_code=400,
                detail="Text input is required for voice processing"
            )
        
        # Process through GRC Agent Squad
        start_time = asyncio.get_event_loop().time()
        response = await squad.route_request(request.text, request.session_id)
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return VoiceResponse(
            session_id=request.session_id,
            text=response.output,
            agent_id=response.agent_id or "auto_selected",
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-audio")
async def upload_audio(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
    language: str = Form("en-US")
) -> Dict[str, Any]:
    """
    Upload audio file for voice processing.
    
    This endpoint accepts audio files, transcribes them, and processes
    the transcription through the GRC Agent Squad.
    """
    try:
        # Validate audio file
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid audio file format"
            )
        
        # Read audio content
        audio_content = await audio.read()
        
        # TODO: Implement actual audio transcription using Amazon Transcribe
        # For now, return a mock response
        return {
            "session_id": session_id,
            "status": "uploaded",
            "message": "Audio uploaded successfully. Transcription coming soon!",
            "file_size": len(audio_content),
            "content_type": audio.content_type
        }
        
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_voice_endpoint() -> Dict[str, Any]:
    """Test endpoint for voice functionality."""
    try:
        squad = await get_grc_squad()
        
        # Test message
        test_message = "Hello, I need help with compliance requirements."
        response = await squad.route_request(test_message, "test_session")
        
        return {
            "status": "success",
            "test_input": test_message,
            "agent_response": response.output,
            "agent_id": response.agent_id,
            "message": "I'm here to help! What would you like to know about our GRC Agent Squad?"
        }
        
    except Exception as e:
        logger.error(f"Voice test error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 