# Hierarchical Agent Routing Implementation

## Overview

This implementation adds **confidence-based hierarchical routing** to the GRC Agent Squad, allowing intelligent routing between specialists and supervisors based on query complexity and confidence scores.

## Key Features

### 🎯 **Smart Routing Logic**
- **Specialists First**: Clear, domain-specific queries (confidence ≥ 0.8) route directly to specialists
- **Supervisor Fallback**: Complex/ambiguous queries (confidence ≥ 0.6) route to supervisors for coordination
- **Default Fallback**: Very unclear queries route to default supervisor agent

### 🔧 **Built on Existing Infrastructure**
- **Extends BedrockClassifier**: Uses existing agent-squad framework
- **Leverages SupervisorAgent**: Existing supervisor coordination capabilities
- **Backwards Compatible**: Standard routing still available via configuration

### ⚙️ **Configuration-Driven**
- **YAML-based Squad Configs**: Define hierarchical structures declaratively
- **Configurable Thresholds**: Adjust confidence levels per deployment
- **Environment Settings**: Easy enable/disable via settings

## Implementation

### Files Created/Modified

#### New Files:
- `src/classifiers/hierarchical_classifier.py` - Hierarchical classifier extending BedrockClassifier
- `src/routing/routing_strategy.py` - Pluggable routing strategy interface
- `config/squad_configurations/grc_basic.yaml` - Basic hierarchical configuration
- `test_hierarchical_routing.py` - Basic implementation tests
- `test_integration_hierarchical.py` - Comprehensive integration tests
- `test_simple_hierarchical.py` - Simple real-world tests

#### Modified Files:
- `src/services/grc_agent_squad.py` - Added hierarchical routing support
- `src/utils/settings.py` - Added hierarchical routing settings

### Configuration Structure

```yaml
squad_config:
  name: "GRC Basic Squad"
  routing_strategy: "confidence_tiered"
  
  hierarchy:
    tiers:
      - name: "specialists"
        type: "specialist"
        confidence_threshold: 0.8
        agents:
          - empathetic_interviewer_executive
          - authoritative_compliance_executive
          - analytical_risk_expert_executive
          - strategic_governance_executive
      
      - name: "directors"
        type: "supervisor" 
        confidence_threshold: 0.6
        agents:
          - supervisor_grc

  fallback:
    agent: supervisor_grc
    confidence_threshold: 0.0
```

## Usage

### Basic Usage

```python
# Enable hierarchical routing (default)
squad = GRCAgentSquad(enable_hierarchical_routing=True)

# Process request - routing happens automatically
response = await squad.process_request(
    user_input="What are SOX compliance requirements?",
    session_id="user_session_123"
)
```

### Configuration Options

```python
# Use custom squad configuration
squad = GRCAgentSquad(
    enable_hierarchical_routing=True,
    squad_config_path="config/squad_configurations/custom_config.yaml"
)

# Disable hierarchical routing (standard behavior)
squad = GRCAgentSquad(enable_hierarchical_routing=False)
```

### Environment Settings

```bash
# Enable/disable hierarchical routing
ENABLE_HIERARCHICAL_ROUTING=true

# Squad configuration path  
SQUAD_CONFIG_PATH=config/squad_configurations/grc_basic.yaml
```

## Test Results

### ✅ Test 1: Specialist Routing
- **Query**: "What are SOX compliance requirements?"
- **Result**: Routed to `authoritative_compliance_executive`
- **Confidence**: 0.95
- **Status**: ✅ SUCCESS - Direct specialist routing

### ✅ Test 2: Supervisor Fallback
- **Query**: "Help me with our situation"  
- **Result**: Routed to `supervisor_grc`
- **Confidence**: 0.60
- **Status**: ✅ SUCCESS - Supervisor fallback

## Benefits

### 🚀 **Performance**
- **Reduced Supervisor Bottlenecks**: Clear queries bypass supervisor coordination
- **Faster Response Times**: Direct specialist routing for obvious domain queries
- **Intelligent Escalation**: Complex queries get appropriate supervisor attention

### 🔧 **Flexibility**
- **Configurable Thresholds**: Adjust confidence levels per use case
- **Multiple Squad Configurations**: Support different organizational structures
- **Easy Deployment**: Toggle hierarchical routing via settings

### 📈 **Scalability**
- **Foundation for Advanced Routing**: Ready for domain-based routing, multiple director tiers
- **Backwards Compatible**: Existing systems continue to work
- **Incremental Adoption**: Can be enabled selectively

## Architecture

```
User Input
    ↓
HierarchicalClassifier
    ↓
┌─ Try Specialists (confidence ≥ 0.8)
│   ├─ authoritative_compliance_executive
│   ├─ analytical_risk_expert_executive  
│   ├─ strategic_governance_executive
│   └─ empathetic_interviewer_executive
│
├─ Try Supervisors (confidence ≥ 0.6)
│   └─ supervisor_grc
│
└─ Fallback (confidence ≥ 0.0)
    └─ supervisor_grc (default)
```

## Running Tests

```bash
# Basic implementation test
source venv/bin/activate && python test_hierarchical_routing.py

# Simple integration test (real AWS calls)
source venv/bin/activate && python test_simple_hierarchical.py

# Comprehensive integration test (longer)
source venv/bin/activate && python test_integration_hierarchical.py
```

## Next Steps

The foundation is ready for advanced features:

1. **Domain-Based Routing**: Route by governance/risk/compliance domains
2. **Multiple Director Tiers**: Department → Division → Enterprise hierarchy  
3. **Dynamic Thresholds**: Adjust confidence based on context
4. **Advanced Configurations**: Support complex organizational structures

## Implementation Status

- ✅ **Core Implementation**: Complete and tested
- ✅ **Basic Configuration**: Working with GRC Basic Squad
- ✅ **Integration Tests**: Passing with real AWS/Bedrock calls
- ✅ **Backwards Compatibility**: Standard routing preserved
- ✅ **Settings Integration**: Environment-based configuration
- 🔄 **Advanced Features**: Ready for future enhancement

**Status**: Ready for production use with basic hierarchical routing!