"""
WebSocket router for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..websocket import manager
import json

router = APIRouter()

@router.websocket("/ws/projects/{project_id}/events")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time project events
    
    Clients can connect to receive real-time updates about:
    - Job status changes
    - New findings
    - Scan progress
    - Agent activity
    """
    await manager.connect(websocket, project_id)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "message": f"Connected to project {project_id} events",
            "project_id": project_id
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages from client (e.g., ping/pong for keepalive)
            data = await websocket.receive_text()
            
            # Handle client messages
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, websocket)
            
            except json.JSONDecodeError:
                # Ignore invalid JSON
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, project_id)
