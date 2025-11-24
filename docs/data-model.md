# Apex Pentest X - Data Model

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Project   │──────<│   Target    │       │ Credential  │
│             │       │             │       │             │
│ - id        │       │ - id        │       │ - id        │
│ - name      │       │ - type      │       │ - type      │
│ - owner_id  │       │ - value     │       │ - encrypted │
│ - status    │       │ - scope     │       └─────────────┘
└──────┬──────┘       └─────────────┘              │
       │                                            │
       │                                            │
       │              ┌─────────────┐               │
       └─────────────>│     Job     │<──────────────┘
       │              │             │
       │              │ - id        │
       │              │ - agent_id  │
       │              │ - status    │
       │              │ - priority  │
       │              └──────┬──────┘
       │                     │
       │                     │
       │              ┌──────▼──────┐
       └─────────────>│   Finding   │
                      │             │
                      │ - id        │
                      │ - title     │
                      │ - severity  │
                      │ - confidence│
                      └──────┬──────┘
                             │
                    ┌────────┴────────┐
                    │                 │
             ┌──────▼──────┐   ┌─────▼─────┐
             │  Evidence   │   │   Vote    │
             │             │   │           │
             │ - id        │   │ - id      │
             │ - type      │   │ - agent_id│
             │ - storage   │   │ - vote    │
             └─────────────┘   └───────────┘
```

## Tables

### projects
Primary table for penetration testing projects.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(255) | Project name |
| owner_id | VARCHAR(255) | User ID of owner |
| description | TEXT | Project description |
| settings | JSONB | Project configuration |
| status | ENUM | created, scanning, paused, completed, failed |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (owner_id)
- INDEX (status)

### targets
Scan targets (URLs, IP ranges, domains).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Foreign key to projects |
| type | ENUM | url, ip_range, domain |
| value | VARCHAR(1024) | Target value |
| scope_rules | JSONB | Scope configuration |
| status | ENUM | pending, in_scope, out_of_scope |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (project_id) REFERENCES projects(id)
- INDEX (project_id)

### credentials
Authentication credentials for targets.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Foreign key to projects |
| target_id | UUID | Foreign key to targets (optional) |
| type | ENUM | basic, form, oauth, token, api_key |
| encrypted_payload | TEXT | Encrypted credential data |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (project_id) REFERENCES projects(id)
- FOREIGN KEY (target_id) REFERENCES targets(id)

### test_cases
WSTG test case definitions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| wstg_id | VARCHAR(50) | WSTG identifier (e.g., WSTG-INFO-01) |
| title | VARCHAR(255) | Test case title |
| description | TEXT | Test case description |
| category | VARCHAR(100) | Test category |
| automatable | BOOLEAN | Can be automated |
| assigned_agent | VARCHAR(100) | Agent responsible |
| priority | INTEGER | Priority level (1-5) |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (wstg_id)
- INDEX (category)
- INDEX (assigned_agent)

### jobs
Execution jobs for test cases.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Foreign key to projects |
| test_case_id | UUID | Foreign key to test_cases |
| agent_id | VARCHAR(100) | Agent identifier |
| status | ENUM | queued, running, completed, failed, cancelled, retrying |
| priority | INTEGER | Job priority |
| retries | INTEGER | Retry count |
| max_retries | INTEGER | Maximum retries |
| eta | TIMESTAMP | Estimated completion time |
| started_at | TIMESTAMP | Start timestamp |
| completed_at | TIMESTAMP | Completion timestamp |
| evidence_refs | JSONB | Evidence references |
| result | JSONB | Job result data |
| error_message | TEXT | Error message if failed |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (project_id) REFERENCES projects(id)
- FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
- INDEX (project_id, status)
- INDEX (agent_id, status)
- INDEX (priority, created_at)

### findings
Security vulnerabilities discovered.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Foreign key to projects |
| job_id | UUID | Foreign key to jobs |
| test_case_id | UUID | Foreign key to test_cases |
| title | VARCHAR(255) | Finding title |
| description | TEXT | Detailed description |
| severity | ENUM | critical, high, medium, low, info |
| cvss_score | FLOAT | CVSS score (0-10) |
| cvss_vector | VARCHAR(255) | CVSS vector string |
| confidence | FLOAT | Confidence score (0-1) |
| status | ENUM | tentative, validated, false_positive, accepted, fixed |
| affected_url | VARCHAR(2048) | Affected URL |
| affected_parameter | VARCHAR(255) | Affected parameter |
| remediation | TEXT | Remediation advice |
| references | JSONB | External references |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation timestamp |
| validated_at | TIMESTAMP | Validation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (project_id) REFERENCES projects(id)
- FOREIGN KEY (job_id) REFERENCES jobs(id)
- INDEX (project_id, severity)
- INDEX (status)
- INDEX (created_at)

### evidence
Evidence files for findings.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| finding_id | UUID | Foreign key to findings |
| type | ENUM | screenshot, har, video, replay_script, log, raw_request, raw_response |
| storage_key | VARCHAR(512) | S3 storage key |
| filename | VARCHAR(255) | Original filename |
| size_bytes | INTEGER | File size |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (finding_id) REFERENCES findings(id)
- INDEX (finding_id)

### votes
Multi-agent validation votes.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| finding_id | UUID | Foreign key to findings |
| agent_id | VARCHAR(100) | Agent identifier |
| vote | ENUM | accept, reject, more_info |
| rationale | TEXT | Vote rationale |
| confidence | FLOAT | Vote confidence (0-1) |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (finding_id) REFERENCES findings(id)
- INDEX (finding_id)
- INDEX (agent_id)

### agent_logs
Agent execution logs.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| agent_id | VARCHAR(100) | Agent identifier |
| job_id | UUID | Related job ID |
| level | VARCHAR(20) | Log level (info, warning, error) |
| message | TEXT | Log message |
| metadata | JSONB | Additional metadata |
| timestamp | TIMESTAMP | Log timestamp |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (agent_id, timestamp)
- INDEX (job_id)
- INDEX (level, timestamp)

## Data Retention

- **Projects**: Retained indefinitely until deleted by user
- **Findings**: Retained with project
- **Evidence**: Retained for 90 days, then archived
- **Jobs**: Retained for 30 days
- **Logs**: Retained for 7 days
