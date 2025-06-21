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

### 2. Local Development

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

### Available GRC Agents
The system includes 4 specialized GRC agents with distinct expertise:

1. **Emma - Information Collector** (`empathetic_interviewer`)
   - Empathetic and patient interviewer
   - Skilled at gathering detailed compliance information
   - Best for: Audit interviews, stakeholder consultations, requirement gathering

2. **Dr. Morgan - Compliance Authority** (`authoritative_compliance`) 
   - Official and regulation-focused
   - Provides definitive compliance guidance
   - Best for: Regulatory interpretation, compliance reporting, formal documentation

3. **Alex - Risk Analysis Expert** (`analytical_risk_expert`)
   - Analytical and detail-oriented
   - Systematic approach to risk assessment
   - Best for: Risk modeling, control gap analysis, threat assessment

4. **Sam - Governance Strategist** (`strategic_governance`)
   - Strategic and consultative
   - Big-picture governance thinking
   - Best for: Governance framework design, policy development, board reporting

### Voice Processing (Planned)
- `POST /api/voice/transcribe` - Transcribe audio to text
- `POST /api/voice/synthesize` - Text-to-speech synthesis
- `WS /api/voice/stream` - WebSocket for real-time voice streaming

## Usage Examples

### Chat with Agents

The system automatically selects the most appropriate agent based on your request:

```bash
# Empathetic request → Emma the Helper
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me with something?", "session_id": "session-1"}'

# Brief/urgent request → Alex the Direct
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need a quick answer. What is 2+2?", "session_id": "session-2"}'

# Technical request → Dr. Morgan
curl -X POST "http://localhost:8001/api/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Can you explain the technical architecture?", "session_id": "session-3"}'
```

### List Available Agents

```bash
curl "http://localhost:8001/api/agents/" | jq .
```

### Get Agent Details

```bash
curl "http://localhost:8001/api/agents/{agent-id}" | jq .
```

### Agent Selection Logic

The system analyzes requests for:
- **Urgency indicators**: "quick", "fast", "urgent", "asap"
- **Emotional content**: "help", "please", "frustrated", "confused"
- **Technical terms**: "code", "api", "technical", "debug", "error"
- **Creative requests**: "write", "create", "story", "poem"
- **Empathy needs**: "sad", "upset", "worried", "anxious"
- **Brevity preferences**: "brief", "short", "summary"

Each agent is scored based on personality matching, and the best fit is selected with confidence scoring and reasoning.

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

## Recent Improvements

### v1.1.0 - Agent System Fixes & Enhancements

✅ **Major Fixes:**
- Fixed agent-squad library integration and Agent class initialization
- Resolved datetime validation errors in API responses
- Implemented proper Bedrock built-in memory for conversation persistence
- Fixed agent orchestrator to properly call agent-squad compatible methods
- Added comprehensive error handling and logging

✅ **New Features:**
- Intelligent agent selection with confidence scoring and reasoning
- 4 distinct personality-based agents with specialized capabilities
- Modern, responsive web interface
- Comprehensive API endpoints for agent management
- Memory management with conversation history support

✅ **Performance Improvements:**
- Optimized agent selection algorithm
- Improved error handling and recovery
- Enhanced logging and debugging capabilities
- Better concurrent request handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Create an issue in the repository
- Check the documentation in the `docs/` directory
- Review AWS service documentation 

# ARC Agents - GRC Agent Squad

An AI agent squad designed for Governance, Risk Management, and Compliance (GRC) industry applications.

## Quick Start

### Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate credentials
- Docker and Docker Compose (for containerized deployment)

### MCP Configuration Setup

The project uses Model Context Protocol (MCP) for AI tool integration. To set up your MCP configuration:

1. **Copy the template file:**
   ```bash
   cp .cursor/mcp.json.template .cursor/mcp.json
   ```

2. **Add your API keys to `.cursor/mcp.json`:**
   Replace the placeholder values with your actual API keys:
   - `PERPLEXITY_API_KEY` - For research capabilities
   - `OPENAI_API_KEY` - For OpenAI models
   - `GOOGLE_API_KEY` - For Google/Gemini models
   - `XAI_API_KEY` - For xAI models
   - `OPENROUTER_API_KEY` - For OpenRouter models
   - `MISTRAL_API_KEY` - For Mistral models
   - `AZURE_OPENAI_API_KEY` - For Azure OpenAI
   - `OLLAMA_API_KEY` - For local Ollama instance

3. **Security Note:** 
   - The `.cursor/mcp.json` file is git-ignored to prevent API keys from being committed
   - Never commit actual API keys to version control
   - Only add the API keys you plan to use

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd arc-agents

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
```

### Development

```bash
# Run locally
make local-start

# Run tests
make test

# Build Docker image
make build
```

### Deployment

```bash
# Deploy infrastructure and application
make deploy
```

## Architecture

The system consists of four specialized GRC agents:

- **Emma (Information Collector)** - Empathetic interviewer for audit interviews and information gathering
- **Dr. Morgan (Compliance Authority)** - Official, formal compliance guidance and regulatory interpretation
- **Alex (Risk Expert)** - Analytical risk assessment and mitigation strategies
- **Sam (Governance Strategist)** - Strategic governance framework guidance and recommendations

The agents are orchestrated using the [AWS Labs agent-squad](https://github.com/awslabs/agent-squad) framework, which automatically routes requests to the most appropriate agent based on the content and context.

## Voice Capabilities

The system supports real-time voice interactions using:
- Amazon Transcribe for speech-to-text
- Amazon Polly Neural TTS for text-to-speech
- WebRTC for browser-based audio streaming

## Contributing

Please read our contributing guidelines and ensure all tests pass before submitting pull requests.

## License

[License information] 