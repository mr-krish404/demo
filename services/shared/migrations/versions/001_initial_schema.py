"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE project_status AS ENUM ('created', 'scanning', 'paused', 'completed', 'failed')")
    op.execute("CREATE TYPE target_type AS ENUM ('url', 'ip_range', 'domain')")
    op.execute("CREATE TYPE target_status AS ENUM ('pending', 'in_scope', 'out_of_scope')")
    op.execute("CREATE TYPE credential_type AS ENUM ('basic', 'form', 'oauth', 'token', 'api_key')")
    op.execute("CREATE TYPE job_status AS ENUM ('queued', 'running', 'completed', 'failed', 'cancelled', 'retrying')")
    op.execute("CREATE TYPE finding_severity AS ENUM ('critical', 'high', 'medium', 'low', 'info')")
    op.execute("CREATE TYPE finding_status AS ENUM ('tentative', 'validated', 'false_positive', 'accepted', 'fixed')")
    op.execute("CREATE TYPE evidence_type AS ENUM ('screenshot', 'har', 'video', 'replay_script', 'log', 'raw_request', 'raw_response')")
    op.execute("CREATE TYPE vote_type AS ENUM ('accept', 'reject', 'more_info')")
    
    # Create projects table
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_id', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('settings', postgresql.JSONB),
        sa.Column('status', sa.Enum('created', 'scanning', 'paused', 'completed', 'failed', name='project_status'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    op.create_index('idx_projects_owner', 'projects', ['owner_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    
    # Create targets table
    op.create_table('targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('url', 'ip_range', 'domain', name='target_type'), nullable=False),
        sa.Column('value', sa.String(1024), nullable=False),
        sa.Column('scope_rules', postgresql.JSONB),
        sa.Column('status', sa.Enum('pending', 'in_scope', 'out_of_scope', name='target_status'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE')
    )
    op.create_index('idx_targets_project', 'targets', ['project_id'])
    
    # Create credentials table
    op.create_table('credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True)),
        sa.Column('type', sa.Enum('basic', 'form', 'oauth', 'token', 'api_key', name='credential_type'), nullable=False),
        sa.Column('encrypted_payload', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='CASCADE')
    )
    
    # Create test_cases table
    op.create_table('test_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('wstg_id', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(100)),
        sa.Column('automatable', sa.Boolean, nullable=False),
        sa.Column('assigned_agent', sa.String(100)),
        sa.Column('priority', sa.Integer),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False)
    )
    op.create_index('idx_test_cases_category', 'test_cases', ['category'])
    op.create_index('idx_test_cases_agent', 'test_cases', ['assigned_agent'])
    
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('test_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('queued', 'running', 'completed', 'failed', 'cancelled', 'retrying', name='job_status'), nullable=False),
        sa.Column('priority', sa.Integer, nullable=False),
        sa.Column('retries', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('eta', sa.DateTime),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('evidence_refs', postgresql.JSONB),
        sa.Column('result', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'])
    )
    op.create_index('idx_jobs_project_status', 'jobs', ['project_id', 'status'])
    op.create_index('idx_jobs_agent_status', 'jobs', ['agent_id', 'status'])
    op.create_index('idx_jobs_priority', 'jobs', ['priority', 'created_at'])
    
    # Create findings table
    op.create_table('findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True)),
        sa.Column('test_case_id', postgresql.UUID(as_uuid=True)),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', 'info', name='finding_severity'), nullable=False),
        sa.Column('cvss_score', sa.Float),
        sa.Column('cvss_vector', sa.String(255)),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('status', sa.Enum('tentative', 'validated', 'false_positive', 'accepted', 'fixed', name='finding_status'), nullable=False),
        sa.Column('affected_url', sa.String(2048)),
        sa.Column('affected_parameter', sa.String(255)),
        sa.Column('remediation', sa.Text),
        sa.Column('references', postgresql.JSONB),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('validated_at', sa.DateTime),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'])
    )
    op.create_index('idx_findings_project_severity', 'findings', ['project_id', 'severity'])
    op.create_index('idx_findings_status', 'findings', ['status'])
    op.create_index('idx_findings_created', 'findings', ['created_at'])
    
    # Create evidence table
    op.create_table('evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('finding_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('screenshot', 'har', 'video', 'replay_script', 'log', 'raw_request', 'raw_response', name='evidence_type'), nullable=False),
        sa.Column('storage_key', sa.String(512), nullable=False),
        sa.Column('filename', sa.String(255)),
        sa.Column('size_bytes', sa.Integer),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE')
    )
    op.create_index('idx_evidence_finding', 'evidence', ['finding_id'])
    
    # Create votes table
    op.create_table('votes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('finding_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('vote', sa.Enum('accept', 'reject', 'more_info', name='vote_type'), nullable=False),
        sa.Column('rationale', sa.Text),
        sa.Column('confidence', sa.Float),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE')
    )
    op.create_index('idx_votes_finding', 'votes', ['finding_id'])
    op.create_index('idx_votes_agent', 'votes', ['agent_id'])
    
    # Create agent_logs table
    op.create_table('agent_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True)),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE')
    )
    op.create_index('idx_agent_logs_agent_time', 'agent_logs', ['agent_id', 'timestamp'])
    op.create_index('idx_agent_logs_job', 'agent_logs', ['job_id'])
    op.create_index('idx_agent_logs_level_time', 'agent_logs', ['level', 'timestamp'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('agent_logs')
    op.drop_table('votes')
    op.drop_table('evidence')
    op.drop_table('findings')
    op.drop_table('jobs')
    op.drop_table('test_cases')
    op.drop_table('credentials')
    op.drop_table('targets')
    op.drop_table('projects')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS vote_type")
    op.execute("DROP TYPE IF EXISTS evidence_type")
    op.execute("DROP TYPE IF EXISTS finding_status")
    op.execute("DROP TYPE IF EXISTS finding_severity")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS credential_type")
    op.execute("DROP TYPE IF EXISTS target_status")
    op.execute("DROP TYPE IF EXISTS target_type")
    op.execute("DROP TYPE IF EXISTS project_status")
