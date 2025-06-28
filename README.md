# 🎯 GRC Agent Squad

**AI-powered agent squad specialized for Governance, Risk Management, and Compliance (GRC) using AWS services and agent-squad framework**

A specialized AI agent squad for Governance, Risk Management, and Compliance (GRC) using AWS services and the agent-squad framework. This project provides intelligent, voice-enabled agents that assist with compliance assessments, risk management, audit interviews, and regulatory guidance using Amazon Bedrock, Transcribe, Polly, and other AWS services.

## Features

- 🎙️ **Voice-Enabled GRC**: Real-time speech-to-text and text-to-speech for audit interviews and compliance discussions
- 🤖 **Specialized GRC Agents**: 4 expert agents tailored for Governance, Risk, and Compliance use cases
- 🧠 **Intelligent Orchestration**: Automatic agent selection using agent-squad framework based on GRC context
- 💼 **GRC Personalities**: Agents optimized for different GRC scenarios (interviewer, compliance authority, risk expert, governance strategist)
- ☁️ **AWS Native**: Built for AWS cloud with Bedrock, Transcribe, Polly, and Lex integration
- 🔄 **WebRTC Support**: Real-time audio streaming for compliance interviews (planned)
- 💾 **Audit Trail**: Bedrock built-in conversation memory for compliance documentation
- 📊 **GRC Monitoring**: CloudWatch integration for audit logging and compliance metrics
- 🐳 **Enterprise Ready**: Docker support for secure enterprise deployment
- 🚀 **Infrastructure as Code**: AWS CDK for compliant infrastructure management
- 🌐 **Compliance Dashboard**: Web interface for GRC agent management and audit documentation
- **File-based Agent Configuration** for easy customization and deployment
- **Bedrock Built-in Memory** for seamless conversation continuity
- **Real-time WebRTC** for browser-based voice interactions
- **Tool Registry Integration** for extensible functionality

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │────│  Load Balancer   │────│   ECS Fargate   │
│   (WebRTC)      │    │      (ALB)       │    │   Containers    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 │                                 │
                ┌─────────────┐                   ┌─────────────┐                 ┌─────────────┐
                │   Amazon    │                   │   Amazon    │                 │   Amazon    │
                │ Transcribe  │                   │   Bedrock   │                 │    Polly    │
                └─────────────┘                   │ (Built-in   │                 └─────────────┘
                       │                          │  Memory)    │                         │
                ┌─────────────┐                   └─────────────┘                 ┌─────────────┐
                │   Amazon    │                                                   │ CloudWatch  │
                │     Lex     │                                                   │    Logs     │
                └─────────────┘                                                   └─────────────┘
```

## Prerequisites

- Python 3.13.2 (installed via pyenv)
- Docker and Docker Compose
- AWS CLI v2
- aws-vault (for secure credential management)
- Node.js (for AWS CDK)
- Make

## Current Status

✅ **Working Features:**
- Complete agent swarm with 4 personality-based agents
- Intelligent agent selection based on request analysis
- REST API with chat functionality
- Modern web interface
- Bedrock built-in memory for conversation persistence
- Docker containerization
- AWS CDK infrastructure code

🚧 **In Development:**
- Voice processing integration with AWS Transcribe/Polly
- WebRTC real-time audio streaming
- Advanced conversation memory features

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd grc-agent-squad

# Create and activate virtual environment
make install

# Copy environment file and configure
cp env.example .env
# Edit .env with your AWS settings
```

### 2. Virtual Environment

This project uses a Python virtual environment stored in the `venv` directory. Here's how to work with it:

```bash
# Create or update the virtual environment
make venv

# Activate the virtual environment (direct method)
source venv/bin/activate

# Alternative: use the activation script
source activate.sh

# Check virtual environment status
make venv-status

# Deactivate the virtual environment when done
deactivate
```

> **VS Code Setup**: The project is configured to automatically use the virtual environment in VS Code. The Python interpreter path is set to `${workspaceFolder}/venv/bin/python` in `.vscode/settings.json`.

### 3. Local Development

```bash
# Start local development environment
make local-start

# The API will be available at http://localhost:8001
# Web interface at http://localhost:8001/
# API documentation at http://localhost:8001/docs
```

### 3. AWS Deployment

```bash
# Configure AWS credentials using aws-vault
aws-vault add acl-playground

# Deploy infrastructure
make cdk-deploy

# Build and push container image
make build push

# Update ECS service
make deploy
```

## Project Structure

```
grc-agent-squad/
├── src/                    # Application source code
│   ├── agents/            # Agent implementations
│   ├── api/               # FastAPI application
│   ├── services/          # AWS service integrations
│   ├── models/            # Data models
│   └── utils/             # Utility functions
├── infrastructure/        # AWS CDK infrastructure code
├── tests/                 # Test suites
├── docs/                  # Documentation
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Local development setup
├── Makefile              # Build and deployment commands
└── requirements.txt       # Python dependencies
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration

# Run with coverage
make test-coverage
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
make type-check
```

### Local Development with Docker

```bash
# Build and start services
docker-compose up --build

# View logs
docker-compose logs -f voice-agent-app

# Stop services
docker-compose down
```

## API Endpoints

### Health Check
- `GET /health/` - Basic health check

### Agent Management
- `GET /api/agents/` - List all available agents with details
- `GET /api/agents/{agent_id}` - Get specific agent information
- `POST /api/agents/chat` - Chat with agents (intelligent agent selection)
- `GET /api/agents/personalities/presets` - Get available personality presets
- `GET /api/agents/capabilities/list` - Get available agent capabilities
- `GET /api/agents/config/details` - Get detailed agent configurations
- `GET /api/agents/grc/agent-types` - Get GRC agent type information

### Available GRC Agents
The system includes 4 specialized executive-level GRC agents with distinct expertise:

1. **Emma - Senior Information Collector** (`empathetic_interviewer_executive`)
   - Executive-level empathetic interviewer
   - Advanced expertise in C-suite and board member interviews
   - **Specializes in**: Executive compliance interviews, board-level risk assessment sessions, senior stakeholder consultations
   - **Voice**: Joanna (formal, warm approach)

2. **Dr. Morgan - Chief Compliance Officer** (`authoritative_compliance_executive`) 
   - Executive-level compliance authority with deep regulatory knowledge
   - Provides definitive compliance guidance for complex regulatory environments
   - **Specializes in**: Executive regulatory interpretation, board compliance reporting, strategic regulatory guidance
   - **Voice**: Matthew (authoritative, low pitch)

3. **Alex - Chief Risk Officer** (`analytical_risk_expert_executive`)
   - Executive-level risk analysis expert specializing in strategic risk assessment
   - Enterprise risk management and data-driven insights for senior leadership
   - **Specializes in**: Executive risk modeling, board risk committee reporting, strategic risk planning
   - **Voice**: Amy (analytical, medium pitch)

4. **Sam - Chief Governance Officer** (`strategic_governance_executive`)
   - Executive-level governance strategist specializing in board effectiveness
   - Corporate governance frameworks and strategic governance advisory
   - **Specializes in**: Board effectiveness assessments, governance framework design, executive governance advisory
   - **Voice**: Brian (consultative, diplomatic approach)

### Voice Processing (Planned)
- `POST /api/voice/transcribe` - Transcribe audio to text
- `POST /api/voice/synthesize` - Text-to-speech synthesis
- `WS /api/voice/stream` - WebSocket for real-time voice streaming

## Usage Examples

### Chat with Agents

The system automatically selects the most appropriate GRC agent based on your request:

```bash
# Compliance query → Dr. Morgan (Compliance Authority)
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the GDPR requirements for data retention?", "session_id": "compliance-session"}'

# Risk assessment → Alex (Risk Expert)  
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do we assess cybersecurity risks in our cloud infrastructure?", "session_id": "risk-session"}'

# Interview preparation → Emma (Information Collector)
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to interview our CFO about financial controls. Can you help?", "session_id": "interview-session"}'

# Governance strategy → Sam (Governance Strategist)
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How should we restructure our board committees for better oversight?", "session_id": "governance-session"}'
```

### Dynamic Agent Switching in Single Conversation

```bash
# Session demonstrating agent switching within one conversation
SESSION_ID="multi-agent-demo"

# First request → Compliance
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What SOX controls do we need for financial reporting?\", \"session_id\": \"$SESSION_ID\"}"

# Follow-up → Risk Expert  
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What are the risks if those controls fail?\", \"session_id\": \"$SESSION_ID\"}"

# Follow-up → Information Collector
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"How should I test these controls with the finance team?\", \"session_id\": \"$SESSION_ID\"}"

# Follow-up → Governance Strategist
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What governance structure should oversee this testing?\", \"session_id\": \"$SESSION_ID\"}"
```

### List Available Agents

```bash
curl "http://localhost:8001/api/agents/" | jq .
```

### Get Agent Details

```bash
curl "http://localhost:8001/api/agents/{agent-id}" | jq .
```

## 🧠 Intelligent Agent Orchestration

The GRC Agent Squad uses the **AWS Labs agent-squad framework** for intelligent agent selection and dynamic switching during conversations.

### How Agent Selection Works

#### 1. **Classifier-Based Routing**
Each request is processed through a **BedrockClassifier** that analyzes:
- **Content analysis** - Understanding the context and topic
- **GRC expertise matching** - Matching to specialized agent capabilities  
- **Agent descriptions** - Using agent personas and specializations
- **Confidence scoring** - Providing selection confidence levels

#### 2. **Dynamic Agent Switching**
**Agents can switch mid-conversation** based on the evolving context:

```bash
# Example conversation flow:
User: "What GDPR training do we need?"
→ 🎯 Dr. Morgan (Compliance Authority) selected
Dr. Morgan: "Under GDPR Article 39, you need comprehensive data protection training..."

User: "How do we assess the risk of data breaches?"  
→ 🎯 Alex (Risk Expert) selected
Alex: "Let me analyze the risk factors. First, we assess likelihood and impact..."

User: "Can you interview our IT director about these controls?"
→ 🎯 Emma (Information Collector) selected  
Emma: "I'd be happy to help structure that interview. Let's prepare some questions..."

User: "What governance structure should oversee this?"
→ 🎯 Sam (Governance Strategist) selected
Sam: "For effective oversight, I recommend establishing a data governance committee..."
```

#### 3. **GRC-Specific Selection Criteria**

The system analyzes requests for GRC-specific indicators:

**Emma (Information Collector)**:
- Interview keywords: "interview", "gather", "collect", "ask questions"
- Empathy indicators: "help me understand", "walk through", "explain step by step"
- Consultation terms: "stakeholder", "team member", "discussion"

**Dr. Morgan (Compliance Authority)**:
- Regulatory terms: "GDPR", "SOX", "HIPAA", "compliance", "regulation"
- Authority indicators: "required", "mandatory", "legal", "violation"
- Formal requests: "policy", "documentation", "official guidance"

**Alex (Risk Expert)**:
- Risk terms: "risk", "threat", "vulnerability", "assessment", "impact"
- Analysis indicators: "analyze", "evaluate", "measure", "quantify"
- Mitigation language: "control", "prevent", "reduce", "manage"

**Sam (Governance Strategist)**:
- Governance terms: "board", "committee", "framework", "structure"
- Strategic language: "strategy", "planning", "oversight", "governance"
- Policy terms: "policy development", "best practices", "standards"

#### 4. **Conversation Continuity**

**Memory Preservation Across Agent Switches:**
- Each agent uses **Bedrock's built-in memory** (`save_chat=True`)
- **Session ID tracking** maintains conversation context
- **Agent metadata** tracks which agent handled each response
- **Seamless handoffs** preserve conversation flow

#### 5. **Response Structure**

Every response includes detailed orchestration metadata:

```json
{
  "success": true,
  "agent_selection": {
    "agent_id": "authoritative_compliance",
    "agent_name": "Dr. Morgan - Chief Compliance Officer", 
    "confidence": 0.92,
    "reasoning": "Selected by agent-squad orchestration with Bedrock memory"
  },
  "agent_response": {
    "response": "According to GDPR Article 32, you must implement..."
  },
  "session_id": "conversation-123"
}
```

#### 6. **Fallback Strategy**

- **Default Agent**: Emma (Information Collector) serves as fallback
- **Low Confidence**: If no agent scores >70% confidence, defaults to Emma
- **Error Handling**: Graceful degradation maintains conversation flow

This orchestration creates a **seamless multi-expert experience** where users get the most qualified GRC specialist for each question while maintaining full conversation continuity!

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_PROFILE` | AWS profile name | `acl-playground` |
| `AWS_REGION` | AWS region | `us-west-2` |
| `BEDROCK_MODEL_ID` | Bedrock model identifier | `anthropic.claude-3-haiku-20240307-v1:0` |
| `TRANSCRIBE_LANGUAGE_CODE` | Language for transcription | `en-US` |
| `POLLY_VOICE_ID` | Polly voice identifier | `Joanna` |
| `API_PORT` | API server port | `8001` |

### AWS Services Configuration

The application requires the following AWS services:
- **Bedrock**: For LLM capabilities
- **Transcribe**: For speech-to-text
- **Polly**: For text-to-speech
- **Lex**: For dialog management (optional)
- **ECS**: For container orchestration
- **ECR**: For container registry
- **ALB**: For load balancing
- **CloudWatch**: For logging and monitoring

## Deployment

### AWS CDK Infrastructure

```bash
# Bootstrap CDK (first time only)
aws-vault exec acl-playground -- cdk bootstrap

# Deploy infrastructure
aws-vault exec acl-playground -- cdk deploy

# View deployed resources
aws-vault exec acl-playground -- cdk list
```

### Container Deployment

```bash
# Build container image
make docker-build

# Push to ECR
make docker-push

# Update ECS service
make deploy
```

## Monitoring

### CloudWatch Logs

Logs are automatically sent to CloudWatch Log Groups:
- `/aws/ecs/grc-agent-squad` - Application logs
- `/aws/apigateway/grc-agent-squad` - API Gateway logs

### Metrics

Key metrics to monitor:
- Request latency
- Error rates
- Active WebSocket connections
- AWS service API calls
- Container resource usage

## Troubleshooting

### Common Issues

1. **Agent Selection Issues**
   - Verify agents are initialized: `curl http://localhost:8001/api/agents/`
   - Check agent orchestrator logs for selection reasoning
   - Ensure proper personality presets are loaded

2. **API Response Errors**
   - Datetime validation errors: Check `created_at` field formatting
   - Agent not found: Verify agent IDs are current (they regenerate on restart)
   - 500 errors: Check server logs for detailed error information

3. **AWS Service Errors** (Future)
   - Verify IAM permissions for Bedrock, Transcribe, Polly
   - Check service quotas and region availability
   - Validate AWS credentials and region configuration

4. **Container Issues**
   - Check ECS task logs for startup errors
   - Verify environment variables are properly set
   - Ensure health checks are responding correctly

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with detailed logs
make local-start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 