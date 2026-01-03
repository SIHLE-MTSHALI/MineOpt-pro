"""
Security Router - API endpoints for security and audit operations

Provides endpoints for:
- Role and permission management
- Audit log queries
- Schedule version history
- Credential management (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.security_service import (
    RBACService, ImmutabilityService, CredentialService,
    Permission, Role, UserContext, credential_service
)
from ..services.audit_service import (
    AuditService, AuditAction, AuditSeverity, audit_service
)
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter(prefix="/security", tags=["Security"])


# =============================================================================
# Pydantic Models
# =============================================================================

class UserContextInput(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    site_ids: List[str] = []


class PermissionCheckInput(BaseModel):
    user_id: str
    username: str
    role: str
    permission: str
    site_id: Optional[str] = None


class ForkVersionInput(BaseModel):
    schedule_version_id: str
    new_name: str
    forked_by: str
    reason: Optional[str] = None


class CredentialInput(BaseModel):
    service_name: str
    credential_type: str
    credential_value: str
    metadata: Optional[Dict] = None


class AuditLogInput(BaseModel):
    user_id: str
    username: str
    action: str
    entity_type: str
    entity_id: str
    entity_name: Optional[str] = None
    changes: Optional[Dict] = None
    reason: Optional[str] = None
    site_id: Optional[str] = None


# =============================================================================
# RBAC Endpoints
# =============================================================================

@router.get("/roles")
def get_all_roles():
    """Get all available roles."""
    return {
        "roles": [
            {"name": role.value, "display_name": role.name.replace("_", " ").title()}
            for role in Role
        ]
    }


@router.get("/permissions")
def get_all_permissions():
    """Get all available permissions."""
    permissions_by_category = {}
    for perm in Permission:
        category = perm.value.split(":")[0]
        if category not in permissions_by_category:
            permissions_by_category[category] = []
        permissions_by_category[category].append({
            "name": perm.value,
            "display_name": perm.name.replace("_", " ").title()
        })
    
    return {"permissions": permissions_by_category}


@router.get("/roles/{role}/permissions")
def get_role_permissions(role: str):
    """Get all permissions for a specific role."""
    try:
        role_enum = Role(role)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Role not found: {role}")
    
    rbac = RBACService()
    permissions = rbac.get_user_permissions(role_enum)
    
    return {
        "role": role,
        "permissions": [p.value for p in permissions],
        "permission_count": len(permissions)
    }


@router.post("/check-permission")
def check_permission(request: PermissionCheckInput, db: Session = Depends(get_db)):
    """Check if a user has a specific permission."""
    rbac = RBACService(db)
    
    try:
        permission = Permission(request.permission)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid permission: {request.permission}")
    
    user = rbac.create_user_context(
        user_id=request.user_id,
        username=request.username,
        email="",
        role=request.role,
        site_ids=[]
    )
    
    has_permission = rbac.check_permission(user, permission)
    has_site_access = rbac.check_site_access(user, request.site_id) if request.site_id else True
    
    return {
        "user_id": request.user_id,
        "permission": request.permission,
        "has_permission": has_permission,
        "has_site_access": has_site_access,
        "allowed": has_permission and has_site_access
    }


# =============================================================================
# Schedule Immutability Endpoints
# =============================================================================

@router.get("/schedule/{schedule_version_id}/editable")
def check_schedule_editable(schedule_version_id: str, db: Session = Depends(get_db)):
    """Check if a schedule version can be edited."""
    service = ImmutabilityService(db)
    editable = service.check_editable(schedule_version_id)
    
    return {
        "schedule_version_id": schedule_version_id,
        "editable": editable,
        "message": "Schedule can be edited" if editable else "Schedule is locked (published or archived)"
    }


@router.post("/schedule/fork")
def fork_schedule_version(request: ForkVersionInput, db: Session = Depends(get_db)):
    """Create a new version by forking an existing schedule."""
    service = ImmutabilityService(db)
    
    # Log the fork action
    audit_service.log(
        user_id=request.forked_by,
        username=request.forked_by,
        action=AuditAction.CREATE,
        entity_type="ScheduleVersion",
        entity_id=request.schedule_version_id,
        entity_name=request.new_name,
        reason=request.reason or "Forked from existing schedule",
        metadata={"source_version": request.schedule_version_id}
    )
    
    new_version_id = service.fork_version(
        request.schedule_version_id,
        request.new_name,
        request.forked_by
    )
    
    return {
        "source_version_id": request.schedule_version_id,
        "new_version_id": new_version_id,
        "new_name": request.new_name,
        "forked_by": request.forked_by
    }


@router.get("/schedule/{schedule_version_id}/history")
def get_version_history(schedule_version_id: str, db: Session = Depends(get_db)):
    """Get version history chain for a schedule."""
    service = ImmutabilityService(db)
    history = service.get_version_history(schedule_version_id)
    
    return {
        "schedule_version_id": schedule_version_id,
        "version_count": len(history),
        "history": history
    }


# =============================================================================
# Audit Log Endpoints
# =============================================================================

@router.post("/audit/log")
def create_audit_log(entry: AuditLogInput):
    """Create a manual audit log entry."""
    try:
        action = AuditAction(entry.action)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid action: {entry.action}")
    
    log_id = audit_service.log(
        user_id=entry.user_id,
        username=entry.username,
        action=action,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        entity_name=entry.entity_name,
        changes=entry.changes,
        reason=entry.reason,
        site_id=entry.site_id
    )
    
    return {"log_id": log_id, "status": "logged"}


@router.get("/audit/logs")
def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    site_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Query audit logs with filters."""
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AuditSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    logs = audit_service.get_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        action=action_enum,
        site_id=site_id,
        severity=severity_enum,
        limit=limit,
        offset=offset
    )
    
    return {
        "count": len(logs),
        "offset": offset,
        "limit": limit,
        "logs": logs
    }


@router.get("/audit/entity/{entity_type}/{entity_id}")
def get_entity_history(entity_type: str, entity_id: str, limit: int = 50):
    """Get complete change history for a specific entity."""
    history = audit_service.get_entity_history(entity_type, entity_id, limit)
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "change_count": len(history),
        "history": history
    }


@router.get("/audit/user/{user_id}")
def get_user_activity(user_id: str, limit: int = 100):
    """Get activity history for a specific user."""
    activity = audit_service.get_user_activity(user_id, limit=limit)
    
    return {
        "user_id": user_id,
        "activity_count": len(activity),
        "activity": activity
    }


@router.get("/audit/recent")
def get_recent_changes(site_id: Optional[str] = None, limit: int = 50):
    """Get most recent changes."""
    changes = audit_service.get_recent_changes(site_id=site_id, limit=limit)
    
    return {
        "count": len(changes),
        "changes": changes
    }


@router.get("/audit/critical")
def get_critical_events(limit: int = 100):
    """Get critical and warning severity events."""
    events = audit_service.get_critical_events(limit=limit)
    
    return {
        "count": len(events),
        "events": events
    }


@router.get("/audit/statistics")
def get_audit_statistics(site_id: Optional[str] = None):
    """Get audit log statistics."""
    stats = audit_service.get_statistics(site_id=site_id)
    
    return stats


# =============================================================================
# Credential Management Endpoints (Admin Only)
# =============================================================================

@router.post("/credentials")
def store_credential(request: CredentialInput):
    """Store a new credential (admin only)."""
    credential_id = credential_service.store_credential(
        service_name=request.service_name,
        credential_type=request.credential_type,
        credential_value=request.credential_value,
        metadata=request.metadata
    )
    
    # Audit the credential creation (without logging the value)
    audit_service.log(
        user_id="system",
        username="system",
        action=AuditAction.CREATE,
        entity_type="Credential",
        entity_id=credential_id,
        entity_name=f"{request.service_name}:{request.credential_type}",
        severity=AuditSeverity.CRITICAL
    )
    
    return {
        "credential_id": credential_id,
        "service_name": request.service_name,
        "credential_type": request.credential_type
    }


@router.get("/credentials")
def list_credentials():
    """List all stored credentials (without values)."""
    credentials = credential_service.list_credentials()
    
    return {
        "count": len(credentials),
        "credentials": credentials
    }


@router.delete("/credentials/{credential_id}")
def delete_credential(credential_id: str):
    """Delete a stored credential (admin only)."""
    success = credential_service.delete_credential(credential_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Audit the deletion
    audit_service.log(
        user_id="system",
        username="system",
        action=AuditAction.DELETE,
        entity_type="Credential",
        entity_id=credential_id,
        severity=AuditSeverity.CRITICAL
    )
    
    return {"status": "deleted", "credential_id": credential_id}
