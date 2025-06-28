"""
Data models for agent management and configuration.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentCapability(str, Enum):
    """Agent capabilities."""
    VOICE_PROCESSING = "voice_processing"
    TEXT_CHAT = "text_chat"
    QUESTION_ANSWERING = "question_answering"
    TASK_ASSISTANCE = "task_assistance"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    CUSTOMER_SUPPORT = "customer_support"
    TECHNICAL_SUPPORT = "technical_support"

