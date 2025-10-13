from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
from backend.utils.logger import logger

router = APIRouter(tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info(f"🔌 WebSocket connected for session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"🔌 WebSocket disconnected for session {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass
    
    async def broadcast(self, message: dict):
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/messages")
async def websocket_messages(websocket: WebSocket, session_id: str = "default"):
    """WebSocket endpoint for real-time message updates"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Echo back for now (can be extended for two-way communication)
            message = json.loads(data)
            await manager.send_message(session_id, {
                "type": "echo",
                "data": message
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)


async def notify_new_message(session_id: str, thread_id: str, message_data: dict):
    """Helper to notify clients of new messages"""
    await manager.send_message(session_id, {
        "type": "new_message",
        "thread_id": thread_id,
        "message": message_data
    })


async def notify_job_status(session_id: str, job_id: str, status: str, logs: list = None):
    """Helper to notify clients of job status updates"""
    await manager.send_message(session_id, {
        "type": "job_status",
        "job_id": job_id,
        "status": status,
        "logs": logs or []
    })
