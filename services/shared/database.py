"""
Shared database models and connection management for Apex Pentest X
"""
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Text, Float, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

# Enums
class ProjectStatus(str, Enum):
    CREATED = "created"
    SCANNING = "scanning"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class TargetType(str, Enum):
    URL = "url"
    IP_RANGE = "ip_range"
    DOMAIN = "domain"

class TargetStatus(str, Enum):
    PENDING = "pending"
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"

class CredentialType(str, Enum):
    BASIC = "basic"
    FORM = "form"
    OAUTH = "oauth"
    TOKEN = "token"
    API_KEY = "api_key"

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class FindingStatus(str, Enum):
    TENTATIVE = "tentative"
    VALIDATED = "validated"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED = "accepted"
    FIXED = "fixed"

class EvidenceType(str, Enum):
    SCREENSHOT = "screenshot"
    HAR = "har"
    VIDEO = "video"
    REPLAY_SCRIPT = "replay_script"
    LOG = "log"
    RAW_REQUEST = "raw_request"
    RAW_RESPONSE = "raw_response"

class VoteType(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    MORE_INFO = "more_info"

# Models
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    settings = Column(JSON, nullable=False, default={})
    status = Column(SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.CREATED)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    targets = relationship("Target", back_populates="project", cascade="all, delete-orphan")
    credentials = relationship("Credential", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="project", cascade="all, delete-orphan")

class Target(Base):
    __tablename__ = "targets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    type = Column(SQLEnum(TargetType), nullable=False)
    value = Column(String(1024), nullable=False)
    scope_rules = Column(JSON, nullable=False, default={})
    status = Column(SQLEnum(TargetStatus), nullable=False, default=TargetStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="targets")
    credentials = relationship("Credential", back_populates="target", cascade="all, delete-orphan")

class Credential(Base):
    __tablename__ = "credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=True)
    type = Column(SQLEnum(CredentialType), nullable=False)
    encrypted_payload = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="credentials")
    target = relationship("Target", back_populates="credentials")

class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wstg_id = Column(String(50), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    automatable = Column(Boolean, nullable=False, default=True)
    assigned_agent = Column(String(100), nullable=True)
    priority = Column(Integer, nullable=False, default=5)
    metadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    jobs = relationship("Job", back_populates="test_case")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False)
    agent_id = Column(String(100), nullable=False)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.QUEUED)
    priority = Column(Integer, nullable=False, default=5)
    retries = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    eta = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    evidence_refs = Column(JSON, nullable=False, default=[])
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="jobs")
    test_case = relationship("TestCase", back_populates="jobs")
    findings = relationship("Finding", back_populates="job")

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(FindingSeverity), nullable=False)
    cvss_score = Column(Float, nullable=True)
    cvss_vector = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=False, default=0.5)
    status = Column(SQLEnum(FindingStatus), nullable=False, default=FindingStatus.TENTATIVE)
    affected_url = Column(String(2048), nullable=True)
    affected_parameter = Column(String(255), nullable=True)
    remediation = Column(Text, nullable=True)
    references = Column(JSON, nullable=False, default=[])
    metadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="findings")
    job = relationship("Job", back_populates="findings")
    evidence = relationship("Evidence", back_populates="finding", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="finding", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)
    type = Column(SQLEnum(EvidenceType), nullable=False)
    storage_key = Column(String(512), nullable=False)
    filename = Column(String(255), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    finding = relationship("Finding", back_populates="evidence")

class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)
    agent_id = Column(String(100), nullable=False)
    vote = Column(SQLEnum(VoteType), nullable=False)
    rationale = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    metadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    finding = relationship("Finding", back_populates="votes")

class AgentLog(Base):
    __tablename__ = "agent_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=False, default={})
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

# Database connection management
class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables in the database"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
