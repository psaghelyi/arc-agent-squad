"""
GRC Agent Configuration Classes

This module contains configuration classes for each specialized GRC agent,
using modular prompt components for maintainable and consistent system prompts.
"""

from typing import Dict, List, Any
from datetime import datetime, UTC
from ..models.agent_models import AgentCapability
from .prompt_components import PromptComponents


class EmpathicInterviewerConfig:
    """Configuration for Emma - Information Collector (Empathetic Interviewer)."""
    
    ID = "empathetic_interviewer"
    NAME = "Emma - Information Collector"
    DESCRIPTION = "Empathetic interviewer specialized in conducting thorough audit interviews, stakeholder consultations, and gathering detailed compliance information"
    
    @staticmethod
    def get_system_prompt() -> str:
        capabilities = EmpathicInterviewerConfig.get_capabilities()
        use_cases = [
            "Compliance interviews", "Risk assessment sessions", "Stakeholder consultations",
            "Documentation reviews", "Control testing interviews"
        ]
        
        return PromptComponents.build_system_prompt(
            agent_id=EmpathicInterviewerConfig.ID,
            name=EmpathicInterviewerConfig.NAME,
            role_description=EmpathicInterviewerConfig.DESCRIPTION,
            capabilities=capabilities,
            use_cases=use_cases
        )
    
    @staticmethod
    def get_capabilities() -> List[AgentCapability]:
        return [
            AgentCapability.QUESTION_ANSWERING,
            AgentCapability.VOICE_PROCESSING,
            AgentCapability.CUSTOMER_SUPPORT
        ]
    
    @staticmethod
    def get_specialized_tools() -> List[str]:
        return PromptComponents.get_specialized_tools_for_role(EmpathicInterviewerConfig.ID)
    
    @staticmethod
    def get_voice_settings() -> Dict[str, str]:
        return PromptComponents.get_voice_settings_for_personality(EmpathicInterviewerConfig.ID)


class ComplianceAuthorityConfig:
    """Configuration for Dr. Morgan - Compliance Authority."""
    
    ID = "authoritative_compliance"
    NAME = "Dr. Morgan - Compliance Authority"
    DESCRIPTION = "Official compliance agent providing definitive regulatory guidance, compliance interpretations, and formal documentation"
    
    @staticmethod
    def get_system_prompt() -> str:
        capabilities = ComplianceAuthorityConfig.get_capabilities()
        use_cases = [
            "Regulatory interpretation", "Compliance status assessments", "Policy guidance",
            "Formal compliance reporting", "Regulatory change analysis"
        ]
        
        return PromptComponents.build_system_prompt(
            agent_id=ComplianceAuthorityConfig.ID,
            name=ComplianceAuthorityConfig.NAME,
            role_description=ComplianceAuthorityConfig.DESCRIPTION,
            capabilities=capabilities,
            use_cases=use_cases
        )
    
    @staticmethod
    def get_capabilities() -> List[AgentCapability]:
        return [
            AgentCapability.QUESTION_ANSWERING,
            AgentCapability.VOICE_PROCESSING,
            AgentCapability.TASK_ASSISTANCE,
            AgentCapability.DATA_ANALYSIS
        ]
    
    @staticmethod
    def get_specialized_tools() -> List[str]:
        return PromptComponents.get_specialized_tools_for_role(ComplianceAuthorityConfig.ID)
    
    @staticmethod
    def get_voice_settings() -> Dict[str, str]:
        return PromptComponents.get_voice_settings_for_personality(ComplianceAuthorityConfig.ID)


class RiskAnalysisExpertConfig:
    """Configuration for Alex - Risk Analysis Expert."""
    
    ID = "analytical_risk_expert"
    NAME = "Alex - Risk Analysis Expert"
    DESCRIPTION = "Analytical risk expert specializing in risk assessment, analysis, and mitigation strategies"
    
    @staticmethod
    def get_system_prompt() -> str:
        capabilities = RiskAnalysisExpertConfig.get_capabilities()
        use_cases = [
            "Risk modeling", "Control gap analysis", "Threat assessment", "Business impact analysis",
            "Risk register maintenance", "Mitigation strategy development"
        ]
        
        return PromptComponents.build_system_prompt(
            agent_id=RiskAnalysisExpertConfig.ID,
            name=RiskAnalysisExpertConfig.NAME,
            role_description=RiskAnalysisExpertConfig.DESCRIPTION,
            capabilities=capabilities,
            use_cases=use_cases
        )
    
    @staticmethod
    def get_capabilities() -> List[AgentCapability]:
        return [
            AgentCapability.QUESTION_ANSWERING,
            AgentCapability.VOICE_PROCESSING,
            AgentCapability.TASK_ASSISTANCE,
            AgentCapability.DATA_ANALYSIS
        ]
    
    @staticmethod
    def get_specialized_tools() -> List[str]:
        return PromptComponents.get_specialized_tools_for_role(RiskAnalysisExpertConfig.ID)
    
    @staticmethod
    def get_voice_settings() -> Dict[str, str]:
        return PromptComponents.get_voice_settings_for_personality(RiskAnalysisExpertConfig.ID)


class GovernanceStrategistConfig:
    """Configuration for Sam - Governance Strategist."""
    
    ID = "strategic_governance"
    NAME = "Sam - Governance Strategist"
    DESCRIPTION = "Strategic governance specialist focused on governance frameworks, policy development, and board-level guidance"
    
    @staticmethod
    def get_system_prompt() -> str:
        capabilities = GovernanceStrategistConfig.get_capabilities()
        use_cases = [
            "Governance framework design", "Policy development", "Board reporting",
            "Stakeholder engagement", "Governance maturity assessment", "Strategic planning"
        ]
        
        return PromptComponents.build_system_prompt(
            agent_id=GovernanceStrategistConfig.ID,
            name=GovernanceStrategistConfig.NAME,
            role_description=GovernanceStrategistConfig.DESCRIPTION,
            capabilities=capabilities,
            use_cases=use_cases
        )
    
    @staticmethod
    def get_capabilities() -> List[AgentCapability]:
        return [
            AgentCapability.QUESTION_ANSWERING,
            AgentCapability.VOICE_PROCESSING,
            AgentCapability.TASK_ASSISTANCE,
            AgentCapability.CREATIVE_WRITING
        ]
    
    @staticmethod
    def get_specialized_tools() -> List[str]:
        return PromptComponents.get_specialized_tools_for_role(GovernanceStrategistConfig.ID)
    
    @staticmethod
    def get_voice_settings() -> Dict[str, str]:
        return PromptComponents.get_voice_settings_for_personality(GovernanceStrategistConfig.ID)


class GRCAgentConfigRegistry:
    """Registry for all GRC agent configurations."""
    
    CONFIGS = {
        EmpathicInterviewerConfig.ID: EmpathicInterviewerConfig,
        ComplianceAuthorityConfig.ID: ComplianceAuthorityConfig,
        RiskAnalysisExpertConfig.ID: RiskAnalysisExpertConfig,
        GovernanceStrategistConfig.ID: GovernanceStrategistConfig,
    }
    
    @classmethod
    def get_config(cls, agent_id: str):
        """Get configuration class for a specific agent."""
        return cls.CONFIGS.get(agent_id)
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, Any]:
        """Get all agent configurations."""
        return cls.CONFIGS
    
    @classmethod
    def build_agent_metadata(cls, agent_id: str) -> Dict[str, Any]:
        """Build agent metadata for API responses."""
        config = cls.get_config(agent_id)
        if not config:
            return {}
        
        metadata = {
            "id": config.ID,
            "name": config.NAME,
            "description": config.DESCRIPTION,
            "personality": config.ID,
            "capabilities": config.get_capabilities(),
            "specialized_tools": config.get_specialized_tools(),
            "status": "active",
            "created_at": datetime.now(UTC).isoformat()
        }
        
        # Add voice settings if agent has voice processing capability
        if hasattr(config, 'get_voice_settings'):
            metadata["voice_settings"] = config.get_voice_settings()
        
        return metadata 