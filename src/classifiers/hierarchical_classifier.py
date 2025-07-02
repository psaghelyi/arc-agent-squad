"""
Hierarchical Classifier extending the agent-squad BedrockClassifier.

This classifier implements tiered agent selection:
1. First tries specialists with high confidence threshold
2. Falls back to supervisors/directors with lower threshold
3. Uses default agent as final fallback

Designed to work with existing agent-squad framework with minimal changes.
"""

import structlog
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from agent_squad.classifiers import BedrockClassifier, BedrockClassifierOptions, ClassifierResult
from agent_squad.agents import Agent
from agent_squad.types import ConversationMessage


@dataclass
class SquadTier:
    """Configuration for a single tier in the squad hierarchy"""
    name: str
    type: str  # "specialist" or "supervisor"
    confidence_threshold: float
    description: str
    agents: List[str]


@dataclass 
class SquadConfig:
    """Complete squad configuration with hierarchical tiers"""
    name: str
    description: str
    routing_strategy: str
    tiers: List[SquadTier]
    fallback_agent: str


class HierarchicalClassifier(BedrockClassifier):
    """
    Extends BedrockClassifier with hierarchical, confidence-based agent selection.
    
    Routes requests through tiers:
    1. Specialists (high confidence threshold) 
    2. Supervisors/Directors (lower confidence threshold)
    3. Fallback agent (lowest/no threshold)
    """
    
    def __init__(self, options: BedrockClassifierOptions, squad_config: SquadConfig):
        super().__init__(options)
        self.squad_config = squad_config
        self.logger = structlog.get_logger(__name__)
        self.all_agents: Dict[str, Agent] = {}
        
        # Log configuration
        self.logger.info(
            "Initialized hierarchical classifier",
            squad_name=squad_config.name,
            routing_strategy=squad_config.routing_strategy,
            tier_count=len(squad_config.tiers)
        )
    
    def set_agents(self, agents: Dict[str, Agent]) -> None:
        """Override to store all agents while still calling parent implementation"""
        self.all_agents = agents
        super().set_agents(agents)
    
    async def classify(self, input_text: str, chat_history: List[ConversationMessage]) -> ClassifierResult:
        """
        Implement hierarchical classification through confidence-based tiers.
        
        Args:
            input_text: User input to classify
            chat_history: Conversation history for context
            
        Returns:
            ClassifierResult with selected agent and confidence
        """
        self.logger.info("Starting hierarchical classification", user_input=input_text[:100])
        
        # Try each tier in order
        for tier in self.squad_config.tiers:
            self.logger.info(
                f"Trying {tier.type} tier",
                tier_name=tier.name,
                confidence_threshold=tier.confidence_threshold,
                agent_count=len(tier.agents)
            )
            
            # Get agents for this tier
            tier_agents = self._get_agents_for_tier(tier)
            if not tier_agents:
                self.logger.warning(f"No agents available for tier: {tier.name}")
                continue
            
            # Temporarily set agents to only this tier's agents
            super().set_agents(tier_agents)
            
            # Classify using parent implementation
            result = await super().classify(input_text, chat_history)
            
            # Check if confidence meets tier threshold
            if result.selected_agent and result.confidence >= tier.confidence_threshold:
                self.logger.info(
                    f"Agent selected from {tier.type} tier",
                    agent_id=result.selected_agent.id,
                    agent_name=result.selected_agent.name,
                    confidence=result.confidence,
                    tier_name=tier.name
                )
                
                # Restore all agents before returning
                super().set_agents(self.all_agents)
                return result
            else:
                self.logger.info(
                    f"Confidence too low for {tier.type} tier",
                    confidence=result.confidence,
                    threshold=tier.confidence_threshold,
                    tier_name=tier.name
                )
        
        # If no tier worked, use fallback
        self.logger.info("Using fallback agent", fallback_agent=self.squad_config.fallback_agent)
        
        # Restore all agents
        super().set_agents(self.all_agents)
        
        fallback_agent = self.all_agents.get(self.squad_config.fallback_agent)
        if fallback_agent:
            return ClassifierResult(
                selected_agent=fallback_agent,
                confidence=0.0  # Fallback confidence
            )
        
        # Final fallback - no agent selected
        self.logger.warning("No fallback agent available")
        return ClassifierResult(selected_agent=None, confidence=0.0)
    
    def _get_agents_for_tier(self, tier: SquadTier) -> Dict[str, Agent]:
        """Get agents that belong to a specific tier"""
        tier_agents = {}
        
        for agent_id in tier.agents:
            if agent_id in self.all_agents:
                tier_agents[agent_id] = self.all_agents[agent_id]
            else:
                self.logger.warning(f"Agent {agent_id} not found for tier {tier.name}")
        
        return tier_agents
    
    @classmethod
    def load_squad_config(cls, config_path: str) -> SquadConfig:
        """Load squad configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                data = yaml.safe_load(file)
            
            squad_data = data['squad_config']
            
            # Parse tiers
            tiers = []
            for tier_data in squad_data['hierarchy']['tiers']:
                tier = SquadTier(
                    name=tier_data['name'],
                    type=tier_data['type'], 
                    confidence_threshold=tier_data['confidence_threshold'],
                    description=tier_data['description'],
                    agents=tier_data['agents']
                )
                tiers.append(tier)
            
            # Create squad config
            config = SquadConfig(
                name=squad_data['name'],
                description=squad_data['description'],
                routing_strategy=squad_data['routing_strategy'],
                tiers=tiers,
                fallback_agent=squad_data['fallback']['agent']
            )
            
            return config
            
        except Exception as e:
            raise ValueError(f"Failed to load squad configuration from {config_path}: {e}")