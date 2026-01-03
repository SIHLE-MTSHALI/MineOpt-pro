"""
Audit Service - Section 4.10 of Enterprise Specification

Comprehensive audit logging service providing:
- Entity change tracking
- User attribution
- Reason capture for edits
- Change history API
- Compliance reporting
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid
import json


# =============================================================================
# Audit Action Types
# =============================================================================

class AuditAction(str, Enum):
    """Types of auditable actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    IMPORT = "import"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"
    CONFIGURATION_CHANGE = "configuration_change"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =============================================================================
# Audit Log Entry
# =============================================================================

@dataclass
class AuditLogEntry:
    """Audit log entry data structure."""
    log_id: str
    timestamp: datetime
    user_id: str
    username: str
    action: AuditAction
    entity_type: str
    entity_id: str
    entity_name: Optional[str]
    changes: Optional[Dict]
    previous_values: Optional[Dict]
    new_values: Optional[Dict]
    reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    site_id: Optional[str]
    severity: AuditSeverity
    metadata: Optional[Dict]


# =============================================================================
# Audit Service
# =============================================================================

class AuditService:
    """
    Comprehensive audit logging service.
    
    Tracks all entity changes with user attribution and
    provides change history API for compliance.
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        # In-memory storage for demo; production uses database
        self._logs: List[AuditLogEntry] = []
    
    def log(
        self,
        user_id: str,
        username: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        entity_name: str = None,
        changes: Dict = None,
        previous_values: Dict = None,
        new_values: Dict = None,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None,
        site_id: str = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: Dict = None
    ) -> str:
        """
        Create an audit log entry.
        
        Args:
            user_id: ID of user performing the action
            username: Username for display
            action: Type of action performed
            entity_type: Type of entity affected
            entity_id: ID of affected entity
            entity_name: Optional human-readable entity name
            changes: Summary of changes made
            previous_values: Values before the change
            new_values: Values after the change
            reason: Optional reason for the change
            ip_address: Client IP address
            user_agent: Client user agent
            site_id: Site scope
            severity: Log severity level
            metadata: Additional metadata
            
        Returns:
            Audit log ID
        """
        log_entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=changes,
            previous_values=previous_values,
            new_values=new_values,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            site_id=site_id,
            severity=severity,
            metadata=metadata
        )
        
        self._logs.append(log_entry)
        
        # In production, persist to database
        # self._persist_to_db(log_entry)
        
        return log_entry.log_id
    
    def log_create(
        self,
        user_id: str,
        username: str,
        entity_type: str,
        entity_id: str,
        entity_data: Dict,
        entity_name: str = None,
        site_id: str = None,
        reason: str = None
    ) -> str:
        """Log a create action."""
        return self.log(
            user_id=user_id,
            username=username,
            action=AuditAction.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            new_values=entity_data,
            site_id=site_id,
            reason=reason
        )
    
    def log_update(
        self,
        user_id: str,
        username: str,
        entity_type: str,
        entity_id: str,
        previous_values: Dict,
        new_values: Dict,
        entity_name: str = None,
        site_id: str = None,
        reason: str = None
    ) -> str:
        """Log an update action with before/after values."""
        # Calculate changes
        changes = {}
        for key in set(list(previous_values.keys()) + list(new_values.keys())):
            old_val = previous_values.get(key)
            new_val = new_values.get(key)
            if old_val != new_val:
                changes[key] = {"from": old_val, "to": new_val}
        
        return self.log(
            user_id=user_id,
            username=username,
            action=AuditAction.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=changes,
            previous_values=previous_values,
            new_values=new_values,
            site_id=site_id,
            reason=reason
        )
    
    def log_delete(
        self,
        user_id: str,
        username: str,
        entity_type: str,
        entity_id: str,
        entity_data: Dict,
        entity_name: str = None,
        site_id: str = None,
        reason: str = None
    ) -> str:
        """Log a delete action."""
        return self.log(
            user_id=user_id,
            username=username,
            action=AuditAction.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            previous_values=entity_data,
            site_id=site_id,
            reason=reason,
            severity=AuditSeverity.WARNING
        )
    
    def log_publish(
        self,
        user_id: str,
        username: str,
        schedule_id: str,
        schedule_name: str,
        site_id: str = None,
        reason: str = None
    ) -> str:
        """Log a schedule publish action."""
        return self.log(
            user_id=user_id,
            username=username,
            action=AuditAction.PUBLISH,
            entity_type="ScheduleVersion",
            entity_id=schedule_id,
            entity_name=schedule_name,
            site_id=site_id,
            reason=reason,
            severity=AuditSeverity.CRITICAL
        )
    
    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------
    
    def get_logs(
        self,
        entity_type: str = None,
        entity_id: str = None,
        user_id: str = None,
        action: AuditAction = None,
        site_id: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
        severity: AuditSeverity = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Query audit logs with filters.
        
        Args:
            entity_type: Filter by entity type
            entity_id: Filter by specific entity
            user_id: Filter by user
            action: Filter by action type
            site_id: Filter by site
            from_date: Start date filter
            to_date: End date filter
            severity: Filter by severity
            limit: Maximum records to return
            offset: Records to skip
            
        Returns:
            List of matching audit log entries
        """
        results = self._logs
        
        if entity_type:
            results = [r for r in results if r.entity_type == entity_type]
        
        if entity_id:
            results = [r for r in results if r.entity_id == entity_id]
        
        if user_id:
            results = [r for r in results if r.user_id == user_id]
        
        if action:
            results = [r for r in results if r.action == action]
        
        if site_id:
            results = [r for r in results if r.site_id == site_id]
        
        if from_date:
            results = [r for r in results if r.timestamp >= from_date]
        
        if to_date:
            results = [r for r in results if r.timestamp <= to_date]
        
        if severity:
            results = [r for r in results if r.severity == severity]
        
        # Sort by timestamp descending
        results = sorted(results, key=lambda r: r.timestamp, reverse=True)
        
        # Apply pagination
        results = results[offset:offset + limit]
        
        return [self._entry_to_dict(r) for r in results]
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get complete change history for a specific entity."""
        return self.get_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )
    
    def get_user_activity(
        self,
        user_id: str,
        from_date: datetime = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get activity history for a specific user."""
        return self.get_logs(
            user_id=user_id,
            from_date=from_date,
            limit=limit
        )
    
    def get_recent_changes(
        self,
        site_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get most recent changes across all entities."""
        return self.get_logs(
            site_id=site_id,
            limit=limit
        )
    
    def get_critical_events(
        self,
        from_date: datetime = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get critical and warning severity events."""
        critical = self.get_logs(
            severity=AuditSeverity.CRITICAL,
            from_date=from_date,
            limit=limit
        )
        warnings = self.get_logs(
            severity=AuditSeverity.WARNING,
            from_date=from_date,
            limit=limit
        )
        
        combined = critical + warnings
        combined = sorted(combined, key=lambda r: r['timestamp'], reverse=True)
        return combined[:limit]
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def get_statistics(
        self,
        site_id: str = None,
        from_date: datetime = None
    ) -> Dict:
        """Get audit log statistics."""
        logs = self._logs
        
        if site_id:
            logs = [l for l in logs if l.site_id == site_id]
        
        if from_date:
            logs = [l for l in logs if l.timestamp >= from_date]
        
        action_counts = {}
        for action in AuditAction:
            action_counts[action.value] = len([l for l in logs if l.action == action])
        
        entity_counts = {}
        for log in logs:
            entity_counts[log.entity_type] = entity_counts.get(log.entity_type, 0) + 1
        
        user_counts = {}
        for log in logs:
            user_counts[log.username] = user_counts.get(log.username, 0) + 1
        
        return {
            "total_entries": len(logs),
            "by_action": action_counts,
            "by_entity_type": entity_counts,
            "by_user": dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "critical_count": len([l for l in logs if l.severity == AuditSeverity.CRITICAL]),
            "warning_count": len([l for l in logs if l.severity == AuditSeverity.WARNING])
        }
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    def _entry_to_dict(self, entry: AuditLogEntry) -> Dict:
        """Convert audit log entry to dictionary."""
        result = asdict(entry)
        result['timestamp'] = entry.timestamp.isoformat()
        result['action'] = entry.action.value
        result['severity'] = entry.severity.value
        return result


# =============================================================================
# Global Audit Service Instance
# =============================================================================

audit_service = AuditService()


# =============================================================================
# Audit Decorator for Routes
# =============================================================================

def audited(
    action: AuditAction,
    entity_type: str,
    get_entity_id: callable = None
):
    """
    Decorator to automatically audit route calls.
    
    Usage:
        @audited(AuditAction.CREATE, "ScheduleVersion")
        async def create_schedule(...):
            ...
    """
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Log the action
            request = kwargs.get('request')
            user = getattr(request.state, 'user', None) if request else None
            
            entity_id = "unknown"
            if get_entity_id and result:
                try:
                    entity_id = get_entity_id(result)
                except:
                    pass
            
            audit_service.log(
                user_id=user.user_id if user else "anonymous",
                username=user.username if user else "anonymous",
                action=action,
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            return result
        return wrapper
    return decorator
