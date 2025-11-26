"""
Orchestrator Service - Manages test planning, job scheduling, and scan coordination
"""
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared.config import settings
from shared.database import DatabaseManager, Project, Target, TestCase, Job, JobStatus
from app.test_planner import TestPlanner
from app.scheduler import JobScheduler
from app.celery_app import celery_app

# Initialize FastAPI app
app = FastAPI(
    title="Apex Pentest X Orchestrator",
    description="Orchestration service for test planning and job scheduling",
    version="1.0.0"
)

# Database
db_manager = DatabaseManager(settings.database_url)

# Test planner and scheduler
test_planner = TestPlanner()
job_scheduler = JobScheduler()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "orchestrator"}

@app.post("/api/orchestrate/scan")
async def orchestrate_scan(project_id: str, config: Dict[str, Any] = {}):
    """
    Orchestrate a complete scan for a project
    - Generate test plan
    - Schedule jobs
    - Return scan metadata
    """
    session = next(db_manager.get_session())
    try:
        # Get project and targets
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        targets = session.query(Target).filter(Target.project_id == project_id).all()
        if not targets:
            raise HTTPException(status_code=400, detail="No targets defined for project")
        
        # Generate test plan
        test_plan = test_planner.generate_plan(project, targets, config)
        
        # Schedule jobs
        scheduled_jobs = job_scheduler.schedule_jobs(session, project_id, test_plan)
        
        session.commit()
        
        return {
            "message": "Scan orchestrated successfully",
            "project_id": project_id,
            "test_plan": test_plan,
            "scheduled_jobs": len(scheduled_jobs),
            "job_ids": [str(job.id) for job in scheduled_jobs]
        }
    finally:
        session.close()

@app.get("/api/orchestrate/status/{project_id}")
async def get_scan_status(project_id: str):
    """Get the current status of a scan"""
    session = next(db_manager.get_session())
    try:
        jobs = session.query(Job).filter(Job.project_id == project_id).all()
        
        status_counts = {
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for job in jobs:
            status_counts[job.status.value] += 1
        
        total_jobs = len(jobs)
        progress = (status_counts["completed"] / total_jobs * 100) if total_jobs > 0 else 0
        
        return {
            "project_id": project_id,
            "total_jobs": total_jobs,
            "status_counts": status_counts,
            "progress_percent": progress,
            "is_complete": status_counts["queued"] == 0 and status_counts["running"] == 0
        }
    finally:
        session.close()

@app.post("/dispatch-job")
async def dispatch_job(request: dict):
    """Dispatch a job to Celery worker"""
    from app.celery_app import execute_agent_job
    import uuid
    
    job_id = request.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    # Update job status to queued
    session = next(db_manager.get_session())
    try:
        job = session.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
        if job:
            job.status = JobStatus.QUEUED
            session.commit()
            
            # Get job details for agent execution
            test_case = session.query(TestCase).filter(TestCase.id == job.test_case_id).first()
            
            # Dispatch to Celery with proper parameters
            task = execute_agent_job.delay(
                job_id=str(job.id),
                agent_type=job.agent_id,
                parameters=job.evidence_refs or {}
            )
            
            return {
                "message": "Job dispatched successfully",
                "job_id": job_id,
                "task_id": task.id
            }
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    finally:
        session.close()

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    db_manager.create_tables()
    
    # Seed test cases if not present
    session = next(db_manager.get_session())
    try:
        existing_count = session.query(TestCase).count()
        if existing_count == 0:
            test_planner.seed_test_cases(session)
            session.commit()
    finally:
        session.close()
    
    print("Orchestrator service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Orchestrator service shutting down")
