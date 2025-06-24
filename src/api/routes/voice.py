"""
Voice processing endpoints for the GRC Agent Squad API.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from src.services.grc_agent_squad import GRCAgentSquad
from src.services.voice_processor import VoiceProcessor
from src.utils.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize configuration
config = settings

# Global instances
grc_squad: Optional[GRCAgentSquad] = None
voice_processor: Optional[VoiceProcessor] = None


async def get_grc_squad() -> GRCAgentSquad:
    """Get or create GRC Agent Squad instance."""
    global grc_squad
    if grc_squad is None:
        grc_squad = GRCAgentSquad()
    return grc_squad


async def get_voice_processor() -> VoiceProcessor:
    """Get or create Voice Processor instance."""
    global voice_processor
    if voice_processor is None:
        voice_processor = VoiceProcessor()
    return voice_processor


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
    audio_data: Optional[str] = None  # Base64 encoded audio
    audio_format: Optional[str] = None
    voice_id: Optional[str] = None
    agent_id: str
    agent_personality: Optional[str] = None
    processing_time: float


@router.post("/process", response_model=VoiceResponse)
async def process_voice(request: VoiceRequest) -> VoiceResponse:
    """
    Process voice input (text or audio) and return agent response with audio output.
    
    This endpoint handles both text and audio input, processes it through
    the appropriate GRC agent, and returns both text and audio responses.
    """
    try:
        squad = await get_grc_squad()
        voice_proc = await get_voice_processor()
        
        # For now, process as text input
        if not request.text:
            raise HTTPException(
                status_code=400,
                detail="Text input is required for voice processing"
            )
        
        # Process through GRC Agent Squad
        start_time = asyncio.get_event_loop().time()
        agent_response = await squad.process_request(request.text, request.session_id)
        
        # Get agent personality for voice synthesis
        agent_selection = agent_response.get("agent_selection", {})
        agent_response_data = agent_response.get("agent_response", {})
        response_text = agent_response_data.get("response", "No response generated")
        agent_personality = "default"  # We'll need to map this from agent selection
        
        # Synthesize speech for the agent response
        tts_result = await voice_proc.synthesize_agent_response(
            text=response_text,
            agent_personality=agent_personality,
            session_id=request.session_id
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # Build response
        response_data = {
            "session_id": request.session_id,
            "text": response_text,
            "agent_id": agent_selection.get("agent_id", "auto_selected"),
            "agent_personality": agent_personality,
            "processing_time": processing_time
        }
        
        # Add audio data if TTS was successful
        if tts_result.get('success'):
            response_data.update({
                "audio_data": tts_result['audio_data'],
                "audio_format": tts_result['audio_format'],
                "voice_id": tts_result['voice_id']
            })
        else:
            logger.warning(f"TTS failed: {tts_result.get('error')}")
        
        return VoiceResponse(**response_data)
        
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


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    voice_id: str = Form("Joanna"),
    agent_personality: str = Form("default")
) -> Dict[str, Any]:
    """
    Synthesize speech from text using Amazon Polly Neural TTS.
    
    This endpoint directly converts text to speech without agent processing.
    """
    try:
        voice_proc = await get_voice_processor()
        
        # Synthesize speech
        result = await voice_proc.synthesize_agent_response(
            text=text,
            agent_personality=agent_personality
        )
        
        if result['success']:
            return {
                "success": True,
                "audio_data": result['audio_data'],
                "audio_format": result['audio_format'],
                "voice_id": result['voice_id'],
                "agent_personality": result['agent_personality'],
                "text_length": result.get('text_length', len(text)),
                "audio_size": result.get('audio_size', 0)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Speech synthesis failed: {result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"Speech synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def get_available_voices(language: Optional[str] = None) -> Dict[str, Any]:
    """Get available Polly voices."""
    try:
        voice_proc = await get_voice_processor()
        
        if language:
            result = voice_proc.get_available_voices(language)
        else:
            result = voice_proc.get_available_voices()
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/neural")
async def get_neural_voices() -> Dict[str, Any]:
    """Get voices that support Neural TTS engine."""
    try:
        voice_proc = await get_voice_processor()
        result = voice_proc.get_neural_voices()
        return result
        
    except Exception as e:
        logger.error(f"Error getting neural voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_voice_endpoint() -> Dict[str, Any]:
    """Test endpoint for voice functionality with TTS."""
    try:
        squad = await get_grc_squad()
        voice_proc = await get_voice_processor()
        
        # Test message
        test_message = "Hello, I need help with compliance requirements."
        agent_response = await squad.process_request(test_message, "test_session")
        
        # Test TTS
        tts_test = await voice_proc.test_voice_synthesis()
        
        return {
            "status": "success",
            "test_input": test_message,
            "agent_response": agent_response.get("agent_response", {}).get("response", "No response"),
            "agent_id": agent_response.get("agent_selection", {}).get("agent_id", "unknown"),
            "tts_test": tts_test,
            "message": "🎙️ I'm here to help! Your GRC Agent Squad is ready to speak!"
        }
        
    except Exception as e:
        logger.error(f"Voice test error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 