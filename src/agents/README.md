# GRC Agents Module

This module contains agent-specific configurations, templates, and utilities that complement the AWS Labs agent-squad framework used in the GRC Agent Squad system.

## Overview

The GRC Agent Squad uses the agent-squad framework for core orchestration and agent management, but this `src/agents/` module provides specialized configurations and tools for the four GRC agents:

- **Emma** - Information Collector (empathetic_interviewer)
- **Dr. Morgan** - Compliance Authority (authoritative_compliance)
- **Alex** - Risk Analysis Expert (analytical_risk_expert)
- **Sam** - Governance Strategist (strategic_governance)

## Module Structure

```
src/agents/
├── README.md                    # This file
├── __init__.py                  # Module initialization
├── grc_agent_configs.py         # Agent configuration classes
└── interview_templates.py       # Interview templates for GRC scenarios
```

## Components

### Agent Configuration Classes (`grc_agent_configs.py`)

Centralized configuration classes for each GRC agent that provide:

- **System Prompts**: Personality and behavior definitions
- **Capabilities**: List of agent capabilities (voice, text, analysis, etc.)
- **Specialized Tools**: Agent-specific tool requirements
- **Metadata**: Agent identification and description

**Usage Example:**
```python
from src.agents.grc_agent_configs import EmpathicInterviewerConfig, GRCAgentConfigRegistry

# Get system prompt for Emma
prompt = EmpathicInterviewerConfig.get_system_prompt()

# Get all agent configurations
all_configs = GRCAgentConfigRegistry.get_all_configs()

# Build metadata for API responses
metadata = GRCAgentConfigRegistry.build_agent_metadata("empathetic_interviewer")
```

### Interview Templates (`interview_templates.py`)

Structured interview templates for different GRC scenarios:

- **Compliance Audit Interview**: For compliance audit purposes
- **Risk Assessment Interview**: For identifying and evaluating risks
- **Control Testing Interview**: For testing control effectiveness
- **Stakeholder Consultation**: For gathering stakeholder input

**Usage Example:**
```python
from src.agents.interview_templates import InterviewTemplates, InterviewGuide, InterviewType

# Get a specific template
audit_template = InterviewTemplates.get_template(InterviewType.COMPLIANCE_AUDIT)

# Use interview guide for structured interviews
guide = InterviewGuide(InterviewType.COMPLIANCE_AUDIT)
intro = guide.get_introduction()
questions = guide.get_questions_for_section("opening_questions")
```

## Integration with Agent-Squad Framework

This module **complements** rather than replaces the agent-squad framework:

1. **Configuration**: Provides centralized agent configurations that can be used when initializing BedrockLLMAgent instances
2. **Templates**: Offers structured interview templates that agents can reference during conversations
3. **Utilities**: Supplies helper functions for agent-specific operations

The actual agent orchestration, routing, and conversation management is handled by the agent-squad framework in `src/services/grc_agent_squad.py`.

## Future Extensions

This module is designed to be extensible. Consider adding:

### Agent-Specific Tools
```python
# src/agents/compliance_tools.py
class ComplianceTools:
    def validate_regulation_compliance(self, controls: List[str]) -> Dict:
        """Validate compliance against specific regulations."""
        pass
```

### Performance Analytics
```python
# src/agents/analytics.py
class AgentAnalytics:
    def track_agent_selection_patterns(self):
        """Analyze which agents are selected for different request types."""
        pass
```

### Workflow Orchestration
```python
# src/agents/workflows.py
class GRCWorkflows:
    def compliance_assessment_workflow(self):
        """Multi-agent workflow for comprehensive compliance assessments."""
        pass
```

### Custom Agent Behaviors
```python
# src/agents/behaviors.py
class AgentBehaviors:
    def customize_response_style(self, agent_type: str, response: str) -> str:
        """Apply agent-specific response customizations."""
        pass
```

## Best Practices

1. **Centralization**: Keep agent-specific configurations centralized in this module
2. **Consistency**: Use the configuration classes to ensure consistent agent setup
3. **Templates**: Leverage interview templates for structured GRC interactions
4. **Extension**: Add new agent-specific functionality here rather than in the main service
5. **Testing**: Create tests for any new agent-specific functionality

## Contributing

When adding new agent configurations or templates:

1. Follow the existing pattern in `grc_agent_configs.py`
2. Add comprehensive docstrings and type hints
3. Include usage examples in docstrings
4. Update this README with new components
5. Add appropriate tests

## Dependencies

This module depends on:
- `src/models/agent_models.py` for AgentCapability enum
- Standard Python libraries (typing, datetime, enum)

The module is designed to be lightweight and focused on configuration and templates rather than complex business logic. 