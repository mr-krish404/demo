"""
Agent management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()

class AgentResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    current_job: Optional[str]
    last_heartbeat: Optional[datetime]

# Mock agent data for now
AGENTS = [
    {
        "id": "recon-agent-1",
        "name": "Recon Agent",
        "type": "recon",
        "status": "idle",
        "current_job": None,
        "last_heartbeat": datetime.utcnow()
    },
    {
        "id": "fuzz-agent-1",
        "name": "Fuzz Agent",
        "type": "fuzz",
        "status": "idle",
        "current_job": None,
        "last_heartbeat": datetime.utcnow()
    },
    {
        "id": "exploit-agent-1",
        "name": "Exploit Agent",
        "type": "exploit",
        "status": "idle",
        "current_job": None,
        "last_heartbeat": datetime.utcnow()
    },
    {
        "id": "validator-agent-1",
        "name": "Validator Agent",
        "type": "validator",
        "status": "idle",
        "current_job": None,
        "last_heartbeat": datetime.utcnow()
    }
]

@router.get("", response_model=List[AgentResponse])
async def list_agents(current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """List all available agents"""
    return [AgentResponse(**agent) for agent in AGENTS]

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Get details of a specific agent"""
    agent = next((a for a in AGENTS if a["id"] == agent_id), None)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(**agent)

@router.post("/{agent_id}/restart")
async def restart_agent(agent_id: str, current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Restart an agent"""
    agent = next((a for a in AGENTS if a["id"] == agent_id), None)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # TODO: Implement actual agent restart logic
    
    return {
        "message": "Agent restart initiated",
        "agent_id": agent_id
    }
