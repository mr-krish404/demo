"""
Agent Runner Service - Manages agent container lifecycle
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import docker
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Apex Pentest X Agent Runner",
    description="Agent container management service",
    version="1.0.0"
)

# Docker client
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Warning: Could not connect to Docker: {e}")
    docker_client = None

class AgentJobRequest(BaseModel):
    job_id: str
    agent_type: str
    parameters: Dict[str, Any]
    timeout_seconds: Optional[int] = 300

class AgentJobResponse(BaseModel):
    job_id: str
    container_id: str
    status: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent-runner",
        "docker_available": docker_client is not None
    }

@app.post("/api/agent/execute", response_model=AgentJobResponse)
async def execute_agent(request: AgentJobRequest):
    """
    Execute an agent in an isolated container
    """
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        # Determine agent image
        agent_image = f"apex-{request.agent_type}:latest"
        
        # Container configuration
        container_config = {
            "image": agent_image,
            "name": f"agent-{request.job_id}",
            "environment": {
                "JOB_ID": request.job_id,
                "AGENT_TYPE": request.agent_type,
                "DATABASE_URL": settings.database_url,
                "REDIS_URL": settings.redis_url
            },
            "network": "apex-network",
            "detach": True,
            "remove": True,
            "mem_limit": f"{settings.agent_memory_limit_mb}m",
            "cpu_period": 100000,
            "cpu_quota": 50000,  # 50% CPU
            "security_opt": ["no-new-privileges"],
            "cap_drop": ["ALL"],
            "cap_add": ["NET_BIND_SERVICE"]
        }
        
        # Run container
        container = docker_client.containers.run(**container_config)
        
        return AgentJobResponse(
            job_id=request.job_id,
            container_id=container.id,
            status="running"
        )
    except docker.errors.ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Agent image not found: {agent_image}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")

@app.get("/api/agent/status/{container_id}")
async def get_agent_status(container_id: str):
    """Get the status of a running agent container"""
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        container = docker_client.containers.get(container_id)
        return {
            "container_id": container_id,
            "status": container.status,
            "logs": container.logs(tail=100).decode('utf-8')
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")

@app.post("/api/agent/stop/{container_id}")
async def stop_agent(container_id: str):
    """Stop a running agent container"""
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        container = docker_client.containers.get(container_id)
        container.stop(timeout=10)
        return {"message": "Agent stopped successfully", "container_id": container_id}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Agent Runner service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Agent Runner service shutting down")
