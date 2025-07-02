"""
Routing strategy interface for pluggable agent routing logic.

Provides an abstraction layer for different routing approaches while maintaining
compatibility with the existing agent-squad framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from agent_squad.classifiers import Classifier, ClassifierResult
from agent_squad.agents import Agent
from agent_squad.types import ConversationMessage


class RoutingStrategy(ABC):
    """Abstract base class for agent routing strategies"""
    
    @abstractmethod
    async def route_request(
        self,
        user_input: str,
        user_id: str, 
        session_id: str,
        classifier: Classifier,
        agents: Dict[str, Agent],
        storage: Any
    ) -> ClassifierResult:
        """
        Route a user request to the appropriate agent.
        
        Args:
            user_input: User's input text
            user_id: User identifier
            session_id: Session identifier
            classifier: Classifier instance to use
            agents: Available agents
            storage: Chat storage instance
            
        Returns:
            ClassifierResult with selected agent and confidence
        """
        pass


class DefaultRoutingStrategy(RoutingStrategy):
    """Default routing strategy using standard classifier"""
    
    async def route_request(
        self,
        user_input: str,
        user_id: str,
        session_id: str, 
        classifier: Classifier,
        agents: Dict[str, Agent],
        storage: Any
    ) -> ClassifierResult:
        """Use standard classification without hierarchical logic"""
        chat_history = await storage.fetch_all_chats(user_id, session_id) or []
        return await classifier.classify(user_input, chat_history)


class HierarchicalRoutingStrategy(RoutingStrategy):
    """Hierarchical routing strategy with confidence-based tiers"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.squad_config = None
        
    async def route_request( 
        self,
        user_input: str,
        user_id: str,
        session_id: str,
        classifier: Classifier,
        agents: Dict[str, Agent],
        storage: Any
    ) -> ClassifierResult:
        """Use hierarchical classifier for tiered routing"""
        
        # Import here to avoid circular dependencies
        from src.classifiers.hierarchical_classifier import HierarchicalClassifier
        
        # If classifier is already hierarchical, use it directly
        if isinstance(classifier, HierarchicalClassifier):
            chat_history = await storage.fetch_all_chats(user_id, session_id) or []
            return await classifier.classify(user_input, chat_history)
        
        # Otherwise, fall back to default routing
        chat_history = await storage.fetch_all_chats(user_id, session_id) or []
        return await classifier.classify(user_input, chat_history)