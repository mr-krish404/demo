# Apex Pentest X - Architecture Documentation

## System Overview

Apex Pentest X is a comprehensive, AI-powered automated web application penetration testing platform built on a microservices architecture with multi-agent AI coordination.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (Next.js / React)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTPS/WSS
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    API Gateway                               │
│              (FastAPI + JWT Auth)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼────────┐ ┌─▼──────────┐
│ Orchestrator │ │   Agent    │ │  Storage   │
│   Service    │ │   Runner   │ │  (MinIO)   │
└───────┬──────┘ └───┬────────┘ └────────────┘
        │            │
        │            │
┌───────▼────────────▼─────────────────────────────────────┐
│                    Agent Ecosystem                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Recon   │  │   Fuzz   │  │ Exploit  │  │Validator│ │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Session  │  │   Auth   │  │ Learning │  │Reporter │ │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└───────────────────────────────────────────────────────────┘
        │                    │
┌───────▼──────┐      ┌──────▼────────┐
│  PostgreSQL  │      │  Redis/Celery │
│   Database   │      │  Job Queue    │
└──────────────┘      └───────────────┘
```

## Core Components

### 1. API Gateway
- **Technology**: FastAPI
- **Responsibilities**:
  - JWT-based authentication
  - Request routing
  - Rate limiting
  - API versioning
- **Scaling**: Horizontal with load balancer

### 2. Orchestrator Service
- **Technology**: FastAPI + Celery
- **Responsibilities**:
  - Test plan generation
  - Job scheduling and prioritization
  - Scan coordination
  - State management
- **Key Features**:
  - WSTG-aligned test case selection
  - Intelligent prioritization
  - ETA calculation
  - Progress tracking

### 3. Agent Runner
- **Technology**: Python + Docker SDK
- **Responsibilities**:
  - Agent container lifecycle management
  - Resource isolation and limits
  - Timeout enforcement
  - Security constraints (seccomp, capabilities)

### 4. AI Agents

#### Recon Agent
- Web crawling with Playwright
- Technology fingerprinting
- Parameter discovery
- JavaScript analysis

#### Fuzz Agent
- Mutation engine for payload generation
- Response pattern analysis
- Anomaly detection
- Candidate vulnerability creation

#### Exploit Agent
- Controlled exploitation
- PoC generation
- Evidence capture (screenshots, HAR files)
- Playwright recording

#### Validator Agent
- Multi-agent reproduction
- Cross-attestation
- Confidence scoring
- False positive elimination

#### Session Agent
- Browser session management
- Login workflow automation
- CSRF/token extraction
- Cookie handling

#### Auth Agent
- Authentication testing
- Credential validation
- Session management testing

#### Learning Agent
- Pattern clustering with ChromaDB
- Historical analysis
- Payload optimization
- Test case suggestion

#### Reporter Agent
- PDF/HTML report generation
- WSTG mapping
- Evidence embedding
- Executive summaries

## Data Flow

### Scan Execution Flow

1. **User initiates scan** → Gateway validates request
2. **Gateway** → Orchestrator: Create scan job
3. **Orchestrator** generates test plan based on:
   - Target characteristics
   - Available credentials
   - Project settings
   - WSTG test cases
4. **Orchestrator** schedules jobs in priority queue (Celery/Redis)
5. **Celery workers** pick up jobs
6. **Agent Runner** spawns isolated containers for each agent
7. **Agents** execute tests and create findings
8. **Validator Agent** verifies findings through reproduction
9. **Findings** stored in PostgreSQL with evidence in MinIO
10. **WebSocket** pushes real-time updates to frontend
11. **Reporter Agent** generates final report

## Security Architecture

### Multi-Layer Security

1. **Network Layer**:
   - Zero-trust service communication
   - mTLS between services
   - Network policies in Kubernetes

2. **Container Layer**:
   - Seccomp profiles
   - Capability dropping
   - Read-only root filesystems
   - Resource limits

3. **Application Layer**:
   - JWT authentication
   - API rate limiting
   - Input validation
   - SQL injection prevention

4. **Data Layer**:
   - Encryption at rest (PostgreSQL)
   - Encryption in transit (TLS)
   - KMS for secret management
   - Credential encryption with Fernet

## Scalability

### Horizontal Scaling
- Gateway: 3-10 replicas (HPA)
- Orchestrator: 2-5 replicas
- Celery workers: Auto-scaling based on queue depth
- Agents: Ephemeral, spawned on-demand

### Vertical Scaling
- Database: Read replicas for reporting
- Redis: Cluster mode for high availability
- MinIO: Distributed mode for large evidence storage

## High Availability

- Multi-replica deployments
- Health checks and auto-restart
- Database backups (automated)
- Redis persistence (AOF + RDB)
- Load balancing across replicas

## Monitoring & Observability

- Prometheus metrics
- Grafana dashboards
- Structured logging (JSON)
- Distributed tracing (OpenTelemetry)
- Alert manager for critical issues

## Technology Stack Summary

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI |
| Frontend | React, TypeScript, Tailwind CSS |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7 |
| Storage | MinIO (S3-compatible) |
| Vector DB | ChromaDB |
| Container | Docker |
| Orchestration | Kubernetes |
| Browser Automation | Playwright |
| Task Queue | Celery |
| AI/LLM | Gemini 2.5 Pro |

## Deployment Models

### Development
- Docker Compose
- Single-node setup
- Local storage

### Production
- Kubernetes cluster
- Multi-node setup
- Distributed storage
- Auto-scaling enabled
- High availability

## Future Enhancements

1. **Advanced AI Features**:
   - GPT-4 integration for natural language findings
   - Automated remediation suggestions
   - Predictive vulnerability detection

2. **Extended Coverage**:
   - Mobile app testing
   - API-specific testing
   - Cloud infrastructure scanning

3. **Collaboration**:
   - Multi-user projects
   - Real-time collaboration
   - Team dashboards

4. **Integration**:
   - CI/CD pipeline integration
   - JIRA/GitHub issue creation
   - Slack/Teams notifications
