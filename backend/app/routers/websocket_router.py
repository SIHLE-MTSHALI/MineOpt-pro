"""
WebSocket Router - Real-time collaboration endpoints

Provides:
- WebSocket connection endpoint for real-time updates
- REST endpoints for change log retrieval
- Presence status queries
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Optional
import json

from ..services.websocket_manager import ws_manager
from ..database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...),
    username: str = Query(...),
    schedule_version_id: Optional[str] = Query(None)
):
    """
    WebSocket connection endpoint for real-time collaboration.
    
    Query Parameters:
        user_id: Unique identifier for the user
        username: Display name for presence indicators
        schedule_version_id: Optional schedule to join initially
    
    Message Protocol (client -> server):
        - {"type": "switch_schedule", "schedule_version_id": "..."}
        - {"type": "start_editing", "entity_type": "task", "entity_id": "..."}
        - {"type": "stop_editing"}
        - {"type": "ping"}
    
    Message Protocol (server -> client):
        - {"type": "user_joined", "user_id": "...", "username": "..."}
        - {"type": "user_left", "user_id": "...", "username": "..."}
        - {"type": "presence_list", "users": [...]}
        - {"type": "presence_update", "user_id": "...", ...}
        - {"type": "entity_changed", "entity_type": "...", "action": "...", ...}
        - {"type": "pong"}
    """
    await ws_manager.connect(websocket, user_id, username, schedule_version_id)
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                
                if msg_type == "switch_schedule":
                    new_schedule_id = data.get("schedule_version_id")
                    if new_schedule_id:
                        await ws_manager.switch_schedule(user_id, new_schedule_id)
                
                elif msg_type == "start_editing":
                    entity_type = data.get("entity_type")
                    entity_id = data.get("entity_id")
                    await ws_manager.update_editing_status(
                        user_id, entity_type, entity_id, is_editing=True
                    )
                
                elif msg_type == "stop_editing":
                    await ws_manager.update_editing_status(
                        user_id, None, None, is_editing=False
                    )
                
                elif msg_type == "ping":
                    await ws_manager.send_to_user(user_id, {"type": "pong"})
                
                elif msg_type == "get_presence":
                    schedule_id = data.get("schedule_version_id")
                    await ws_manager.send_presence_list(user_id, schedule_id)
                
            except json.JSONDecodeError:
                # Invalid JSON, ignore
                pass
                
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id)


# REST endpoints for change log and presence

@router.get("/changes/{schedule_version_id}")
def get_change_log(
    schedule_version_id: str,
    limit: int = 50,
    entity_type: Optional[str] = None
):
    """
    Get recent change log entries for a schedule.
    
    Query Parameters:
        limit: Max entries to return (default 50)
        entity_type: Filter by entity type (task, flow, stockpile, etc.)
    """
    return ws_manager.get_change_log(
        schedule_version_id,
        limit=limit,
        entity_type=entity_type
    )


@router.get("/presence/{schedule_version_id}")
def get_presence(schedule_version_id: str):
    """
    Get currently connected users for a schedule.
    """
    users = []
    if schedule_version_id in ws_manager.schedule_connections:
        for uid in ws_manager.schedule_connections[schedule_version_id]:
            if uid in ws_manager.user_presence:
                p = ws_manager.user_presence[uid]
                users.append({
                    "user_id": p.user_id,
                    "username": p.username,
                    "entity_type": p.current_entity_type,
                    "entity_id": p.current_entity_id,
                    "is_editing": p.is_editing,
                    "connected_at": p.connected_at.isoformat()
                })
    
    return {
        "schedule_version_id": schedule_version_id,
        "connected_users": len(users),
        "users": users
    }


@router.get("/presence/{schedule_version_id}/count")
def get_presence_count(schedule_version_id: str):
    """
    Get count of connected users (lightweight endpoint for badges).
    """
    return {
        "count": ws_manager.get_connected_count(schedule_version_id)
    }
