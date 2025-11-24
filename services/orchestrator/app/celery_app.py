"""
Celery application for async task processing
"""
from celery import Celery
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared.config import settings

# Initialize Celery
celery_app = Celery(
    "apex_orchestrator",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100
)

@celery_app.task(name="execute_agent_job")
def execute_agent_job(job_id: str, agent_type: str, parameters: dict):
    """
    Execute an agent job
    This task is picked up by Celery workers
    """
    from shared.database import DatabaseManager
    from app.scheduler import JobScheduler
    
    db_manager = DatabaseManager(settings.database_url)
    scheduler = JobScheduler()
    
    session = next(db_manager.get_session())
    try:
        import uuid
        job_uuid = uuid.UUID(job_id)
        
        # Mark job as running
        scheduler.mark_job_running(session, job_uuid)
        
        # TODO: Call agent runner to execute the job
        # For now, simulate execution
        result = {
            "status": "completed",
            "agent": agent_type,
            "findings": []
        }
        
        # Mark job as completed
        scheduler.mark_job_completed(session, job_uuid, result)
        
        return result
    except Exception as e:
        # Mark job as failed
        scheduler.mark_job_failed(session, job_uuid, str(e))
        raise
    finally:
        session.close()

@celery_app.task(name="validate_finding")
def validate_finding(finding_id: str):
    """
    Trigger multi-agent validation for a finding
    """
    # TODO: Implement validation logic
    return {"status": "validated", "finding_id": finding_id}

@celery_app.task(name="generate_report")
def generate_report(project_id: str, format: str = "pdf"):
    """
    Generate a report for a project
    """
    # TODO: Implement report generation
    return {"status": "generated", "project_id": project_id, "format": format}
