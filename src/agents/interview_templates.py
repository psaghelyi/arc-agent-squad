"""
Interview Templates for GRC Scenarios

This module contains structured interview templates for different types of
GRC interviews, assessments, and consultations.
"""

from typing import Dict, List, Any
from enum import Enum


class InterviewType(str, Enum):
    """Types of GRC interviews."""
    COMPLIANCE_AUDIT = "compliance_audit"
    RISK_ASSESSMENT = "risk_assessment" 
    CONTROL_TESTING = "control_testing"
    STAKEHOLDER_CONSULTATION = "stakeholder_consultation"
    INCIDENT_INVESTIGATION = "incident_investigation"
    GOVERNANCE_REVIEW = "governance_review"


class InterviewTemplates:
    """Collection of interview templates for different GRC scenarios."""
    
    COMPLIANCE_AUDIT = {
        "name": "Compliance Audit Interview",
        "description": "Structured interview for compliance audit purposes",
        "introduction": """Hello, I'm Emma, your compliance interviewer. I'll be conducting a compliance audit interview today to understand your processes and controls. This conversation is confidential and designed to help ensure our organization meets regulatory requirements. Please feel free to ask questions at any time.""",
        
        "opening_questions": [
            "Can you please introduce yourself and describe your role in the organization?",
            "How long have you been in this position?",
            "What are your primary responsibilities related to compliance?"
        ],
        
        "process_questions": [
            "Can you walk me through your typical daily/weekly compliance activities?",
            "What policies and procedures do you follow in your work?",
            "How do you stay updated on regulatory changes that affect your area?",
            "What documentation do you maintain for compliance purposes?"
        ],
        
        "control_questions": [
            "What controls are in place to ensure compliance in your area?",
            "How do you monitor the effectiveness of these controls?",
            "Can you provide examples of how these controls have prevented issues?",
            "What happens when a control fails or an exception occurs?"
        ],
        
        "challenge_questions": [
            "What compliance challenges do you face in your role?",
            "Have you encountered any situations where compliance requirements conflicted with business objectives?",
            "What improvements would you suggest for our compliance program?"
        ],
        
        "closing": """Thank you for your time and candid responses. Is there anything else you'd like to add about compliance in your area? Do you have any questions about this interview or the audit process?""",
        
        "follow_up_prompts": [
            "Can you provide more details about that?",
            "What was the outcome of that situation?",
            "How did that make you feel?",
            "What would you do differently next time?",
            "Who else was involved in that process?"
        ]
    },
    
    RISK_ASSESSMENT = {
        "name": "Risk Assessment Interview",
        "description": "Interview focused on identifying and evaluating risks",
        "introduction": """Hi, I'm Emma. I'm here to conduct a risk assessment interview to better understand the risks in your area of responsibility. This helps us identify potential issues before they become problems and ensures we have appropriate risk management strategies in place.""",
        
        "opening_questions": [
            "What do you see as the biggest risks in your area of work?",
            "How do you currently identify and assess risks?",
            "What risk management processes do you follow?"
        ],
        
        "risk_identification": [
            "Can you describe any recent incidents or near-misses in your area?",
            "What external factors could impact your operations?",
            "What internal factors pose risks to your objectives?",
            "Are there any emerging risks you're concerned about?"
        ],
        
        "risk_assessment": [
            "How do you evaluate the likelihood of these risks occurring?",
            "What would be the potential impact if these risks materialized?",
            "How do you prioritize different risks?",
            "What factors do you consider when assessing risk severity?"
        ],
        
        "mitigation_strategies": [
            "What controls or measures are in place to mitigate these risks?",
            "How effective do you think these mitigation strategies are?",
            "What additional risk mitigation measures would you recommend?",
            "How do you monitor and review risk mitigation effectiveness?"
        ],
        
        "closing": """Thank you for sharing your insights on risk management. Your perspective is valuable for our overall risk assessment. Is there anything else about risks in your area that we should be aware of?"""
    },
    
    CONTROL_TESTING = {
        "name": "Control Testing Interview", 
        "description": "Interview to understand and test the effectiveness of controls",
        "introduction": """Hello, I'm Emma. I'm here to understand how specific controls work in practice and test their effectiveness. This helps ensure our controls are operating as designed and achieving their intended objectives.""",
        
        "control_understanding": [
            "Can you explain how this control is supposed to work?",
            "What is the purpose of this control?",
            "Who is responsible for performing this control?",
            "How frequently is this control performed?"
        ],
        
        "control_execution": [
            "Can you walk me through how you perform this control?",
            "What documentation do you create when performing this control?",
            "What systems or tools do you use?",
            "How do you know the control has been performed correctly?"
        ],
        
        "exception_handling": [
            "What happens when you identify an issue during control execution?",
            "Can you give me an example of an exception you've encountered?",
            "How are exceptions documented and resolved?",
            "Who do you escalate issues to?"
        ],
        
        "effectiveness_assessment": [
            "How do you know this control is working effectively?",
            "What would happen if this control failed?",
            "Have there been any changes to this control recently?",
            "What improvements would you suggest for this control?"
        ]
    },
    
    STAKEHOLDER_CONSULTATION = {
        "name": "Stakeholder Consultation",
        "description": "General consultation with stakeholders on GRC matters",
        "introduction": """Hi, I'm Emma. I'm conducting stakeholder consultations to gather input on our GRC programs and understand your perspective on governance, risk, and compliance matters that affect your work.""",
        
        "stakeholder_perspective": [
            "How do GRC requirements impact your daily work?",
            "What GRC-related challenges do you face?",
            "How well do you think our current GRC programs are working?",
            "What would make GRC processes easier for you to follow?"
        ],
        
        "program_effectiveness": [
            "Which GRC programs or processes work well in your opinion?",
            "Which ones need improvement?",
            "How could we better communicate GRC requirements?",
            "What training or support would be helpful?"
        ],
        
        "future_considerations": [
            "What changes do you see coming that might affect GRC?",
            "What new risks or opportunities should we be considering?",
            "How can we better integrate GRC into business processes?",
            "What would success look like for GRC in your area?"
        ]
    }
    
    @classmethod
    def get_template(cls, interview_type: InterviewType) -> Dict[str, Any]:
        """Get a specific interview template."""
        template_map = {
            InterviewType.COMPLIANCE_AUDIT: cls.COMPLIANCE_AUDIT,
            InterviewType.RISK_ASSESSMENT: cls.RISK_ASSESSMENT,
            InterviewType.CONTROL_TESTING: cls.CONTROL_TESTING,
            InterviewType.STAKEHOLDER_CONSULTATION: cls.STAKEHOLDER_CONSULTATION
        }
        return template_map.get(interview_type, {})
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available interview templates."""
        return {
            InterviewType.COMPLIANCE_AUDIT: cls.COMPLIANCE_AUDIT,
            InterviewType.RISK_ASSESSMENT: cls.RISK_ASSESSMENT,
            InterviewType.CONTROL_TESTING: cls.CONTROL_TESTING,
            InterviewType.STAKEHOLDER_CONSULTATION: cls.STAKEHOLDER_CONSULTATION
        }
    
    @classmethod
    def get_template_names(cls) -> List[str]:
        """Get names of all available templates."""
        return [template["name"] for template in cls.get_all_templates().values()]


class InterviewGuide:
    """Helper class for conducting interviews using templates."""
    
    def __init__(self, interview_type: InterviewType):
        self.template = InterviewTemplates.get_template(interview_type)
        self.current_section = "introduction"
        self.completed_sections = []
    
    def get_introduction(self) -> str:
        """Get the interview introduction."""
        return self.template.get("introduction", "")
    
    def get_questions_for_section(self, section: str) -> List[str]:
        """Get questions for a specific section."""
        return self.template.get(section, [])
    
    def get_follow_up_prompts(self) -> List[str]:
        """Get follow-up prompts for deeper exploration."""
        return self.template.get("follow_up_prompts", [
            "Can you tell me more about that?",
            "What was your experience with that?",
            "How did that affect your work?",
            "What would you recommend?"
        ])
    
    def get_closing(self) -> str:
        """Get the interview closing statement."""
        return self.template.get("closing", "Thank you for your time and valuable insights.")
    
    def mark_section_complete(self, section: str):
        """Mark a section as completed."""
        if section not in self.completed_sections:
            self.completed_sections.append(section)
    
    def get_completion_status(self) -> Dict[str, Any]:
        """Get interview completion status."""
        all_sections = [key for key in self.template.keys() 
                       if isinstance(self.template[key], list)]
        
        return {
            "total_sections": len(all_sections),
            "completed_sections": len(self.completed_sections),
            "completion_percentage": len(self.completed_sections) / len(all_sections) * 100 if all_sections else 0,
            "remaining_sections": [section for section in all_sections 
                                 if section not in self.completed_sections]
        } 