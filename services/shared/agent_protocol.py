"""
Agent communication protocol
"""
from typing import Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

MessageType = Literal["proposal", "vote", "result", "heartbeat", "request", "response"]

class AgentMessage(BaseModel):
    """Standard message envelope for agent communication"""
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str
    to_agent: str  # Can be specific agent ID or "all" for broadcast
    type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProposalMessage(BaseModel):
    """Proposal for a finding or action"""
    finding_id: Optional[str] = None
    title: str
    description: str
    severity: str
    confidence: float
    evidence: list = []

class VoteMessage(BaseModel):
    """Vote on a finding"""
    finding_id: str
    vote: Literal["accept", "reject", "more_info"]
    rationale: str
    confidence: float

class ResultMessage(BaseModel):
    """Result of an agent task"""
    job_id: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

class HeartbeatMessage(BaseModel):
    """Agent heartbeat"""
    agent_id: str
    status: str
    current_job: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

class RequestMessage(BaseModel):
    """Request for information or action"""
    request_type: str
    parameters: Dict[str, Any]

class ResponseMessage(BaseModel):
    """Response to a request"""
    request_id: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
