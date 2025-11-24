"""
WebSocket manager for real-time updates
"""
from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Map of project_id to set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        
        self.active_connections[project_id].add(websocket)
        print(f"Client connected to project {project_id}. Total connections: {len(self.active_connections[project_id])}")
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            
            # Clean up empty project connections
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        
        print(f"Client disconnected from project {project_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def broadcast_to_project(self, project_id: str, message: dict):
        """Broadcast a message to all connections for a specific project"""
        if project_id not in self.active_connections:
            return
        
        # Create a copy of the set to avoid modification during iteration
        connections = self.active_connections[project_id].copy()
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                # Remove failed connection
                self.disconnect(connection, project_id)
    
    async def send_job_started(self, project_id: str, job_data: dict):
        """Send job started event"""
        message = {
            "type": "job_started",
            "data": job_data,
            "timestamp": job_data.get("created_at")
        }
        await self.broadcast_to_project(project_id, message)
    
    async def send_job_completed(self, project_id: str, job_data: dict):
        """Send job completed event"""
        message = {
            "type": "job_completed",
            "data": job_data,
            "timestamp": job_data.get("completed_at")
        }
        await self.broadcast_to_project(project_id, message)
    
    async def send_finding_created(self, project_id: str, finding_data: dict):
        """Send finding created event"""
        message = {
            "type": "finding_created",
            "data": finding_data,
            "timestamp": finding_data.get("created_at")
        }
        await self.broadcast_to_project(project_id, message)
    
    async def send_scan_progress(self, project_id: str, progress_data: dict):
        """Send scan progress update"""
        message = {
            "type": "scan_progress",
            "data": progress_data,
            "timestamp": progress_data.get("timestamp")
        }
        await self.broadcast_to_project(project_id, message)

# Global connection manager instance
manager = ConnectionManager()
