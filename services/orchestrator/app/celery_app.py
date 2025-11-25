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
    Execute an agent job by calling the agent runner
    This task is picked up by Celery workers
    """
    from shared.database import DatabaseManager
    from app.scheduler import JobScheduler
    import requests
    
    db_manager = DatabaseManager(settings.database_url)
    scheduler = JobScheduler()
    
    session = next(db_manager.get_session())
    try:
        import uuid
        job_uuid = uuid.UUID(job_id)
        
        # Mark job as running
        scheduler.mark_job_running(session, job_uuid)
        
        # Call agent runner to execute the job
        agent_runner_url = os.getenv("AGENT_RUNNER_URL", "http://agent-runner:8082")
        
        response = requests.post(
            f"{agent_runner_url}/execute",
            json={
                "job_id": job_id,
                "agent_type": agent_type,
                "parameters": parameters
            },
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            scheduler.mark_job_completed(session, job_uuid, result)
            return result
        else:
            error_msg = f"Agent runner returned status {response.status_code}"
            scheduler.mark_job_failed(session, job_uuid, error_msg)
            raise Exception(error_msg)
            
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
    import requests
    
    agent_runner_url = os.getenv("AGENT_RUNNER_URL", "http://agent-runner:8082")
    
    try:
        # Trigger validator agent
        response = requests.post(
            f"{agent_runner_url}/execute",
            json={
                "job_id": finding_id,
                "agent_type": "validator-agent",
                "parameters": {"finding_id": finding_id}
            },
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "failed", "finding_id": finding_id}
    except Exception as e:
        return {"status": "error", "finding_id": finding_id, "error": str(e)}

@celery_app.task(name="generate_report")
def generate_report(project_id: str, format: str = "pdf"):
    """
    Generate a report for a project
    """
    import requests
    
    agent_runner_url = os.getenv("AGENT_RUNNER_URL", "http://agent-runner:8082")
    
    try:
        # Trigger reporter agent
        response = requests.post(
            f"{agent_runner_url}/execute",
            json={
                "job_id": f"report-{project_id}",
                "agent_type": "reporter-agent",
                "parameters": {"project_id": project_id, "format": format}
            },
            timeout=600  # 10 minute timeout for report generation
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "failed", "project_id": project_id}
    except Exception as e:
        return {"status": "error", "project_id": project_id, "error": str(e)}

@celery_app.task(name="run_learning_agent")
def run_learning_agent(project_id: str):
    """
    Run learning agent to analyze patterns
    """
    import requests
    
    agent_runner_url = os.getenv("AGENT_RUNNER_URL", "http://agent-runner:8082")
    
    try:
        response = requests.post(
            f"{agent_runner_url}/execute",
            json={
                "job_id": f"learning-{project_id}",
                "agent_type": "learning-agent",
                "parameters": {"project_id": project_id}
            },
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "failed", "project_id": project_id}
    except Exception as e:
        return {"status": "error", "project_id": project_id, "error": str(e)}
