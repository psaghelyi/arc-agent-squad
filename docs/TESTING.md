# Voice Agent Swarm - Testing Guide

This document provides comprehensive information about testing the Voice Agent Swarm project.

## Test Structure

The test suite is organized into multiple categories to provide comprehensive coverage:

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── test_health.py            # Health check endpoint tests
│   └── test_agent_orchestrator.py # Agent manipulation and orchestration tests
├── integration/                   # Integration tests for complete workflows
│   ├── test_chat_integration.py  # Chat flow integration tests
│   └── test_api_integration.py   # API endpoint integration tests
└── __init__.py
```

## Test Categories

### 1. Unit Tests

#### Health Check Tests (`test_health.py`)
- ✅ Basic health endpoint functionality
- ✅ Readiness and liveness probes
- ✅ Root endpoint HTML response

#### Agent Orchestrator Tests (`test_agent_orchestrator.py`)
- ✅ **Agent Manipulation:**
  - Creating agents with different personalities and capabilities
  - Creating agents with custom parameters
  - Deleting agents
  - Listing agents (empty and populated)
  - Initializing default agents

- ✅ **Agent Selection Logic:**
  - Empathetic request → Emma the Helper
  - Urgent request → Alex the Direct
  - Technical request → Dr. Morgan (or Emma)
  - Creative request → Sam the Buddy
  - Error handling when no agents available

- ✅ **Request Processing:**
  - Successful request processing through selected agent
  - Error handling when agent processing fails
  - Session tracking and statistics
  - Concurrent agent operations

### 2. Integration Tests

#### Chat Integration Tests (`test_chat_integration.py`)
- ✅ **Complete Chat Flow:**
  - Simple chat conversation with agent selection
  - Multi-turn conversations with session continuity
  - Different request types selecting appropriate agents
  - Concurrent chat sessions handling

- ✅ **Advanced Features:**
  - Error handling in chat processing
  - Agent selection confidence scoring
  - Chat with additional context parameters
  - Agent response formatting (various content types)
  - Session isolation between different users

#### API Integration Tests (`test_api_integration.py`)
- ✅ **Endpoint Testing:**
  - Health check endpoints
  - Agent listing and details
  - Chat functionality through REST API
  - Personality presets and capabilities endpoints

- ✅ **API Behavior:**
  - Input validation and error responses
  - Concurrent API request handling
  - Session continuity through API
  - Response format consistency
  - CORS headers and error formatting

## Running Tests

### Quick Test Runner

Use the provided test runner for easy execution:

```bash
# Run all tests
make test

# Run specific test categories
make test-unit                # Unit tests only
make test-integration        # Integration tests only
make test-orchestrator       # Agent orchestrator tests only
make test-chat              # Chat integration tests only
make test-api               # API integration tests only
make test-quick             # Quick subset of tests
make test-coverage          # Tests with coverage report
```

### Direct pytest Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests with verbose output
pytest tests/ -v

# Run specific test files
pytest tests/unit/test_agent_orchestrator.py -v
pytest tests/integration/test_chat_integration.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test methods
pytest tests/unit/test_agent_orchestrator.py::TestAgentOrchestrator::test_create_agent -v
```

## Test Features Covered

### ✅ Agent Squad Manipulation
- **Creating Agents:** Test creation with different personalities, capabilities, and custom parameters
- **Removing Agents:** Test deletion of existing and non-existent agents
- **Changing Parameters:** Test agent configuration with custom settings
- **Listing Agents:** Test agent enumeration and details retrieval

### ✅ Orchestration Capabilities
- **Agent Selection:** Test intelligent selection based on request analysis
- **Confidence Scoring:** Test that selection provides meaningful confidence scores
- **Selection Reasoning:** Test that selection includes human-readable reasoning
- **Fallback Handling:** Test behavior when no agents are available

### ✅ Chat Flow Integration
- **Basic Chat:** Test simple request → agent selection → response flow
- **Multi-turn Conversations:** Test session continuity and context retention
- **Auto Agent Selection:** Test that different request types select appropriate agents
- **Error Handling:** Test graceful error handling throughout the chat flow
- **Concurrent Sessions:** Test handling multiple simultaneous conversations

## Test Configuration

### Mock Strategy
- **Agent Responses:** LLM responses are mocked to ensure consistent test results
- **Memory Service:** Redis operations are mocked for unit tests, graceful fallback for integration
- **AWS Services:** Not yet implemented, will be mocked when added

### Test Data
- **Personalities:** Tests use the 4 default agent personalities (kind_helpful, to_the_point, professional, casual_friendly)
- **Capabilities:** Tests cover all defined agent capabilities
- **Request Types:** Tests include emotional, urgent, technical, and creative request patterns

## Test Results Summary

```
✅ Unit Tests: 22 tests passing
  - Health Check: 4 tests
  - Agent Orchestrator: 18 tests

✅ Integration Tests: 17 tests passing  
  - Chat Integration: 9 tests
  - API Integration: 8 tests

✅ Total: 39 tests passing
✅ Coverage: Comprehensive coverage of core functionality
```

## Key Test Scenarios

### Agent Manipulation Examples

```python
# Create agent with custom parameters
agent_id = await orchestrator.create_agent(
    name="Custom Agent",
    personality_type=AgentPersonality.PROFESSIONAL,
    capabilities=[AgentCapability.TECHNICAL_SUPPORT],
    memory_enabled=False,
    voice_enabled=True
)

# Delete agent
success = await orchestrator.delete_agent(agent_id)

# List all agents
agents = await orchestrator.list_agents()
```

### Chat Flow Examples

```python
# Simple chat request
request = OrchestratorRequest(
    user_input="Hello, I need help with something",
    session_id="test-session",
    context={}
)

result = await orchestrator.process_request(request)
# Verifies: agent selection, response generation, session tracking
```

### API Integration Examples

```python
# Chat through REST API
chat_request = {
    "message": "I'm feeling sad and need emotional support",
    "session_id": "test-session"
}

response = await client.post("/api/agents/chat", json=chat_request)
# Verifies: Emma the Helper selected for emotional support
```

## Continuous Integration

The test suite is designed to:
- Run quickly (all tests complete in under 2 minutes)
- Be deterministic (consistent results across runs)
- Provide clear failure messages with detailed context
- Support parallel execution for faster CI/CD

## Future Test Enhancements

### Planned Additions
- **Voice Processing Tests:** When AWS Transcribe/Polly integration is added
- **WebRTC Tests:** When real-time audio streaming is implemented
- **Performance Tests:** Load testing for concurrent users
- **End-to-End Tests:** Full workflow tests with real AWS services

### Test Improvements
- **Better Agent Selection Tuning:** More precise scoring algorithm tests
- **Memory Persistence Tests:** Redis integration testing
- **AWS Service Integration:** Real AWS service testing (with mocking for CI)

## Troubleshooting Tests

### Common Issues

1. **Agent Selection Variability**
   - Agent selection is probabilistic based on scoring
   - Tests use flexible assertions to accommodate reasonable variations
   - Check confidence scores and reasoning for debugging

2. **Memory Service Tests**
   - Tests gracefully handle Redis unavailability
   - In-memory fallback mode is used for testing
   - No Redis dependency required for test execution

3. **Async Test Issues**
   - All async tests use proper pytest-asyncio fixtures
   - Ensure `pytest-asyncio` is installed and configured

### Debug Mode

```bash
# Run tests with debug output
pytest tests/ -v -s --tb=long

# Run specific failing test with full output
pytest tests/unit/test_agent_orchestrator.py::TestAgentOrchestrator::test_create_agent -v -s
```

## Contributing to Tests

### Adding New Tests
1. Follow the existing test structure and naming conventions
2. Use appropriate fixtures for setup and teardown
3. Mock external dependencies (AWS services, Redis, etc.)
4. Include both positive and negative test cases
5. Add comprehensive docstrings explaining test purpose

### Test Guidelines
- **Unit Tests:** Test individual components in isolation
- **Integration Tests:** Test complete workflows and interactions
- **Mock Strategy:** Mock external services, use real internal logic
- **Assertions:** Use descriptive assertions with helpful error messages
- **Coverage:** Aim for high coverage of critical paths 