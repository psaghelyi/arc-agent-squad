# Voice Agent Swarm

A voice-enabled AI agent swarm using AWS services and the agent-squad framework. This project demonstrates how to build scalable, cloud-native voice AI applications with intelligent agent selection, personality-based responses, and real-time voice processing using Amazon Bedrock, Transcribe, Polly, and other AWS services.

## Features

- 🎙️ **Voice Processing**: Real-time speech-to-text and text-to-speech with Amazon Transcribe and Polly
- 🤖 **Intelligent Agent Swarm**: 4 specialized agents with distinct personalities using agent-squad framework
- 🧠 **Smart Agent Selection**: Automatic agent selection based on request analysis and personality matching
- 💬 **Personality-Based Responses**: Agents with different communication styles (helpful, direct, professional, casual)
- ☁️ **AWS Native**: Built for AWS cloud with Bedrock, Transcribe, Polly, and Lex integration
- 🔄 **WebRTC Support**: Real-time audio streaming capabilities (planned)
- 💾 **Memory Management**: Redis-based conversation memory with graceful fallback
- 📊 **Monitoring**: CloudWatch integration for logging and metrics
- 🐳 **Containerized**: Docker support for easy deployment
- 🚀 **Infrastructure as Code**: AWS CDK for infrastructure management
- 🌐 **Modern Web UI**: Beautiful, responsive web interface for agent management

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
                └─────────────┘                   └─────────────┘                 └─────────────┘
                       │                                 │                                 │
                ┌─────────────┐                   ┌─────────────┐                 ┌─────────────┐
                │   Amazon    │                   │    Redis    │                 │ CloudWatch  │
                │     Lex     │                   │  (Memory)   │                 │    Logs     │
                └─────────────┘                   └─────────────┘                 └─────────────┘
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
- Memory management with Redis fallback
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
cd voice-agent-swarm

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
voice-agent-swarm/
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

### Available Agents
The system includes 4 pre-configured agents with distinct personalities:

1. **Emma the Helper** (`kind_helpful`)
   - Empathetic and supportive
   - Provides detailed explanations
   - Best for: General help, emotional support, learning

2. **Alex the Direct** (`to_the_point`) 
   - Brief and straightforward
   - Quick, concise answers
   - Best for: Urgent requests, simple questions

3. **Dr. Morgan** (`professional`)
   - Professional and technical
   - Formal communication style
   - Best for: Technical queries, business contexts

4. **Sam the Buddy** (`casual_friendly`)
   - Casual and creative
   - Friendly, conversational tone
   - Best for: Creative tasks, casual conversations

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
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
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
- `/aws/ecs/voice-agent-swarm` - Application logs
- `/aws/apigateway/voice-agent-swarm` - API Gateway logs

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

2. **Memory Service Issues**
   - Redis connection failures are handled gracefully with fallback
   - Check Redis connectivity if persistent memory is needed
   - Verify memory service logs for connection status

3. **API Response Errors**
   - Datetime validation errors: Check `created_at` field formatting
   - Agent not found: Verify agent IDs are current (they regenerate on restart)
   - 500 errors: Check server logs for detailed error information

4. **AWS Service Errors** (Future)
   - Verify IAM permissions for Bedrock, Transcribe, Polly
   - Check service quotas and region availability
   - Validate AWS credentials and region configuration

5. **Container Issues**
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
- Implemented proper Redis connection handling with graceful fallback
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