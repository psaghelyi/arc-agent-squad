"""
Super Agent - Replaced with Agent Squad Framework's SupervisorAgent

This module now uses the SupervisorAgent from the agent-squad framework
for better coordination and management of agent squads.
"""

import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime

from agent_squad.agents import SupervisorAgent, SupervisorAgentOptions
from agent_squad.agents import BedrockLLMAgent, BedrockLLMAgentOptions
from agent_squad.types import ConversationMessage, ParticipantRole

from ..models.agent_models import (
    AgentConfiguration,
    AgentPersonalityConfig,
    AgentPersonality,
    AgentTone,
    AgentCapability,
    OrchestratorRequest
)
from ..services.memory_service import MemoryService
from ..tools.tool_registry import ToolRegistry, get_default_registry
from ..tools.base_tool import ToolResult


class SuperAgent:
    """
    Super Agent wrapper that uses agent-squad's SupervisorAgent for coordination.
    
    This agent serves as the single point of contact for users and leverages
    the agent-squad framework's SupervisorAgent for:
    1. Analyzing user requests
    2. Coordinating with team agents
    3. Managing tool usage
    4. Providing unified responses
    """
    
    def __init__(self, 
                 orchestrator,
                 memory_service: MemoryService,
                 tool_registry: Optional[ToolRegistry] = None):
        """
        Initialize the Super Agent with SupervisorAgent from agent-squad.
        
        Args:
            orchestrator: Agent orchestrator instance
            memory_service: Memory service for conversation history
            tool_registry: Tool registry for external capabilities
        """
        self.orchestrator = orchestrator
        self.memory_service = memory_service
        self.tool_registry = tool_registry or get_default_registry()
        self.logger = structlog.get_logger(__name__)
        
        # Create the lead agent (supervisor) using BedrockLLMAgent
        self.lead_agent = BedrockLLMAgent(BedrockLLMAgentOptions(
            name="Team Lead",
            description="Coordinates specialized team members and handles complex requests",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            streaming=True
        ))
        
        # Initialize team agents from the orchestrator
        self.team_agents = self._initialize_team_agents()
        
        # Create the SupervisorAgent
        self.supervisor_agent = SupervisorAgent(SupervisorAgentOptions(
            name="SuperAgent",
            description="Coordinating agent that manages the entire agent squad and tool usage",
            lead_agent=self.lead_agent,
            team=self.team_agents,
            storage=None,  # We'll use our own memory service
            trace=True,
            extra_tools=self._create_custom_tools()
        ))
        
        # Configuration for compatibility
        self.config = AgentConfiguration(
            name="Super Agent",
            description="Coordinating agent that manages the entire agent squad and tool usage",
            personality=AgentPersonalityConfig(
                personality_type=AgentPersonality.PROFESSIONAL,
                tone=AgentTone.WARM,
                greeting_message="Hello! I'm your Super Agent. I'll analyze your request and connect you with the best agent or tools to help you.",
                system_prompt=self._get_system_prompt(),
                response_style="Coordinator and facilitator",
                max_response_length=1000,
                use_emojis=True,
                politeness_level=8,
                enthusiasm_level=6,
                asks_follow_up_questions=True,
                provides_examples=True,
                shows_empathy=True,
                is_proactive=True
            ),
            capabilities=[
                AgentCapability.QUESTION_ANSWERING,
                AgentCapability.TASK_ASSISTANCE,
                AgentCapability.CUSTOMER_SUPPORT,
                AgentCapability.DATA_ANALYSIS
            ]
        )
        
        self.logger.info("Super Agent initialized with SupervisorAgent from agent-squad",
                        available_tools=len(self.tool_registry.list_tools()),
                        team_size=len(self.team_agents))
    
    def _initialize_team_agents(self) -> List[Any]:
        """Initialize team agents from the orchestrator's agents."""
        team_agents = []
        
        if self.orchestrator and hasattr(self.orchestrator, 'agents'):
            for agent_id, agent_instance in self.orchestrator.agents.items():
                # Create BedrockLLMAgent for each personality agent
                config = self.orchestrator.agent_configs.get(agent_id)
                if config:
                    team_agent = BedrockLLMAgent(BedrockLLMAgentOptions(
                        name=config.name,
                        description=config.description,
                        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                        streaming=False
                    ))
                    team_agents.append(team_agent)
        
        # If no agents from orchestrator, create default team
        if not team_agents:
            team_agents = [
                BedrockLLMAgent(BedrockLLMAgentOptions(
                    name="Emma the Helper",
                    description="Kind & helpful assistant for detailed explanations and support",
                    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
                )),
                BedrockLLMAgent(BedrockLLMAgentOptions(
                    name="Alex the Direct",
                    description="Direct & efficient assistant for quick answers and technical issues",
                    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
                )),
                BedrockLLMAgent(BedrockLLMAgentOptions(
                    name="Dr. Morgan",
                    description="Professional assistant for formal business interactions and data analysis",
                    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
                )),
                BedrockLLMAgent(BedrockLLMAgentOptions(
                    name="Sam the Buddy",
                    description="Casual & friendly assistant for creative tasks and natural conversations",
                    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
                ))
            ]
        
        return team_agents
    
    def _create_custom_tools(self) -> List[Any]:
        """Create custom tools from the tool registry for the SupervisorAgent."""
        from agent_squad.utils import AgentTool
        
        custom_tools = []
        
        # Convert our tool registry tools to agent-squad format
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                # Create AgentTool from our tool
                agent_tool = AgentTool(
                    name=tool.name,
                    description=tool.description,
                    properties=tool.get_schema().get("parameters", {}).get("properties", {}),
                    required=tool.get_schema().get("parameters", {}).get("required", []),
                    func=self._create_tool_wrapper(tool)
                )
                custom_tools.append(agent_tool)
        
        return custom_tools
    
    def _create_tool_wrapper(self, tool):
        """Create a wrapper function for our tools to work with agent-squad."""
        async def tool_wrapper(**kwargs):
            try:
                result = await tool.execute(**kwargs)
                if isinstance(result, ToolResult):
                    return {
                        "success": result.success,
                        "content": result.content,
                        "data": result.data,
                        "error": result.error
                    }
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "content": f"Error executing tool {tool.name}: {str(e)}"
                }
        
        return tool_wrapper
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the super agent."""
        return """You are the Super Agent, the coordinating intelligence for an agent squad system.

Your responsibilities:
1. Analyze user requests to understand their intent and requirements
2. Determine if external tools or APIs are needed to fulfill the request
3. Select the most appropriate agent from the squad based on personality and capabilities
4. Coordinate tool usage when needed
5. Provide clear, helpful responses that explain your reasoning

Available agent personalities in your squad:
- Emma the Helper: Kind & helpful, great for detailed explanations and support
- Alex the Direct: Straightforward & efficient, perfect for quick answers and technical issues
- Dr. Morgan: Professional, ideal for formal business interactions and data analysis
- Sam the Buddy: Casual & friendly, excellent for creative tasks and natural conversations

When you need to use tools or external APIs, clearly explain what you're doing and why.
Always be transparent about which agent you're selecting and your reasoning.

Be proactive in suggesting the best approach for each user request."""
    
    async def analyze_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a user request (maintained for backward compatibility).
        The SupervisorAgent handles this internally now.
        """
        # Basic analysis for backward compatibility
        analysis = {
            "needs_tools": "api" in user_input.lower() or "tool" in user_input.lower(),
            "recommended_tools": [],
            "agent_requirements": {
                "personality_preference": None,
                "required_capabilities": []
            },
            "complexity": "moderate",
            "intent": "general",
            "reasoning": "Delegated to SupervisorAgent for intelligent coordination"
        }
        
        return analysis
    
    async def process_request(self, 
                            input_text: str,
                            user_id: str = "default_user",
                            session_id: str = "default_session",
                            chat_history: Optional[List[ConversationMessage]] = None,
                            additional_params: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Process a user request through the SupervisorAgent.
        
        Args:
            input_text: User input text
            user_id: User identifier
            session_id: Session identifier
            chat_history: Previous conversation history
            additional_params: Additional parameters
            
        Returns:
            Response message
        """
        try:
            self.logger.info("Processing request through SupervisorAgent",
                           input_text=input_text,
                           user_id=user_id,
                           session_id=session_id)
            
            # Process through the SupervisorAgent
            response = await self.supervisor_agent.process_request(
                input_text,
                user_id,
                session_id
            )
            
            # Convert response format for backward compatibility
            if hasattr(response, 'streaming') and response.streaming:
                # Handle streaming response
                content_parts = []
                async for chunk in response.output:
                    if hasattr(chunk, 'text'):
                        content_parts.append(chunk.text)
                    else:
                        content_parts.append(str(chunk))
                
                full_content = ''.join(content_parts)
            else:
                # Handle non-streaming response
                if hasattr(response, 'output'):
                    full_content = response.output
                elif hasattr(response, 'content'):
                    full_content = response.content
                else:
                    full_content = str(response)
            
            # Store in memory if available
            if self.memory_service:
                try:
                    conversation = await self.memory_service.get_conversation(session_id)
                    if conversation:
                        conversation.add_message("user", input_text)
                        conversation.add_message("assistant", full_content)
                        await self.memory_service.store_conversation(conversation)
                except Exception as e:
                    self.logger.warning("Failed to store conversation", error=str(e))
            
            return ConversationMessage(
                role=ParticipantRole.ASSISTANT,
                content=[{"text": full_content}]
            )
            
        except Exception as e:
            self.logger.error("SupervisorAgent processing failed", error=str(e))
            error_response = f"❌ I encountered an error processing your request: {str(e)}\n\nPlease try rephrasing your request or contact support if the issue persists."
            
            return ConversationMessage(
                role=ParticipantRole.ASSISTANT,
                content=[{"text": error_response}]
            )
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return self.tool_registry.get_tool_schemas()
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get super agent statistics."""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "available_tools": len(self.tool_registry.list_tools()),
            "capabilities": [cap.value for cap in self.config.capabilities],
            "tool_schemas": self.get_available_tools(),
            "team_size": len(self.team_agents),
            "framework": "agent-squad SupervisorAgent"
        } 