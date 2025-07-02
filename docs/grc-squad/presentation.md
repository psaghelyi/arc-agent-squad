---
title: "GRC Agent Squad"
author: "Diligent"
theme: "diligent"
---

# GRC Agent Squad
## Intelligent Voice-Enabled AI Specialists<br>for Governance, Risk & Compliance

---

# Our Solution: Create Your own GRC Squad

An **agentic framework** that simulates how organizations manage complex GRC tasks through intelligent delegation:
- **Layered Architecture**: Supervisor agent orchestrates complex multi-step operations by delegating to specialist agents
- **Intelligent Task Delegation**: Classifier analyzes requests and breaks them into subtasks for appropriate expert agents
- **Agentic Tool Ecosystem**: Agents can call APIs, Lambda functions, MCP clients, and even other agents as tools
- **Autonomous Agent Tools**: Each agent is both a specialist and a tool that can be used by other agents
- **Modular Agent Construction**: Agents can be constructed from a set of tools, use cases and capabilities

---

# GRC Squad Configurations for Different Company Sizes

- **Small Companies**: 1-2 agents with versatile use cases
- **Medium Companies**: 5-6 agents with orchestration and complex use cases
- **Large Companies**: 10+ agents with layered structure, multilevel delegation

```mermaid
graph TD
    %% Small Company Configuration
    subgraph "Small Company"
        EU1[End User] --> A1[Single GRC Agent]
    end
    
    %% Medium Company Configuration
    subgraph "Medium Company"
        EU2[End User] --> D1[Director]
        D1 --> A2_1[Agent 1]
        D1 --> A2_2[Agent 2]
        D1 --> A2_3[Agent 3]
        D1 --> A2_4[Agent 4]
    end
    
    %% Large Company Configuration
    subgraph "Large Company"
        EU3[End User] --> VP[VP of GRC]
        VP --> D2_1[Director 1]
        VP --> D2_2[Director 2]
        
        D2_1 --> A3_1[Agent 1]
        D2_1 --> A3_2[Agent 2]
        D2_1 --> A3_3[Agent 3]
        
        D2_2 --> A3_4[Agent 4]
        D2_2 --> A3_5[Agent 5]
        D2_2 --> A3_6[Agent 6]
    end
    
    %% Styling
    classDef user fill:#f9f9f9,stroke:#333,stroke-width:1px
    classDef director fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff
    classDef vp fill:#ff9e64,stroke:#333,stroke-width:2px,color:#fff
    classDef agent fill:#c7d2fe,stroke:#333,stroke-width:1px
    
    class EU1,EU2,EU3 user
    class D1,D2_1,D2_2 director
    class VP vp
    class A1,A2_1,A2_2,A2_3,A2_4,A3_1,A3_2,A3_3,A3_4,A3_5,A3_6 agent
```

---

# Meet The Squad

**🎯 SupervisorAgent**: Hybrid team leader that coordinates complex cases by orchestrating parallel communication between specialist agents

**🔄 Confidence-Based Routing**: High confidence requests go directly to experts, low confidence/complex requests use supervisor coordination

- **Emma**: Information Collector - Empathetic interviewer conducting audit interviews, stakeholder consultations, and compliance information gathering
- **Dr. Morgan**: Compliance Authority - Official compliance agent providing definitive regulatory guidance and formal documentation
- **Alex**: Risk Analysis Expert - Analytical specialist in risk assessment, analysis, and mitigation strategies
- **Sam**: Governance Strategist - Strategic specialist focused on governance frameworks, policy development, and board-level guidance
- **Jordan**: Audit Expert - Internal audit specialist *(In Development - Not Yet Implemented)*

---

# Key Capabilities

- **Hybrid Routing**: Confidence threshold (0.8) determines direct expert access vs supervisor coordination
- **Parallel Coordination**: SupervisorAgent can communicate with multiple team members simultaneously
- **RAG-Enhanced Intelligence**: Amazon Knowledge Base Retriever with RAFT fine-tuning capability
- **Multi-Modal Interaction**: Rich text chat, voice synthesis (Polly NTTS), and real-time voice (Lex V2)
- **Tool Ecosystem**: MCP clients, API calls, Lambda functions, and external service integrations
- **Context Continuity**: Bedrock built-in memory maintains complex workflow state across interactions

---

# Use Cases: Complex Orchestration

**Multi-Step Risk Assessment Workflow** (Low Confidence → Supervisor):
1. User: "Assess our cloud migration risks and create a mitigation plan"
2. Classifier confidence < 0.8 → Routes to SupervisorAgent
3. Supervisor coordinates: Emma interviews stakeholders || Alex analyzes risks || Morgan reviews compliance || Sam designs governance
4. Supervisor synthesizes responses into comprehensive plan

**Parallel Team Coordination**:
- SupervisorAgent uses `send_messages` tool for simultaneous agent communication
- Team members work independently while supervisor maintains coordination
- RAG provides domain knowledge, tools provide external data and actions

---

# Use Cases: Simple Requests

**Direct Expert Routing (High Confidence ≥ 0.8)**:
- **"What are GDPR data retention requirements?"** → Direct to Dr. Morgan (Compliance)
- **"Schedule an interview with our CISO"** → Direct to Emma (Information Collector) 
- **"What's our current risk exposure?"** → Direct to Alex (Risk Expert)
- **"Review board committee structure"** → Direct to Sam (Governance)
- **"Conduct SOC 2 internal audit"** → Direct to Jordan (Audit Expert)

**Tool Integration Examples**:
- Emma uses Lex V2 for real-time voice interviews
- Alex calls risk assessment APIs and Lambda functions
- Morgan queries regulatory databases via MCP clients
- Sam analyzes governance documents using RAG retrieval
- Jordan executes audit procedures and compliance testing

---

# Hybrid Tool Ecosystem

**SupervisorAgent Communication**:
- `send_messages` tool enables parallel agent coordination
- SupervisorAgent orchestrates complex multi-agent workflows
- Dynamic routing based on confidence thresholds

**External Tool Integration**:
- **MCP Clients**: File operations, database queries, document analysis
- **API Calls**: Regulatory databases, compliance systems, GRC platforms  
- **Lambda Functions**: Custom business logic, data processing, integrations
- **Lex V2**: Real-time voice interactions for interviews

**Context Enhancement**:
- **RAG (Knowledge Base)**: Domain-specific GRC knowledge with RAFT fine-tuning
- **Bedrock Memory**: Built-in session memory for conversation continuity
- **System Prompts**: Agent personality and capability definitions

---

# Voice & Interaction Capabilities

**Current Implementation**:
- **Voice Synthesis**: Amazon Polly Neural TTS for agent responses
- **Text-Based Chat**: Primary interaction with rich markdown support
- **Conversation Memory**: Bedrock built-in memory for session continuity

**Advanced Voice Features** (In Development):
- **Real-Time Voice Interviews**: Emma agent with Lex V2 integration
- **Bidirectional Voice**: Full speech-to-text and text-to-speech pipeline
- **Voice-Guided Workflows**: SupervisorAgent-led voice orchestration

**Multi-Modal Experience**:
- Text, voice, and hybrid interactions based on use case
- Agent-specific voice and response styles
- Context-aware interaction mode selection

---

# Architecture

```mermaid
graph TD
    Client["Web Client<br/>(Chat Interface)"] --> ALB["Load Balancer<br/>(ALB)"]
    ALB --> ECSF["ECS Fargate<br/>Containers"]
    
    subgraph "Hybrid Routing Framework"
        ECSF --> FastAPI["FastAPI<br/>Application"]
        FastAPI --> Router{{"Confidence-Based<br/>Router"}}
        
        Router -->|"confidence ≥ 0.8"| Classifier["BedrockClassifier<br/>(Direct Expert Routing)"]
        Router -->|"confidence < 0.8"| Supervisor["SupervisorAgent<br/>(Team Coordination)"]
        
        %% Direct Expert Routing
        Classifier -->|"High Confidence"| Emma["Emma<br/>(Information Collector)"]
        Classifier -->|"High Confidence"| Morgan["Dr. Morgan<br/>(Compliance Authority)"]
        Classifier -->|"High Confidence"| Alex["Alex<br/>(Risk Expert)"]
        Classifier -->|"High Confidence"| Sam["Sam<br/>(Governance Strategist)"]
        Classifier -->|"High Confidence"| Jordan["Jordan<br/>(Audit Expert)"]
        
        %% Supervisor Coordination
        Supervisor -->|"Team Leader"| SupervisorGRC["Supervisor GRC<br/>(Lead Agent)"]
        Supervisor -->|"Coordinates Team"| Emma
        Supervisor -->|"Coordinates Team"| Morgan
        Supervisor -->|"Coordinates Team"| Alex
        Supervisor -->|"Coordinates Team"| Sam
        Supervisor -->|"Coordinates Team"| Jordan
        
        %% Agent-to-Agent Communication via Supervisor
        SupervisorGRC -.->|"send_messages tool"| Emma
        SupervisorGRC -.->|"send_messages tool"| Morgan
        SupervisorGRC -.->|"send_messages tool"| Alex
        SupervisorGRC -.->|"send_messages tool"| Sam
        SupervisorGRC -.->|"send_messages tool"| Jordan
    end
    
    subgraph "AI Services"
        Emma --> Bedrock["Amazon Bedrock<br/>(Claude Models)"]
        Morgan --> Bedrock
        Alex --> Bedrock
        Sam --> Bedrock
        Jordan --> Bedrock
        SupervisorGRC --> Bedrock
        
        Emma --> LexV2["Amazon Lex V2<br/>(Real-time Voice)"]
        SupervisorGRC --> Polly["Amazon Polly<br/>(Voice Synthesis)"]
    end
    
    subgraph "Knowledge & Memory"
        Bedrock --> KnowledgeBase["Amazon Knowledge Base<br/>(RAG + RAFT)"]
        SupervisorGRC --> BedrockMemory["Bedrock Built-in<br/>(Session Memory)"]
        Emma --> BedrockMemory
        Morgan --> BedrockMemory
        Alex --> BedrockMemory
        Sam --> BedrockMemory
        Jordan --> BedrockMemory
    end
    
    subgraph "Agent Tools"
        Emma --> MCPClient["MCP Clients<br/>(File & DB Ops)"]
        Morgan --> RegulatoryAPIs["Regulatory APIs<br/>(Compliance Data)"]
        Alex --> Lambda["Lambda Functions<br/>(Risk Analysis)"]
        Sam --> ExternalAPIs["External APIs<br/>(Governance Tools)"]
        Jordan --> AuditTools["Audit Tools<br/>(Testing & Evidence)"]
    end
    
    subgraph "Infrastructure"
        ECSF --> CloudWatch["CloudWatch<br/>Logs & Metrics"]
        ALB --> WAF["AWS WAF<br/>Security"]
    end

    style Router fill:#ff6b6b,stroke:#333,stroke-width:3px,color:#fff
    style Supervisor fill:#ff9e64,stroke:#333,stroke-width:3px,color:#fff
    style SupervisorGRC fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff
    style Classifier fill:#4ecdc4,stroke:#333,stroke-width:2px,color:#fff
    style Emma fill:#c7d2fe,stroke:#333,stroke-width:1px
    style Morgan fill:#c7d2fe,stroke:#333,stroke-width:1px
    style Alex fill:#c7d2fe,stroke:#333,stroke-width:1px
    style Sam fill:#c7d2fe,stroke:#333,stroke-width:1px
    style Jordan fill:#c7d2fe,stroke:#333,stroke-width:1px
    style KnowledgeBase fill:#ffd93d,stroke:#333,stroke-width:2px
    style BedrockMemory fill:#6bcf7f,stroke:#333,stroke-width:2px
    style LexV2 fill:#ff8b94,stroke:#333,stroke-width:1px
```

- **Hybrid Framework**: Confidence-based routing between direct expert access and supervisor coordination
- **SupervisorAgent**: Team leader orchestrates complex cases with parallel agent communication
- **Tool Ecosystem**: Agents as tools, MCP clients, APIs, Lambda functions
- **RAG Architecture**: Knowledge Base Retriever with RAFT fine-tuning  
- **Built-in Memory**: Bedrock session memory for conversation continuity

---

# Development Roadmap

<div id="left">

**Phase 1: Hybrid Framework (Current PoC)** ✓
- SupervisorAgent-led orchestration with confidence-based routing
- Parallel agent communication and tool integration
- Basic voice synthesis (Polly NTTS)
- Bedrock built-in memory for session management

**Phase 2: Enhanced Tool Ecosystem** 🚧
- RAG implementation with Amazon Knowledge Base Retriever
- RAFT fine-tuning capabilities for domain-specific knowledge
- Expanded MCP client integrations and external API tools
- Lambda function integration for custom business logic

</div>

<div id="right">

**Phase 3: Advanced Voice & Real-Time Features** 📋
- Emma agent with full Lex V2 integration for voice interviews
- Bidirectional voice processing with Amazon Transcribe
- Real-time conversation flows and SupervisorAgent voice orchestration
- Multi-modal interaction coordination

**Future: Enterprise & Production** 🏢
- Production-scale deployment and monitoring
- Advanced agent collaboration patterns
- Custom agent development framework
- Enterprise integration and security hardening

</div>

---

# Summary

- **Hybrid Intelligence**: Confidence-based routing between direct expert access and supervisor coordination
- **Parallel Coordination**: SupervisorAgent orchestrates complex workflows with simultaneous team communication
- **Knowledge Enhancement**: RAG with RAFT fine-tuning provides continuously improving domain expertise
- **Tool Flexibility**: Extensible architecture supports MCP clients, APIs, Lambda functions, and custom integrations
- **Context Continuity**: Bedrock built-in memory maintains workflow state across complex multi-session operations
- **Adaptive Interaction**: Smart routing (≥0.8 confidence) between simple direct responses and complex orchestrated workflows

---

# 👍 Thank You 👍

