"""
FastAPI application for the Voice Agent Swarm.

This module creates and configures the FastAPI application with all routes,
middleware, and WebSocket endpoints for voice communication.
"""

from contextlib import asynccontextmanager
from typing import List

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

from .routes import agents, health, voice
from src.services.websocket_manager import WebSocketManager
from src.utils.config import settings


# Global WebSocket manager
websocket_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger = structlog.get_logger(__name__)
    logger.info("Starting Voice Agent Swarm API")
    
    # Startup logic here
    yield
    
    # Shutdown logic here
    logger.info("Shutting down Voice Agent Swarm API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Voice Agent Swarm API",
        description="Voice-enabled AI agent swarm using AWS services",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
    
    # Mount static files
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # WebSocket endpoint for real-time voice communication
    @app.websocket("/ws/voice/{session_id}")
    async def websocket_voice_endpoint(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time voice communication."""
        await websocket_manager.connect(websocket, session_id)
        try:
            while True:
                # Receive data (could be text or binary)
                data = await websocket.receive()
                
                if "bytes" in data:
                    # Handle audio data
                    audio_data = data["bytes"]
                    await websocket_manager.handle_audio_data(websocket, audio_data)
                elif "text" in data:
                    # Handle text messages
                    text_data = data["text"]
                    # Echo back for now - replace with actual processing
                    await websocket_manager.send_personal_message(
                        f"Received: {text_data}", websocket
                    )
                    
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)
    
    # WebSocket connection status endpoint
    @app.get("/api/v1/websocket/stats")
    async def get_websocket_stats():
        """Get WebSocket connection statistics."""
        return websocket_manager.get_connection_stats()
    
    # Root endpoint - serve the web UI
    @app.get("/")
    async def root():
        """Serve the web UI."""
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        else:
            return {
                "message": "Voice Agent Swarm API",
                "version": "0.1.0",
                "docs": "/docs",
                "health": "/health"
            }
    
    return app


# Create the app instance
app = create_app() 