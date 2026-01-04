"""
WebSocket Manager - Real-time collaboration infrastructure

Provides:
- Connection management (track connected users by schedule version)
- Event broadcasting (push updates to all connected clients)
- Presence tracking (who is viewing/editing what)
- Message routing for different event types
"""

from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio


@dataclass
class UserPresence:
    """Tracks a connected user's presence."""
    user_id: str
    username: str
    websocket: WebSocket
    connected_at: datetime
    current_schedule_id: Optional[str] = None
    current_entity_type: Optional[str] = None  # 'task', 'flow', 'stockpile', etc.
    current_entity_id: Optional[str] = None
    is_editing: bool = False


@dataclass
class ChangeLogEntry:
    """Records a change for the change log panel."""
    timestamp: datetime
    user_id: str
    username: str
    entity_type: str
    entity_id: str
    action: str  # 'create', 'update', 'delete'
    summary: str
    schedule_version_id: str


class WebSocketManager:
    """
    Manages WebSocket connections for real-time collaboration.
    
    Tracks users per schedule version and broadcasts events.
    """
    
    def __init__(self):
        # Map: schedule_version_id -> set of user_ids
        self.schedule_connections: Dict[str, Set[str]] = {}
        
        # Map: user_id -> UserPresence
        self.user_presence: Dict[str, UserPresence] = {}
        
        # Recent change log (ring buffer, last 100 entries per schedule)
        self.change_logs: Dict[str, List[ChangeLogEntry]] = {}
        self.max_log_entries = 100
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        username: str,
        schedule_version_id: Optional[str] = None
    ):
        """
        Accept a new WebSocket connection and register the user.
        """
        await websocket.accept()
        
        presence = UserPresence(
            user_id=user_id,
            username=username,
            websocket=websocket,
            connected_at=datetime.utcnow(),
            current_schedule_id=schedule_version_id
        )
        
        self.user_presence[user_id] = presence
        
        if schedule_version_id:
            if schedule_version_id not in self.schedule_connections:
                self.schedule_connections[schedule_version_id] = set()
            self.schedule_connections[schedule_version_id].add(user_id)
            
            # Notify others that user joined
            await self.broadcast_to_schedule(
                schedule_version_id,
                {
                    "type": "user_joined",
                    "user_id": user_id,
                    "username": username,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_user_id=user_id
            )
        
        # Send initial presence list to newly connected user
        await self.send_presence_list(user_id, schedule_version_id)
    
    async def disconnect(self, user_id: str):
        """
        Handle disconnection and cleanup.
        """
        if user_id not in self.user_presence:
            return
        
        presence = self.user_presence[user_id]
        schedule_id = presence.current_schedule_id
        
        # Remove from schedule connections
        if schedule_id and schedule_id in self.schedule_connections:
            self.schedule_connections[schedule_id].discard(user_id)
            
            # Notify others that user left
            await self.broadcast_to_schedule(
                schedule_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "username": presence.username,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Cleanup empty schedule rooms
            if not self.schedule_connections[schedule_id]:
                del self.schedule_connections[schedule_id]
        
        del self.user_presence[user_id]
    
    async def switch_schedule(self, user_id: str, new_schedule_id: str):
        """
        Handle user switching to a different schedule version.
        """
        if user_id not in self.user_presence:
            return
        
        presence = self.user_presence[user_id]
        old_schedule_id = presence.current_schedule_id
        
        # Leave old schedule room
        if old_schedule_id and old_schedule_id in self.schedule_connections:
            self.schedule_connections[old_schedule_id].discard(user_id)
            await self.broadcast_to_schedule(
                old_schedule_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "username": presence.username
                }
            )
        
        # Join new schedule room
        presence.current_schedule_id = new_schedule_id
        if new_schedule_id not in self.schedule_connections:
            self.schedule_connections[new_schedule_id] = set()
        self.schedule_connections[new_schedule_id].add(user_id)
        
        await self.broadcast_to_schedule(
            new_schedule_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "username": presence.username
            },
            exclude_user_id=user_id
        )
        
        await self.send_presence_list(user_id, new_schedule_id)
    
    async def update_editing_status(
        self,
        user_id: str,
        entity_type: Optional[str],
        entity_id: Optional[str],
        is_editing: bool
    ):
        """
        Update what entity a user is currently editing.
        Used for edit locks and presence indicators.
        """
        if user_id not in self.user_presence:
            return
        
        presence = self.user_presence[user_id]
        presence.current_entity_type = entity_type
        presence.current_entity_id = entity_id
        presence.is_editing = is_editing
        
        if presence.current_schedule_id:
            await self.broadcast_to_schedule(
                presence.current_schedule_id,
                {
                    "type": "presence_update",
                    "user_id": user_id,
                    "username": presence.username,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "is_editing": is_editing
                },
                exclude_user_id=user_id
            )
    
    async def broadcast_to_schedule(
        self,
        schedule_version_id: str,
        message: Dict[str, Any],
        exclude_user_id: Optional[str] = None
    ):
        """
        Broadcast a message to all users viewing a specific schedule.
        """
        if schedule_version_id not in self.schedule_connections:
            return
        
        user_ids = self.schedule_connections[schedule_version_id]
        
        for uid in user_ids:
            if uid == exclude_user_id:
                continue
            
            if uid in self.user_presence:
                websocket = self.user_presence[uid].websocket
                try:
                    await websocket.send_json(message)
                except Exception:
                    # Connection may be stale, will be cleaned up on next ping
                    pass
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific user.
        """
        if user_id in self.user_presence:
            try:
                await self.user_presence[user_id].websocket.send_json(message)
            except Exception:
                pass
    
    async def send_presence_list(self, user_id: str, schedule_version_id: Optional[str]):
        """
        Send the list of currently connected users for a schedule.
        """
        if not schedule_version_id:
            return
        
        users = []
        if schedule_version_id in self.schedule_connections:
            for uid in self.schedule_connections[schedule_version_id]:
                if uid in self.user_presence:
                    p = self.user_presence[uid]
                    users.append({
                        "user_id": p.user_id,
                        "username": p.username,
                        "entity_type": p.current_entity_type,
                        "entity_id": p.current_entity_id,
                        "is_editing": p.is_editing
                    })
        
        await self.send_to_user(user_id, {
            "type": "presence_list",
            "users": users,
            "schedule_version_id": schedule_version_id
        })
    
    def log_change(
        self,
        schedule_version_id: str,
        user_id: str,
        username: str,
        entity_type: str,
        entity_id: str,
        action: str,
        summary: str
    ):
        """
        Record a change to the change log.
        """
        entry = ChangeLogEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            username=username,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            summary=summary,
            schedule_version_id=schedule_version_id
        )
        
        if schedule_version_id not in self.change_logs:
            self.change_logs[schedule_version_id] = []
        
        self.change_logs[schedule_version_id].append(entry)
        
        # Trim to max entries
        if len(self.change_logs[schedule_version_id]) > self.max_log_entries:
            self.change_logs[schedule_version_id] = \
                self.change_logs[schedule_version_id][-self.max_log_entries:]
    
    async def broadcast_change(
        self,
        schedule_version_id: str,
        user_id: str,
        username: str,
        entity_type: str,
        entity_id: str,
        action: str,
        summary: str,
        data: Optional[Dict] = None
    ):
        """
        Log a change and broadcast it to all connected users.
        """
        self.log_change(
            schedule_version_id, user_id, username,
            entity_type, entity_id, action, summary
        )
        
        await self.broadcast_to_schedule(
            schedule_version_id,
            {
                "type": "entity_changed",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "summary": summary,
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
        )
    
    def get_change_log(
        self,
        schedule_version_id: str,
        limit: int = 50,
        entity_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent changes for a schedule.
        """
        if schedule_version_id not in self.change_logs:
            return []
        
        entries = self.change_logs[schedule_version_id]
        
        if entity_type:
            entries = [e for e in entries if e.entity_type == entity_type]
        
        # Sort by timestamp descending and limit
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        return [{
            "timestamp": e.timestamp.isoformat(),
            "user_id": e.user_id,
            "username": e.username,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "action": e.action,
            "summary": e.summary
        } for e in entries]
    
    def get_connected_count(self, schedule_version_id: str) -> int:
        """Get number of users connected to a schedule."""
        if schedule_version_id in self.schedule_connections:
            return len(self.schedule_connections[schedule_version_id])
        return 0
    
    # =========================================================================
    # Conflict Resolution (Optimistic Locking)
    # =========================================================================
    
    def __init_entity_versions(self):
        """Initialize entity version tracking if not already done."""
        if not hasattr(self, '_entity_versions'):
            # Map: (entity_type, entity_id) -> {version, user_id, timestamp}
            self._entity_versions: Dict[Tuple[str, str], Dict] = {}
    
    def acquire_edit_lock(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
        version: int = 0
    ) -> Dict:
        """
        Attempt to acquire an edit lock on an entity.
        
        Returns:
            {"success": True, "lock_version": n} if lock acquired
            {"success": False, "held_by": user_id, "held_since": timestamp} if already locked
        """
        self.__init_entity_versions()
        key = (entity_type, entity_id)
        
        if key in self._entity_versions:
            existing = self._entity_versions[key]
            # Check if lock is stale (>5 minutes old)
            from datetime import timedelta
            if datetime.utcnow() - existing['timestamp'] > timedelta(minutes=5):
                # Stale lock, allow takeover
                pass
            elif existing['user_id'] != user_id:
                return {
                    "success": False,
                    "held_by": existing['user_id'],
                    "held_since": existing['timestamp'].isoformat()
                }
        
        self._entity_versions[key] = {
            'version': version + 1,
            'user_id': user_id,
            'timestamp': datetime.utcnow()
        }
        
        return {"success": True, "lock_version": version + 1}
    
    def release_edit_lock(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str
    ):
        """Release an edit lock."""
        self.__init_entity_versions()
        key = (entity_type, entity_id)
        
        if key in self._entity_versions:
            if self._entity_versions[key]['user_id'] == user_id:
                del self._entity_versions[key]
    
    def check_version_conflict(
        self,
        entity_type: str,
        entity_id: str,
        client_version: int
    ) -> Dict:
        """
        Check if client's version matches server version.
        
        Returns:
            {"conflict": False} if versions match
            {"conflict": True, "server_version": n, "message": str} if mismatch
        """
        self.__init_entity_versions()
        key = (entity_type, entity_id)
        
        if key not in self._entity_versions:
            return {"conflict": False}
        
        server_version = self._entity_versions[key]['version']
        
        if client_version < server_version:
            return {
                "conflict": True,
                "server_version": server_version,
                "message": f"Entity was modified by another user. Your version: {client_version}, Server version: {server_version}"
            }
        
        return {"conflict": False}
    
    async def notify_concurrent_edit(
        self,
        schedule_version_id: str,
        user_id: str,
        username: str,
        entity_type: str,
        entity_id: str
    ):
        """Warn other users that someone started editing an entity."""
        await self.broadcast_to_schedule(
            schedule_version_id,
            {
                "type": "edit_conflict_warning",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "editing_user_id": user_id,
                "editing_username": username,
                "message": f"{username} is editing this {entity_type}",
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user_id=user_id
        )
    
    def get_entities_locked_by_user(self, user_id: str) -> List[Dict]:
        """Get all entities currently locked by a user."""
        self.__init_entity_versions()
        
        return [
            {"entity_type": k[0], "entity_id": k[1], "version": v['version']}
            for k, v in self._entity_versions.items()
            if v['user_id'] == user_id
        ]
    
    def release_all_user_locks(self, user_id: str):
        """Release all locks held by a user (e.g., on disconnect)."""
        self.__init_entity_versions()
        
        keys_to_remove = [
            k for k, v in self._entity_versions.items()
            if v['user_id'] == user_id
        ]
        for key in keys_to_remove:
            del self._entity_versions[key]


# Global singleton instance
ws_manager = WebSocketManager()
