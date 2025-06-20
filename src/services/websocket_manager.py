"""
WebSocket manager for real-time voice communication and agent interactions.
"""

import asyncio
import json
from typing import Dict, List, Set

import structlog
from fastapi import WebSocket

# from services.logger import LoggerMixin


class WebSocketManager:
    """Manages WebSocket connections for real-time voice communication."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.logger = structlog.get_logger(__name__)
        self.active_connections: Set[WebSocket] = set()
        self.session_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str = None) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            session_id: Optional session identifier
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if session_id:
            self.session_connections[session_id] = websocket
            
        self.connection_metadata[websocket] = {
            "session_id": session_id,
            "connected_at": asyncio.get_event_loop().time(),
            "messages_sent": 0,
            "messages_received": 0
        }
        
        self.logger.info("WebSocket connected", 
                        session_id=session_id,
                        total_connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        # Remove from session mapping
        metadata = self.connection_metadata.get(websocket, {})
        session_id = metadata.get("session_id")
        if session_id and session_id in self.session_connections:
            del self.session_connections[session_id]
            
        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
            
        self.logger.info("WebSocket disconnected",
                        session_id=session_id,
                        total_connections=len(self.active_connections))
    
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            message: The message to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_text(message)
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["messages_sent"] += 1
        except Exception as e:
            self.logger.error("Failed to send personal message", error=str(e))
            self.disconnect(websocket)
    
    async def send_json_message(self, data: dict, websocket: WebSocket) -> None:
        """
        Send a JSON message to a specific WebSocket connection.
        
        Args:
            data: The data to send as JSON
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_json(data)
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["messages_sent"] += 1
        except Exception as e:
            self.logger.error("Failed to send JSON message", error=str(e))
            self.disconnect(websocket)
    
    async def send_binary_message(self, data: bytes, websocket: WebSocket) -> None:
        """
        Send binary data to a specific WebSocket connection.
        
        Args:
            data: The binary data to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_bytes(data)
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["messages_sent"] += 1
        except Exception as e:
            self.logger.error("Failed to send binary message", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast_message(self, message: str) -> None:
        """
        Broadcast a message to all connected WebSocket connections.
        
        Args:
            message: The message to broadcast
        """
        if not self.active_connections:
            return
            
        # Send to all connections simultaneously
        await asyncio.gather(
            *[self.send_personal_message(message, connection) 
              for connection in self.active_connections.copy()],
            return_exceptions=True
        )
    
    async def broadcast_json(self, data: dict) -> None:
        """
        Broadcast JSON data to all connected WebSocket connections.
        
        Args:
            data: The data to broadcast as JSON
        """
        if not self.active_connections:
            return
            
        # Send to all connections simultaneously
        await asyncio.gather(
            *[self.send_json_message(data, connection) 
              for connection in self.active_connections.copy()],
            return_exceptions=True
        )
    
    async def send_to_session(self, message: str, session_id: str) -> bool:
        """
        Send a message to a specific session.
        
        Args:
            message: The message to send
            session_id: The session identifier
            
        Returns:
            True if message was sent, False if session not found
        """
        if session_id in self.session_connections:
            websocket = self.session_connections[session_id]
            await self.send_personal_message(message, websocket)
            return True
        return False
    
    async def handle_audio_data(self, websocket: WebSocket, audio_data: bytes) -> None:
        """
        Handle incoming audio data from a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            audio_data: The raw audio data
        """
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["messages_received"] += 1
            
        # Process audio data here
        # This is where you would integrate with:
        # - Amazon Transcribe for speech-to-text
        # - Agent Squad for processing the transcribed text
        # - Amazon Polly for text-to-speech response
        
        self.logger.debug("Processing audio data",
                         audio_size=len(audio_data),
                         session_id=self.connection_metadata.get(websocket, {}).get("session_id"))
        
        # Mock response - replace with actual processing
        response = {
            "type": "audio_processed",
            "transcript": "Mock transcript of audio data",
            "response": "Mock agent response",
            "audio_url": "/mock/audio/response.mp3"
        }
        
        await self.send_json_message(response, websocket)
    
    def get_connection_stats(self) -> Dict:
        """
        Get statistics about current connections.
        
        Returns:
            Dictionary with connection statistics
        """
        return {
            "total_connections": len(self.active_connections),
            "session_connections": len(self.session_connections),
            "active_sessions": list(self.session_connections.keys())
        } 