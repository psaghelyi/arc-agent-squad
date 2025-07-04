"""
Main FastAPI application for GRC Agent Squad.
Uses agent-squad framework with Bedrock built-in memory for conversation persistence.
"""

import structlog
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import agents, health, chat
from ..utils.settings import settings


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting GRC Agent Squad API")
    
    try:
        # Initialize configuration
        logger.info("Configuration loaded", 
                   log_level=settings.log_level,
                   debug_mode=settings.debug)
        
        logger.info("GRC Agent Squad API startup complete")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    
    # Shutdown
    logger.info("Shutting down GRC Agent Squad API")


# Create FastAPI app
app = FastAPI(
    title="GRC Agent Squad API",
    description="AI agent squad specialized for Governance, Risk Management, and Compliance (GRC) industry applications",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define API routes first
@app.get("/api/info")
async def get_api_info() -> Dict[str, Any]:
    """Get API information and status."""
    
    return {
        "name": "GRC Agent Squad API",
        "version": "1.1.0",
        "description": "AI agent squad for Governance, Risk Management, and Compliance",
        "memory_system": "bedrock_built_in",
        "agents": {
            "total": 4,
            "types": [
                "empathetic_interviewer",
                "authoritative_compliance", 
                "analytical_risk_expert",
                "strategic_governance"
            ]
        },
        "features": [
            "Intelligent agent routing",
            "GRC-specialized personas and roles",
            "Bedrock built-in memory",
            "Tool integration support"
        ],
        "endpoints": {
            "agents": "/api/agents/",
            "chat": "/api/chat", 
            "health": "/health/",
            "docs": "/docs"
        }
    }


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Add convenience endpoints (without trailing slash) that redirect to canonical versions
@app.get("/health")
async def health_redirect():
    """Redirect to canonical health endpoint with trailing slash."""
    from fastapi import Response
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/health/", status_code=301)

@app.get("/api/agents")
async def agents_redirect():
    """Redirect to canonical agents endpoint with trailing slash."""
    from fastapi import Response
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/agents/", status_code=301)

@app.get("/api/chat")
async def chat_redirect():
    """Redirect to canonical chat endpoint with trailing slash."""
    from fastapi import Response
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/chat/", status_code=301)


# Mount static files (must come last to avoid overriding API routes)
try:
    app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
except Exception as e:
    logger.warning("Failed to mount static files", error=str(e)) 