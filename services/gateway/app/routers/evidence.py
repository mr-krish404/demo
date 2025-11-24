"""
Evidence endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shared.database import DatabaseManager, Evidence, Finding, Project
from shared.config import settings
from shared.storage import StorageManager

router = APIRouter()
db_manager = DatabaseManager(settings.database_url)
storage_manager = StorageManager()

class EvidenceResponse(BaseModel):
    id: str
    finding_id: str
    type: str
    filename: Optional[str]
    size_bytes: Optional[int]
    download_url: Optional[str]
    created_at: datetime

@router.get("", response_model=List[EvidenceResponse])
async def list_evidence(finding_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """List all evidence for a finding"""
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
        
        evidence_list = session.query(Evidence).filter(Evidence.finding_id == uuid.UUID(finding_id)).all()
        
        return [
            EvidenceResponse(
                id=str(e.id),
                finding_id=str(e.finding_id),
                type=e.type.value,
                filename=e.filename,
                size_bytes=e.size_bytes,
                download_url=storage_manager.get_presigned_url(e.storage_key),
                created_at=e.created_at
            )
            for e in evidence_list
        ]
    finally:
        session.close()

@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Get details of specific evidence"""
    session = next(db_manager.get_session())
    try:
        evidence = session.query(Evidence).filter(Evidence.id == uuid.UUID(evidence_id)).first()
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        finding = session.query(Finding).filter(Finding.id == evidence.finding_id).first()
        
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == finding.project_id,
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return EvidenceResponse(
            id=str(evidence.id),
            finding_id=str(evidence.finding_id),
            type=evidence.type.value,
            filename=evidence.filename,
            size_bytes=evidence.size_bytes,
            download_url=storage_manager.get_presigned_url(evidence.storage_key),
            created_at=evidence.created_at
        )
    finally:
        session.close()
