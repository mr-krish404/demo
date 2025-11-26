"""
Scan management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shared.database import DatabaseManager, Job, JobStatus, Project
from shared.config import settings

router = APIRouter()
db_manager = DatabaseManager(settings.database_url)

class ScanStartRequest(BaseModel):
    test_cases: Optional[List[str]] = None
    config: Dict[str, Any] = {}

class JobResponse(BaseModel):
    id: str
    project_id: str
    test_case_id: str
    agent_id: str
    status: str
    priority: int
    retries: int
    eta: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

@router.post("/{project_id}/start")
async def start_scan(
    project_id: str,
    request: ScanStartRequest,
    current_user: dict = Depends(lambda: {"sub": "user_1"})
):
    """Start a scan for a project"""
    import httpx
    from shared.database import TestCase, Target
    
    session = next(db_manager.get_session())
    try:
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get targets for the project
        targets = session.query(Target).filter(Target.project_id == uuid.UUID(project_id)).all()
        if not targets:
            raise HTTPException(status_code=400, detail="No targets configured for this project")
        
        # Get test cases to run
        test_case_query = session.query(TestCase)
        if request.test_cases:
            test_case_query = test_case_query.filter(TestCase.wstg_id.in_(request.test_cases))
        test_cases = test_case_query.filter(TestCase.automatable == True).all()
        
        if not test_cases:
            raise HTTPException(status_code=400, detail="No automatable test cases found")
        
        # Create jobs for each test case
        from shared.database import Job, JobStatus
        from datetime import datetime, timedelta
        
        jobs_created = []
        for test_case in test_cases:
            for target in targets:
                job = Job(
                    project_id=uuid.UUID(project_id),
                    test_case_id=test_case.id,
                    agent_id=test_case.assigned_agent,
                    status=JobStatus.PENDING,
                    priority=5,  # Default priority
                    retries=0,
                    eta=datetime.utcnow() + timedelta(seconds=10),
                    evidence_refs={"target_id": str(target.id), "target_value": target.value}
                )
                session.add(job)
                jobs_created.append(job)
        
        session.commit()
        
        # Dispatch jobs to Celery
        for job in jobs_created:
            try:
                # Call orchestrator to dispatch job
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://orchestrator:8081/dispatch-job",
                        json={"job_id": str(job.id)},
                        timeout=5.0
                    )
            except Exception as e:
                print(f"Failed to dispatch job {job.id}: {e}")
        
        return {
            "message": "Scan started successfully",
            "project_id": project_id,
            "status": "queued",
            "jobs_created": len(jobs_created)
        }
    finally:
        session.close()

@router.get("/{project_id}/jobs", response_model=List[JobResponse])
async def list_jobs(project_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """List all jobs for a project"""
    session = next(db_manager.get_session())
    try:
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        jobs = session.query(Job).filter(Job.project_id == uuid.UUID(project_id)).all()
        
        return [
            JobResponse(
                id=str(j.id),
                project_id=str(j.project_id),
                test_case_id=str(j.test_case_id),
                agent_id=j.agent_id,
                status=j.status.value,
                priority=j.priority,
                retries=j.retries,
                eta=j.eta,
                started_at=j.started_at,
                completed_at=j.completed_at,
                created_at=j.created_at
            )
            for j in jobs
        ]
    finally:
        session.close()

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Get details of a specific job"""
    session = next(db_manager.get_session())
    try:
        job = session.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == job.project_id,
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return JobResponse(
            id=str(job.id),
            project_id=str(job.project_id),
            test_case_id=str(job.test_case_id),
            agent_id=job.agent_id,
            status=job.status.value,
            priority=job.priority,
            retries=job.retries,
            eta=job.eta,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at
        )
    finally:
        session.close()

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Cancel a running job"""
    session = next(db_manager.get_session())
    try:
        job = session.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify project ownership
        project = session.query(Project).filter(
            Project.id == job.project_id,
            Project.owner_id == current_user["sub"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        job.status = JobStatus.CANCELLED
        session.commit()
        
        return {"message": "Job cancelled successfully", "job_id": job_id}
    finally:
        session.close()
