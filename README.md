# Apex Pentest X

**AI-Powered Automated Web Application Penetration Testing Platform**

## Overview

Apex Pentest X is an advanced, fully automated web application penetration testing platform powered by multi-agent AI, Playwright-based browser execution, orchestrated job pipelines, automated fuzzing, payload mutation, and multi-agent validation (debate-based).

This platform automatically executes WSTG-aligned tests, finds vulnerabilities, validates them, produces proof-of-concept evidence, and generates detailed reports.

## Architecture

- **Multi-tenant SaaS architecture** with per-project isolation
- **Multi-agent AI system** with specialized agents for different testing phases
- **Real-time dashboards** with WebSocket-based updates
- **Automated scan planning** and intelligent test case selection
- **Zero-trust security** with comprehensive audit logging
- **Scalable infrastructure** with Kubernetes orchestration

## Tech Stack

- **Backend:** Python (FastAPI)
- **Frontend:** Next.js
- **Database:** PostgreSQL
- **Queue:** Redis + Celery
- **Browser Engine:** Playwright
- **Storage:** S3-compatible (MinIO/AWS S3)
- **Vector Memory:** ChromaDB
- **Deployment:** Docker + Kubernetes
- **AI Runtime:** Gemini 2.5 Pro API

## Services

### Core Services
- **Gateway:** JWT auth, routing, rate limiting
- **Orchestrator:** Test plan generation, job scheduling, state management
- **Agent Runner:** Container management for agent execution

### AI Agents
- **Recon Agent:** Crawling, fingerprinting, parameter discovery
- **Session Agent:** Login workflows, CSRF/token extraction
- **Auth Agent:** Authentication testing
- **Fuzz Agent:** Mutation engine, response analysis
- **Exploit Agent:** Controlled exploitation, PoC generation
- **Validator Agent:** Multi-agent validation, cross-attestation
- **Learning Agent:** Pattern clustering, optimization
- **Reporter Agent:** PDF/HTML report generation

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Kubernetes (for production)

### Development Setup

```bash
# Start infrastructure services
cd infra/docker
docker-compose up -d

# Start backend services
cd services/orchestrator
poetry install
poetry run uvicorn app.main:app --reload

# Start frontend
cd ui/web
npm install
npm run dev
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Specification](docs/api-spec.md)
- [Data Model](docs/data-model.md)
- [Runbook](docs/runbook.md)

## Security

This platform implements:
- KMS-based encryption for all secrets
- Zero-trust service communication
- Seccomp profiles for container isolation
- Comprehensive audit logging
- Rate limiting per project

## License

Proprietary - All Rights Reserved

## Contact

For support and inquiries, please contact the development team.
