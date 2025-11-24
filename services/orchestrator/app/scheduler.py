"""
Job Scheduler - Schedules and prioritizes test jobs
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared.database import Job, JobStatus, TestCase

class JobScheduler:
    """Schedules jobs for agent execution"""
    
    def schedule_jobs(self, session, project_id: str, test_plan: Dict[str, Any]) -> List[Job]:
        """
        Schedule jobs based on test plan
        Returns list of created jobs
        """
        scheduled_jobs = []
        current_time = datetime.utcnow()
        
        for test_case_data in test_plan["test_cases"]:
            # Get test case from database
            test_case = session.query(TestCase).filter(
                TestCase.wstg_id == test_case_data["wstg_id"]
            ).first()
            
            if not test_case:
                continue
            
            # Create job
            job = Job(
                project_id=uuid.UUID(project_id),
                test_case_id=test_case.id,
                agent_id=test_case_data["agent"],
                status=JobStatus.QUEUED,
                priority=test_case_data["priority"],
                retries=0,
                max_retries=3,
                eta=current_time + timedelta(minutes=test_case_data["priority"] * 5)
            )
            
            session.add(job)
            scheduled_jobs.append(job)
        
        return scheduled_jobs
    
    def get_next_job(self, session, agent_type: str = None):
        """
        Get the next job to execute
        Prioritizes by priority and creation time
        """
        query = session.query(Job).filter(Job.status == JobStatus.QUEUED)
        
        if agent_type:
            query = query.filter(Job.agent_id.like(f"{agent_type}%"))
        
        job = query.order_by(Job.priority.desc(), Job.created_at.asc()).first()
        
        return job
    
    def mark_job_running(self, session, job_id: uuid.UUID):
        """Mark a job as running"""
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            session.commit()
    
    def mark_job_completed(self, session, job_id: uuid.UUID, result: Dict[str, Any]):
        """Mark a job as completed"""
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            session.commit()
    
    def mark_job_failed(self, session, job_id: uuid.UUID, error: str):
        """Mark a job as failed and potentially retry"""
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.retries += 1
            job.error_message = error
            
            if job.retries < job.max_retries:
                job.status = JobStatus.RETRYING
                job.eta = datetime.utcnow() + timedelta(minutes=5 * job.retries)
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
            
            session.commit()
