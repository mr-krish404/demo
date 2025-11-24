"""
Targets endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shared.database import DatabaseManager, Target, TargetType, TargetStatus, Project
from shared.config import settings

router = APIRouter()
db_manager = DatabaseManager(settings.database_url)

class TargetCreate(BaseModel):
    project_id: str
    type: str
    value: str
    scope_rules: Dict[str, Any] = {}

class TargetResponse(BaseModel):
    id: str
    project_id: str
    type: str
    value: str
    scope_rules: Dict[str, Any]
    status: str
    created_at: datetime

@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(target: TargetCreate, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Add a target to a project"""
    session = next(db_manager.get_session())
    try:
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == uuid.UUID(target.project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        new_target = Target(
            project_id=uuid.UUID(target.project_id),
            type=TargetType(target.type),
            value=target.value,
            scope_rules=target.scope_rules,
            status=TargetStatus.PENDING
        )
        session.add(new_target)
        session.commit()
        session.refresh(new_target)
        
        return TargetResponse(
            id=str(new_target.id),
            project_id=str(new_target.project_id),
            type=new_target.type.value,
            value=new_target.value,
            scope_rules=new_target.scope_rules,
            status=new_target.status.value,
            created_at=new_target.created_at
        )
    finally:
        session.close()

@router.get("", response_model=List[TargetResponse])
async def list_targets(project_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """List all targets for a project"""
    session = next(db_manager.get_session())
    try:
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        targets = session.query(Target).filter(Target.project_id == uuid.UUID(project_id)).all()
        
        return [
            TargetResponse(
                id=str(t.id),
                project_id=str(t.project_id),
                type=t.type.value,
                value=t.value,
                scope_rules=t.scope_rules,
                status=t.status.value,
                created_at=t.created_at
            )
            for t in targets
        ]
    finally:
        session.close()

@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(target_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Delete a target"""
    session = next(db_manager.get_session())
    try:
        target = session.query(Target).filter(Target.id == uuid.UUID(target_id)).first()
        
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == target.project_id,
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        session.delete(target)
        session.commit()
    finally:
        session.close()
