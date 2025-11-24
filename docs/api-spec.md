# Apex Pentest X - API Specification

## Base URL
```
Production: https://api.apex-pentest.com
Development: http://localhost:8080
```

## Authentication

All API requests (except `/api/auth/*`) require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /api/auth/signup
Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "user_123",
  "email": "user@example.com"
}
```

#### POST /api/auth/login
Authenticate and receive access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "user_123",
  "email": "user@example.com"
}
```

### Projects

#### GET /api/projects
List all projects for the authenticated user.

**Response:**
```json
[
  {
    "id": "proj_123",
    "name": "My Web App",
    "description": "Security assessment",
    "owner_id": "user_123",
    "settings": {},
    "status": "created",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /api/projects
Create a new project.

**Request Body:**
```json
{
  "name": "My Web App",
  "description": "Security assessment",
  "settings": {
    "rate_limit": 10,
    "concurrency": 5
  }
}
```

#### GET /api/projects/{project_id}
Get project details.

#### PATCH /api/projects/{project_id}
Update project.

**Request Body:**
```json
{
  "name": "Updated Name",
  "status": "scanning"
}
```

#### DELETE /api/projects/{project_id}
Delete a project.

### Targets

#### POST /api/targets
Add a target to a project.

**Request Body:**
```json
{
  "project_id": "proj_123",
  "type": "url",
  "value": "https://example.com",
  "scope_rules": {
    "include_subdomains": true,
    "exclude_paths": ["/admin"]
  }
}
```

#### GET /api/targets?project_id={project_id}
List targets for a project.

#### DELETE /api/targets/{target_id}
Remove a target.

### Scans

#### POST /api/scans/{project_id}/start
Start a security scan.

**Request Body:**
```json
{
  "test_cases": ["WSTG-INFO-01", "WSTG-INPV-01"],
  "config": {
    "depth": 3,
    "timeout": 300
  }
}
```

**Response:**
```json
{
  "message": "Scan started successfully",
  "project_id": "proj_123",
  "status": "queued"
}
```

#### GET /api/scans/{project_id}/jobs
List all jobs for a project.

**Response:**
```json
[
  {
    "id": "job_123",
    "project_id": "proj_123",
    "test_case_id": "tc_123",
    "agent_id": "recon-agent",
    "status": "running",
    "priority": 3,
    "retries": 0,
    "eta": "2024-01-01T00:05:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/scans/jobs/{job_id}
Get job details.

#### POST /api/scans/jobs/{job_id}/cancel
Cancel a running job.

### Findings

#### GET /api/findings?project_id={project_id}
List findings for a project.

**Response:**
```json
[
  {
    "id": "finding_123",
    "project_id": "proj_123",
    "title": "SQL Injection",
    "description": "SQL injection vulnerability detected...",
    "severity": "critical",
    "cvss_score": 9.8,
    "confidence": 0.95,
    "status": "validated",
    "affected_url": "https://example.com/login",
    "affected_parameter": "username",
    "created_at": "2024-01-01T00:00:00Z",
    "validated_at": "2024-01-01T00:10:00Z"
  }
]
```

#### GET /api/findings/{finding_id}
Get finding details.

#### POST /api/findings/{finding_id}/comment
Add a comment to a finding.

**Request Body:**
```json
{
  "comment": "This has been fixed in version 2.0"
}
```

#### POST /api/findings/{finding_id}/validate
Update finding status.

**Request Body:**
```json
{
  "status": "validated",
  "notes": "Confirmed through manual testing"
}
```

### Evidence

#### GET /api/evidence?finding_id={finding_id}
List evidence for a finding.

**Response:**
```json
[
  {
    "id": "evidence_123",
    "finding_id": "finding_123",
    "type": "screenshot",
    "filename": "exploit_proof.png",
    "size_bytes": 102400,
    "download_url": "https://storage.apex.com/...",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/evidence/{evidence_id}
Get evidence details and download URL.

### Agents

#### GET /api/agents
List all available agents.

**Response:**
```json
[
  {
    "id": "recon-agent-1",
    "name": "Recon Agent",
    "type": "recon",
    "status": "idle",
    "current_job": null,
    "last_heartbeat": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/agents/{agent_id}
Get agent details.

#### POST /api/agents/{agent_id}/restart
Restart an agent.

## WebSocket API

### /ws/projects/{project_id}/events
Real-time project events stream.

**Event Types:**
- `job_started`
- `job_completed`
- `finding_created`
- `scan_progress`

**Example Event:**
```json
{
  "type": "finding_created",
  "data": {
    "finding_id": "finding_123",
    "severity": "high",
    "title": "XSS Vulnerability"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Common Status Codes:**
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Rate Limiting

- Default: 60 requests per minute per user
- Configurable per project
- Headers included in response:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
