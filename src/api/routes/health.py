"""
Health check endpoints for the Voice Agent Swarm API.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    version: str = "0.1.0"


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Voice Agent Swarm is running"
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint for Kubernetes/container orchestration."""
    # Add more sophisticated checks here if needed
    # e.g., database connectivity, external service availability
    return HealthResponse(
        status="ready",
        message="Voice Agent Swarm is ready to serve requests"
    )


@router.get("/live", response_model=HealthResponse)
async def liveness_check():
    """Liveness check endpoint for Kubernetes/container orchestration."""
    return HealthResponse(
        status="alive",
        message="Voice Agent Swarm is alive"
    ) 