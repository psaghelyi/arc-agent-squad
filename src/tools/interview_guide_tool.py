"""
Interview Guide Tool

This tool provides structured interview templates and guidance for conducting
various types of GRC interviews. It leverages the InterviewTemplates class
to provide standardized interview frameworks.
"""

import json
from typing import Dict, List, Any, Optional
from agent_squad.utils import AgentTool
from src.agents.interview_templates import InterviewTemplates, InterviewType, InterviewGuide


class InterviewGuideTool:
    """Tool for providing structured interview guidance and templates."""
    
    def __init__(self):
        self.templates = InterviewTemplates()
        self.current_guides: Dict[str, InterviewGuide] = {}
    
    def get_available_interview_types(self) -> List[Dict[str, str]]:
        """
        Get a list of available interview types with descriptions.
        
        Returns:
            List of interview types with names and descriptions
        """
        return [
            {
                "type": "compliance_audit",
                "name": "Compliance Audit Interview",
                "description": "Structured interview for compliance audit purposes"
            },
            {
                "type": "risk_assessment", 
                "name": "Risk Assessment Interview",
                "description": "Interview focused on identifying and evaluating risks"
            },
            {
                "type": "control_testing",
                "name": "Control Testing Interview", 
                "description": "Interview to understand and test control effectiveness"
            },
            {
                "type": "stakeholder_consultation",
                "name": "Stakeholder Consultation",
                "description": "General consultations with stakeholders on GRC matters"
            }
        ]
    
    def start_interview_guide(self, interview_type: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Start a new interview guide for the specified type.
        
        Args:
            interview_type: Type of interview (compliance_audit, risk_assessment, etc.)
            session_id: Session identifier for tracking
            
        Returns:
            Interview guide with introduction and opening questions
        """
        try:
            # Convert string to enum
            interview_enum = InterviewType(interview_type)
            
            # Create interview guide
            guide = InterviewGuide(interview_enum)
            self.current_guides[session_id] = guide
            
            # Get the template
            template = guide.template
            
            return {
                "success": True,
                "interview_type": interview_type,
                "name": template["name"],
                "description": template["description"],
                "introduction": template["introduction"],
                "opening_questions": template.get("opening_questions", []),
                "sections": guide.get_available_sections(),
                "session_id": session_id,
                "message": f"Interview guide for {template['name']} has been started. Use the introduction to begin the interview."
            }
            
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid interview type: {interview_type}. Available types: {[t.value for t in InterviewType]}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start interview guide: {str(e)}"
            }
    
    def get_interview_section(self, section_name: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Get questions for a specific interview section.
        
        Args:
            section_name: Name of the section (e.g., "process_questions", "control_questions")
            session_id: Session identifier
            
        Returns:
            Questions for the specified section
        """
        if session_id not in self.current_guides:
            return {
                "success": False,
                "error": "No active interview guide found. Please start an interview guide first."
            }
        
        guide = self.current_guides[session_id]
        questions = guide.get_section_questions(section_name)
        
        if questions:
            return {
                "success": True,
                "section": section_name,
                "questions": questions,
                "message": f"Here are the {section_name.replace('_', ' ')} for your interview."
            }
        else:
            return {
                "success": False,
                "error": f"Section '{section_name}' not found. Available sections: {guide.get_available_sections()}"
            }
    
    def get_follow_up_prompts(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Get follow-up prompts for deeper questioning.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Follow-up prompts for the interview
        """
        if session_id not in self.current_guides:
            return {
                "success": False,
                "error": "No active interview guide found. Please start an interview guide first."
            }
        
        guide = self.current_guides[session_id]
        prompts = guide.get_follow_up_prompts()
        
        return {
            "success": True,
            "follow_up_prompts": prompts,
            "message": "Here are follow-up prompts to encourage deeper responses."
        }
    
    def get_interview_closing(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Get the closing statement for the interview.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Closing statement for the interview
        """
        if session_id not in self.current_guides:
            return {
                "success": False,
                "error": "No active interview guide found. Please start an interview guide first."
            }
        
        guide = self.current_guides[session_id]
        closing = guide.get_closing()
        
        return {
            "success": True,
            "closing": closing,
            "message": "Here is the professional closing statement for your interview."
        }
    
    def get_interview_progress(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Get the current progress of the interview.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current interview progress and status
        """
        if session_id not in self.current_guides:
            return {
                "success": False,
                "error": "No active interview guide found."
            }
        
        guide = self.current_guides[session_id]
        
        return {
            "success": True,
            "interview_type": guide.interview_type.value,
            "completed_sections": guide.completed_sections,
            "available_sections": guide.get_available_sections(),
            "is_complete": guide.is_complete(),
            "progress_percentage": len(guide.completed_sections) / len(guide.get_available_sections()) * 100
        }
    
    def complete_interview(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Mark the interview as complete and clean up.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Completion status and summary
        """
        if session_id not in self.current_guides:
            return {
                "success": False,
                "error": "No active interview guide found."
            }
        
        guide = self.current_guides[session_id]
        
        # Mark as complete
        guide.mark_complete()
        
        # Clean up
        del self.current_guides[session_id]
        
        return {
            "success": True,
            "message": "Interview completed successfully. Thank you for using the interview guide.",
            "completed_sections": guide.completed_sections,
            "interview_type": guide.interview_type.value
        }


# Global instance for use in agent configurations
interview_guide_tool = InterviewGuideTool()


def get_interview_types() -> str:
    """
    Get available interview types and descriptions.
    
    Returns:
        JSON string of available interview types
    """
    result = interview_guide_tool.get_available_interview_types()
    return json.dumps(result, indent=2)


def start_interview(interview_type: str, session_id: str = "default") -> str:
    """
    Start a structured interview guide for the specified type.
    
    Args:
        interview_type: Type of interview (compliance_audit, risk_assessment, control_testing, stakeholder_consultation)
        session_id: Session identifier for tracking (optional)
        
    Returns:
        JSON string with interview introduction and opening questions
    """
    result = interview_guide_tool.start_interview_guide(interview_type, session_id)
    return json.dumps(result, indent=2)


def get_section_questions(section_name: str, session_id: str = "default") -> str:
    """
    Get questions for a specific interview section.
    
    Args:
        section_name: Name of the section (e.g., "process_questions", "control_questions", "risk_identification")
        session_id: Session identifier (optional)
        
    Returns:
        JSON string with questions for the specified section
    """
    result = interview_guide_tool.get_interview_section(section_name, session_id)
    return json.dumps(result, indent=2)


def get_follow_up_prompts(session_id: str = "default") -> str:
    """
    Get follow-up prompts for deeper questioning during the interview.
    
    Args:
        session_id: Session identifier (optional)
        
    Returns:
        JSON string with follow-up prompts
    """
    result = interview_guide_tool.get_follow_up_prompts(session_id)
    return json.dumps(result, indent=2)


def get_interview_closing(session_id: str = "default") -> str:
    """
    Get the professional closing statement for the interview.
    
    Args:
        session_id: Session identifier (optional)
        
    Returns:
        JSON string with closing statement
    """
    result = interview_guide_tool.get_interview_closing(session_id)
    return json.dumps(result, indent=2)


def get_interview_progress(session_id: str = "default") -> str:
    """
    Get the current progress of the interview.
    
    Args:
        session_id: Session identifier (optional)
        
    Returns:
        JSON string with interview progress information
    """
    result = interview_guide_tool.get_interview_progress(session_id)
    return json.dumps(result, indent=2)


def complete_interview(session_id: str = "default") -> str:
    """
    Mark the interview as complete and clean up resources.
    
    Args:
        session_id: Session identifier (optional)
        
    Returns:
        JSON string with completion status
    """
    result = interview_guide_tool.complete_interview(session_id)
    return json.dumps(result, indent=2)


# Create AgentTool instances for the interview guide tool
interview_guide_tool_agent = AgentTool(
    name="interview_guide_tool",
    description="Provides structured interview templates and guidance for conducting various types of GRC interviews including compliance audits, risk assessments, control testing, and stakeholder consultations.",
    properties={
        "get_interview_types": {
            "type": "function",
            "function": {
                "name": "get_interview_types",
                "description": "Get available interview types with descriptions",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        "start_interview": {
            "type": "function", 
            "function": {
                "name": "start_interview",
                "description": "Start a structured interview guide for the specified type",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interview_type": {
                            "type": "string",
                            "description": "Type of interview (compliance_audit, risk_assessment, control_testing, stakeholder_consultation)",
                            "enum": ["compliance_audit", "risk_assessment", "control_testing", "stakeholder_consultation"]
                        },
                        "session_id": {
                            "type": "string", 
                            "description": "Session identifier for tracking (optional)",
                            "default": "default"
                        }
                    },
                    "required": ["interview_type"]
                }
            }
        },
        "get_section_questions": {
            "type": "function",
            "function": {
                "name": "get_section_questions", 
                "description": "Get questions for a specific interview section",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "section_name": {
                            "type": "string",
                            "description": "Name of the section (e.g., 'process_questions', 'control_questions', 'risk_identification')"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier (optional)",
                            "default": "default"
                        }
                    },
                    "required": ["section_name"]
                }
            }
        },
        "get_follow_up_prompts": {
            "type": "function",
            "function": {
                "name": "get_follow_up_prompts",
                "description": "Get follow-up prompts for deeper questioning during the interview", 
                "parameters": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier (optional)",
                            "default": "default"
                        }
                    },
                    "required": []
                }
            }
        },
        "get_interview_closing": {
            "type": "function",
            "function": {
                "name": "get_interview_closing",
                "description": "Get the professional closing statement for the interview",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier (optional)",
                            "default": "default"
                        }
                    },
                    "required": []
                }
            }
        },
        "get_interview_progress": {
            "type": "function",
            "function": {
                "name": "get_interview_progress",
                "description": "Get the current progress of the interview",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string", 
                            "description": "Session identifier (optional)",
                            "default": "default"
                        }
                    },
                    "required": []
                }
            }
        },
        "complete_interview": {
            "type": "function",
            "function": {
                "name": "complete_interview",
                "description": "Mark the interview as complete and clean up resources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier (optional)", 
                            "default": "default"
                        }
                    },
                    "required": []
                }
            }
        }
    },
    functions={
        "get_interview_types": get_interview_types,
        "start_interview": start_interview,
        "get_section_questions": get_section_questions,
        "get_follow_up_prompts": get_follow_up_prompts,
        "get_interview_closing": get_interview_closing,
        "get_interview_progress": get_interview_progress,
        "complete_interview": complete_interview
    }
)