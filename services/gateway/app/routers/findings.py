"""
Findings endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shared.database import DatabaseManager, Finding, FindingSeverity, FindingStatus, Project
from shared.config import settings

router = APIRouter()
db_manager = DatabaseManager(settings.database_url)

class FindingResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    severity: str
    cvss_score: Optional[float]
    confidence: float
    status: str
    affected_url: Optional[str]
    affected_parameter: Optional[str]
    created_at: datetime
    validated_at: Optional[datetime]

class CommentRequest(BaseModel):
    comment: str

class ValidateRequest(BaseModel):
    status: str
    notes: Optional[str] = None

@router.get("", response_model=List[FindingResponse])
async def list_findings(project_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """List all findings for a project"""
    session = next(db_manager.get_session())
    try:
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        findings = session.query(Finding).filter(Finding.project_id == uuid.UUID(project_id)).all()
        
        return [
            FindingResponse(
                id=str(f.id),
                project_id=str(f.project_id),
                title=f.title,
                description=f.description,
                severity=f.severity.value,
                cvss_score=f.cvss_score,
                confidence=f.confidence,
                status=f.status.value,
                affected_url=f.affected_url,
                affected_parameter=f.affected_parameter,
                created_at=f.created_at,
                validated_at=f.validated_at
            )
            for f in findings
        ]
    finally:
        session.close()

@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Get details of a specific finding"""
    session = next(db_manager.get_session())
    try:
        finding = session.query(Finding).filter(Finding.id == uuid.UUID(finding_id)).first()
        
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == finding.project_id,
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return FindingResponse(
            id=str(finding.id),
            project_id=str(finding.project_id),
            title=finding.title,
            description=finding.description,
            severity=finding.severity.value,
            cvss_score=finding.cvss_score,
            confidence=finding.confidence,
            status=finding.status.value,
            affected_url=finding.affected_url,
            affected_parameter=finding.affected_parameter,
            created_at=finding.created_at,
            validated_at=finding.validated_at
        )
    finally:
        session.close()

@router.post("/{finding_id}/comment")
async def add_comment(
    finding_id: str,
    request: CommentRequest,
    current_user: dict = Depends(lambda: {"sub": "user_1"})
):
    """Add a comment to a finding"""
    # TODO: Implement comment storage
    return {
        "message": "Comment added successfully",
        "finding_id": finding_id,
        "comment": request.comment
    }

@router.post("/{finding_id}/validate")
async def validate_finding(
    finding_id: str,
    request: ValidateRequest,
    current_user: dict = Depends(lambda: {"sub": "user_1"})
):
    """Validate or mark a finding as false positive"""
    session = next(db_manager.get_session())
    try:
        finding = session.query(Finding).filter(Finding.id == uuid.UUID(finding_id)).first()
        
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == finding.project_id,
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        finding.status = FindingStatus(request.status)
        if request.status == "validated":
            finding.validated_at = datetime.utcnow()
        
        session.commit()
        
        return {
            "message": "Finding status updated successfully",
            "finding_id": finding_id,
            "status": request.status
        }
    finally:
        session.close()
