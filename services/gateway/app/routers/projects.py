"""
Projects endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shared.database import DatabaseManager, Project, ProjectStatus
from shared.config import settings

router = APIRouter()
db_manager = DatabaseManager(settings.database_url)

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Dict[str, Any] = {}

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    settings: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

@router.get("", response_model=List[ProjectResponse])
async def list_projects(current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """List all projects for the current user"""
    session = next(db_manager.get_session())
    try:
        projects = session.query(Project).filter(Project.owner_id == current_user["sub"]).all()
        return [
            ProjectResponse(
                id=str(p.id),
                name=p.name,
                description=p.description,
                owner_id=p.owner_id,
                settings=p.settings,
                status=p.status.value,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in projects
        ]
    finally:
        session.close()

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Create a new project"""
    session = next(db_manager.get_session())
    try:
        new_project = Project(
            name=project.name,
            description=project.description,
            owner_id=current_user["sub"],
            settings=project.settings,
            status=ProjectStatus.CREATED
        )
        session.add(new_project)
        session.commit()
        session.refresh(new_project)
        
        return ProjectResponse(
            id=str(new_project.id),
            name=new_project.name,
            description=new_project.description,
            owner_id=new_project.owner_id,
            settings=new_project.settings,
            status=new_project.status.value,
            created_at=new_project.created_at,
            updated_at=new_project.updated_at
        )
    finally:
        session.close()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Get a specific project"""
    session = next(db_manager.get_session())
    try:
        project = session.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            settings=project.settings,
            status=project.status.value,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
    finally:
        session.close()

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    updates: ProjectUpdate,
    current_user: dict = Depends(lambda: {"sub": "user_1"})
):
    """Update a project"""
    session = next(db_manager.get_session())
    try:
        project = session.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if updates.name is not None:
            project.name = updates.name
        if updates.description is not None:
            project.description = updates.description
        if updates.settings is not None:
            project.settings = updates.settings
        if updates.status is not None:
            project.status = ProjectStatus(updates.status)
        
        project.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(project)
        
        return ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            settings=project.settings,
            status=project.status.value,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
    finally:
        session.close()

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Delete a project"""
    session = next(db_manager.get_session())
    try:
        project = session.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        session.delete(project)
        session.commit()
    finally:
        session.close()
