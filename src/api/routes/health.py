"""
Health check endpoints for the GRC Agent Squad API.
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint returning basic service information."""
    return {
        "service": "GRC Agent Squad",
        "status": "running",
        "message": "GRC Agent Squad is running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {
        "status": "ready",
        "message": "GRC Agent Squad is ready to serve requests",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {
        "status": "alive",
        "message": "GRC Agent Squad is alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    } 