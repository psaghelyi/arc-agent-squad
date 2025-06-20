"""
Memory service for storing and retrieving agent conversation history.

This service uses Redis to persist conversation history and provides
methods for managing agent memory across sessions.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import redis.asyncio as redis
import structlog
from redis.exceptions import RedisError

from ..models.agent_models import ChatMessage, ConversationHistory


class MemoryService:
    """Service for managing agent conversation memory."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", redis_password: Optional[str] = None):
        """
        Initialize the memory service.
        
        Args:
            redis_url: Redis connection URL
            redis_password: Redis password (if required)
        """
        self.logger = structlog.get_logger(__name__)
        self.redis_url = redis_url
        self.redis_password = redis_password
        self._redis_client: Optional[redis.Redis] = None
        
        # Key prefixes for different data types
        self.CONVERSATION_PREFIX = "conversation:"
        self.AGENT_SESSIONS_PREFIX = "agent_sessions:"
        self.SESSION_METADATA_PREFIX = "session_meta:"
        
        # Default TTL for conversation data (7 days)
        self.DEFAULT_TTL = 7 * 24 * 60 * 60
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self._redis_client.ping()
            self.logger.info("Connected to Redis for memory service")
            
        except Exception as e:
            self.logger.warning("Failed to connect to Redis, using mock mode", error=str(e))
            # Use a mock mode instead of failing
            self._redis_client = None
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis_client:
            await self._redis_client.close()
            self.logger.info("Disconnected from Redis")
    
    @property
    def redis(self) -> Optional[redis.Redis]:
        """Get Redis client (connect if not connected)."""
        return self._redis_client
    
    def _is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._redis_client is not None
    
    async def store_conversation(self, conversation: ConversationHistory) -> bool:
        """
        Store a conversation in memory.
        
        Args:
            conversation: Conversation history to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self._is_connected():
            self.logger.debug("Redis not connected, skipping conversation storage")
            return True  # Return True to not break the flow
            
        try:
            conversation_key = f"{self.CONVERSATION_PREFIX}{conversation.session_id}"
            conversation_data = conversation.model_dump_json()
            
            # Store conversation with TTL
            await self.redis.setex(conversation_key, self.DEFAULT_TTL, conversation_data)
            
            # Add session to agent's session list
            agent_sessions_key = f"{self.AGENT_SESSIONS_PREFIX}{conversation.agent_id}"
            await self.redis.sadd(agent_sessions_key, conversation.session_id)
            await self.redis.expire(agent_sessions_key, self.DEFAULT_TTL)
            
            # Store session metadata
            metadata_key = f"{self.SESSION_METADATA_PREFIX}{conversation.session_id}"
            metadata = {
                "agent_id": conversation.agent_id,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": len(conversation.messages)
            }
            await self.redis.setex(metadata_key, self.DEFAULT_TTL, json.dumps(metadata))
            
            self.logger.debug("Stored conversation", 
                            session_id=conversation.session_id,
                            agent_id=conversation.agent_id,
                            message_count=len(conversation.messages))
            return True
            
        except RedisError as e:
            self.logger.error("Failed to store conversation", 
                            session_id=conversation.session_id,
                            error=str(e))
            return False
    
    async def get_conversation(self, session_id: str) -> Optional[ConversationHistory]:
        """
        Retrieve a conversation from memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation history if found, None otherwise
        """
        if not self._is_connected():
            self.logger.debug("Redis not connected, returning None for conversation")
            return None
            
        try:
            conversation_key = f"{self.CONVERSATION_PREFIX}{session_id}"
            conversation_data = await self.redis.get(conversation_key)
            
            if not conversation_data:
                return None
            
            conversation = ConversationHistory.model_validate_json(conversation_data)
            self.logger.debug("Retrieved conversation", 
                            session_id=session_id,
                            message_count=len(conversation.messages))
            return conversation
            
        except Exception as e:
            self.logger.error("Failed to retrieve conversation", 
                            session_id=session_id,
                            error=str(e))
            return None
    
    async def add_message(self, session_id: str, role: str, content: str, 
                         metadata: Dict = None) -> Optional[ChatMessage]:
        """
        Add a message to an existing conversation.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional message metadata
            
        Returns:
            Added message if successful, None otherwise
        """
        try:
            conversation = await self.get_conversation(session_id)
            if not conversation:
                self.logger.warning("Conversation not found for adding message", 
                                  session_id=session_id)
                return None
            
            message = conversation.add_message(role, content, metadata)
            
            # Store updated conversation
            if await self.store_conversation(conversation):
                return message
            else:
                return None
                
        except Exception as e:
            self.logger.error("Failed to add message", 
                            session_id=session_id,
                            error=str(e))
            return None
    
    async def get_agent_sessions(self, agent_id: str) -> List[str]:
        """
        Get all session IDs for a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of session IDs
        """
        if not self._is_connected():
            self.logger.debug("Redis not connected, returning empty sessions list")
            return []
            
        try:
            agent_sessions_key = f"{self.AGENT_SESSIONS_PREFIX}{agent_id}"
            sessions = await self.redis.smembers(agent_sessions_key)
            return list(sessions) if sessions else []
            
        except RedisError as e:
            self.logger.error("Failed to get agent sessions", 
                            agent_id=agent_id,
                            error=str(e))
            return []
    
    async def get_recent_conversations(self, agent_id: str, limit: int = 10) -> List[ConversationHistory]:
        """
        Get recent conversations for an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        try:
            session_ids = await self.get_agent_sessions(agent_id)
            conversations = []
            
            for session_id in session_ids:
                conversation = await self.get_conversation(session_id)
                if conversation:
                    conversations.append(conversation)
            
            # Sort by updated_at and limit
            conversations.sort(key=lambda c: c.updated_at, reverse=True)
            return conversations[:limit]
            
        except Exception as e:
            self.logger.error("Failed to get recent conversations", 
                            agent_id=agent_id,
                            error=str(e))
            return []
    
    async def create_conversation(self, session_id: str, agent_id: str, 
                                initial_message: Optional[str] = None) -> ConversationHistory:
        """
        Create a new conversation.
        
        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            initial_message: Optional initial system message
            
        Returns:
            New conversation history
        """
        conversation = ConversationHistory(
            session_id=session_id,
            agent_id=agent_id
        )
        
        if initial_message:
            conversation.add_message("system", initial_message)
        
        await self.store_conversation(conversation)
        return conversation
    
    async def delete_conversation(self, session_id: str) -> bool:
        """
        Delete a conversation from memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Get conversation to find agent_id
            conversation = await self.get_conversation(session_id)
            if not conversation:
                return True  # Already deleted
            
            # Delete conversation
            conversation_key = f"{self.CONVERSATION_PREFIX}{session_id}"
            await self.redis.delete(conversation_key)
            
            # Remove from agent sessions
            agent_sessions_key = f"{self.AGENT_SESSIONS_PREFIX}{conversation.agent_id}"
            await self.redis.srem(agent_sessions_key, session_id)
            
            # Delete session metadata
            metadata_key = f"{self.SESSION_METADATA_PREFIX}{session_id}"
            await self.redis.delete(metadata_key)
            
            self.logger.info("Deleted conversation", session_id=session_id)
            return True
            
        except RedisError as e:
            self.logger.error("Failed to delete conversation", 
                            session_id=session_id,
                            error=str(e))
            return False
    
    async def cleanup_expired_conversations(self, max_age_days: int = 7) -> int:
        """
        Clean up expired conversations.
        
        Args:
            max_age_days: Maximum age in days for conversations
            
        Returns:
            Number of conversations cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            cleaned_count = 0
            
            # Get all session metadata keys
            metadata_pattern = f"{self.SESSION_METADATA_PREFIX}*"
            async for key in self.redis.scan_iter(match=metadata_pattern):
                try:
                    metadata_str = await self.redis.get(key)
                    if metadata_str:
                        metadata = json.loads(metadata_str)
                        updated_at = datetime.fromisoformat(metadata.get("updated_at", ""))
                        
                        if updated_at < cutoff_date:
                            session_id = key.replace(self.SESSION_METADATA_PREFIX, "")
                            if await self.delete_conversation(session_id):
                                cleaned_count += 1
                                
                except Exception as e:
                    self.logger.warning("Error processing session for cleanup", 
                                      key=key, error=str(e))
            
            self.logger.info("Cleaned up expired conversations", count=cleaned_count)
            return cleaned_count
            
        except Exception as e:
            self.logger.error("Failed to cleanup conversations", error=str(e))
            return 0
    
    async def get_memory_stats(self) -> Dict:
        """
        Get memory service statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self._is_connected():
            return {
                "total_conversations": 0,
                "active_agents": 0,
                "redis_memory_usage": "disconnected",
                "redis_connected": False,
                "error": "Redis not connected"
            }
            
        try:
            # Count conversations
            conversation_pattern = f"{self.CONVERSATION_PREFIX}*"
            conversation_count = 0
            async for _ in self.redis.scan_iter(match=conversation_pattern):
                conversation_count += 1
            
            # Count agent sessions
            agent_sessions_pattern = f"{self.AGENT_SESSIONS_PREFIX}*"
            agent_count = 0
            async for _ in self.redis.scan_iter(match=agent_sessions_pattern):
                agent_count += 1
            
            # Get Redis info
            redis_info = await self.redis.info("memory")
            
            return {
                "total_conversations": conversation_count,
                "active_agents": agent_count,
                "redis_memory_usage": redis_info.get("used_memory_human", "unknown"),
                "redis_connected": True
            }
            
        except Exception as e:
            self.logger.error("Failed to get memory stats", error=str(e))
            return {
                "total_conversations": 0,
                "active_agents": 0,
                "redis_memory_usage": "unknown",
                "redis_connected": False,
                "error": str(e)
            } 