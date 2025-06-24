# GRC Agent Configurations

This directory contains YAML configuration files for the four specialized GRC (Governance, Risk, and Compliance) agents.

## Agent Types

### Basic Agents
- `empathetic_interviewer.yaml` - Emma, Information Collector
- `authoritative_compliance.yaml` - Dr. Morgan, Compliance Authority  
- `analytical_risk_expert.yaml` - Alex, Risk Analysis Expert
- `strategic_governance.yaml` - Sam, Governance Strategist

### Advanced Agents (Executive-Level)
- `empathetic_interviewer_advanced.yaml` - Emma, Senior Information Collector
- `authoritative_compliance_advanced.yaml` - Dr. Morgan, Chief Compliance Officer
- `analytical_risk_expert_advanced.yaml` - Alex, Chief Risk Officer
- `strategic_governance_advanced.yaml` - Sam, Chief Governance Officer

## Schema Validation

All agent configuration files follow the JSON schema defined in `../agent-schema.json`.

### Editor Support

#### VS Code / Cursor
The workspace is configured with proper schema association in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    "./config/agent-schema.json": [
      "config/agents/*.yaml",
      "config/agents/**/*.yaml"
    ]
  }
}
```

#### YAML Language Server
Each YAML file includes a schema comment at the top:
```yaml
# yaml-language-server: $schema=../agent-schema.json
```

This ensures:
- ✅ **Schema validation** - Real-time validation against the agent schema
- ✅ **IntelliSense** - Auto-completion for valid properties
- ✅ **Error highlighting** - Invalid properties are highlighted
- ✅ **Documentation** - Hover tooltips show property descriptions

## Configuration Structure

Each agent configuration includes:

- **Basic Information**: `id`, `name`, `description`
- **Capabilities**: List of agent capabilities (e.g., `voice_processing`, `question_answering`)
- **Use Cases**: Specific scenarios where the agent excels
- **Specialized Tools**: Tools available to the agent
- **Voice Settings**: Amazon Polly configuration for text-to-speech
- **Personality**: Tone, approach, and behavioral traits
- **Model Settings**: AI model configuration and inference parameters
- **System Prompt**: The agent's core instructions and behavior

## Schema Reference

For detailed schema documentation, see `../agent-schema.json` which defines:
- Required and optional properties
- Property types and constraints
- Enumerated values for specific fields
- Property descriptions and examples

## Validation

Agent configurations are validated at runtime using the JSON schema. Invalid configurations will prevent the agent from loading and display detailed error messages.

## Adding New Agents

1. Create a new YAML file following the naming convention
2. Include the schema comment at the top
3. Follow the structure defined in `../agent-schema.json`
4. Test the configuration by loading it in the application
5. Update the active agents list in `src/utils/settings.py` if needed 