"""
Security Service - Section 4.10 of Enterprise Specification

Comprehensive security service providing:
- Role-Based Access Control (RBAC)
- Permission definitions
- Route protection utilities
- Site-level access scoping
- Schedule immutability enforcement
"""

from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException, Request, Depends
from functools import wraps
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


# =============================================================================
# Permission Definitions
# =============================================================================

class Permission(str, Enum):
    """System permission definitions."""
    # Read permissions
    VIEW_SCHEDULE = "view:schedule"
    VIEW_RESOURCES = "view:resources"
    VIEW_STOCKPILES = "view:stockpiles"
    VIEW_REPORTS = "view:reports"
    VIEW_QUALITY = "view:quality"
    VIEW_FLOW_NETWORK = "view:flow_network"
    
    # Write permissions
    EDIT_SCHEDULE = "edit:schedule"
    EDIT_RESOURCES = "edit:resources"
    EDIT_STOCKPILES = "edit:stockpiles"
    EDIT_QUALITY = "edit:quality"
    EDIT_FLOW_NETWORK = "edit:flow_network"
    
    # Execution permissions
    RUN_OPTIMIZATION = "run:optimization"
    PUBLISH_SCHEDULE = "publish:schedule"
    IMPORT_DATA = "import:data"
    EXPORT_DATA = "export:data"
    
    # Admin permissions
    MANAGE_USERS = "admin:users"
    MANAGE_SITES = "admin:sites"
    MANAGE_SETTINGS = "admin:settings"
    VIEW_AUDIT_LOG = "admin:audit"


class Role(str, Enum):
    """System role definitions."""
    VIEWER = "viewer"
    PLANNER = "planner"
    SENIOR_PLANNER = "senior_planner"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.VIEW_SCHEDULE,
        Permission.VIEW_RESOURCES,
        Permission.VIEW_STOCKPILES,
        Permission.VIEW_REPORTS,
        Permission.VIEW_QUALITY,
    },
    Role.PLANNER: {
        Permission.VIEW_SCHEDULE,
        Permission.VIEW_RESOURCES,
        Permission.VIEW_STOCKPILES,
        Permission.VIEW_REPORTS,
        Permission.VIEW_QUALITY,
        Permission.VIEW_FLOW_NETWORK,
        Permission.EDIT_SCHEDULE,
        Permission.RUN_OPTIMIZATION,
    },
    Role.SENIOR_PLANNER: {
        Permission.VIEW_SCHEDULE,
        Permission.VIEW_RESOURCES,
        Permission.VIEW_STOCKPILES,
        Permission.VIEW_REPORTS,
        Permission.VIEW_QUALITY,
        Permission.VIEW_FLOW_NETWORK,
        Permission.EDIT_SCHEDULE,
        Permission.EDIT_RESOURCES,
        Permission.EDIT_STOCKPILES,
        Permission.EDIT_QUALITY,
        Permission.EDIT_FLOW_NETWORK,
        Permission.RUN_OPTIMIZATION,
        Permission.PUBLISH_SCHEDULE,
        Permission.EXPORT_DATA,
    },
    Role.SUPERVISOR: {
        Permission.VIEW_SCHEDULE,
        Permission.VIEW_RESOURCES,
        Permission.VIEW_STOCKPILES,
        Permission.VIEW_REPORTS,
        Permission.VIEW_QUALITY,
        Permission.VIEW_FLOW_NETWORK,
        Permission.PUBLISH_SCHEDULE,
        Permission.EXPORT_DATA,
        Permission.VIEW_AUDIT_LOG,
    },
    Role.ADMIN: {
        # All permissions except super admin
        p for p in Permission if p != Permission.MANAGE_SITES
    },
    Role.SUPER_ADMIN: {
        p for p in Permission  # All permissions
    }
}


@dataclass
class UserContext:
    """Current user context for authorization."""
    user_id: str
    username: str
    email: str
    role: Role
    site_ids: List[str]  # Sites user has access to
    permissions: Set[Permission]
    is_active: bool = True


# =============================================================================
# RBAC Service
# =============================================================================

class RBACService:
    """Role-Based Access Control service."""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def get_user_permissions(self, role: Role) -> Set[Permission]:
        """Get all permissions for a role."""
        return ROLE_PERMISSIONS.get(role, set())
    
    def check_permission(
        self, 
        user: UserContext, 
        required_permission: Permission
    ) -> bool:
        """Check if user has a specific permission."""
        if not user.is_active:
            return False
        return required_permission in user.permissions
    
    def check_any_permission(
        self, 
        user: UserContext, 
        permissions: List[Permission]
    ) -> bool:
        """Check if user has any of the specified permissions."""
        if not user.is_active:
            return False
        return any(p in user.permissions for p in permissions)
    
    def check_all_permissions(
        self, 
        user: UserContext, 
        permissions: List[Permission]
    ) -> bool:
        """Check if user has all specified permissions."""
        if not user.is_active:
            return False
        return all(p in user.permissions for p in permissions)
    
    def check_site_access(
        self, 
        user: UserContext, 
        site_id: str
    ) -> bool:
        """Check if user has access to a specific site."""
        if user.role == Role.SUPER_ADMIN:
            return True
        return site_id in user.site_ids
    
    def enforce_permission(
        self, 
        user: UserContext, 
        required_permission: Permission,
        site_id: str = None
    ) -> None:
        """Enforce permission check, raise HTTPException if denied."""
        if not self.check_permission(user, required_permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {required_permission.value} required"
            )
        
        if site_id and not self.check_site_access(user, site_id):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied for site: {site_id}"
            )
    
    def create_user_context(
        self,
        user_id: str,
        username: str,
        email: str,
        role: str,
        site_ids: List[str] = None
    ) -> UserContext:
        """Create a user context object."""
        role_enum = Role(role) if role in [r.value for r in Role] else Role.VIEWER
        permissions = self.get_user_permissions(role_enum)
        
        return UserContext(
            user_id=user_id,
            username=username,
            email=email,
            role=role_enum,
            site_ids=site_ids or [],
            permissions=permissions
        )


# =============================================================================
# Schedule Immutability Service
# =============================================================================

class ImmutabilityService:
    """Enforces schedule immutability after publishing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_editable(self, schedule_version_id: str) -> bool:
        """Check if a schedule version can be edited."""
        from ..domain.models_scheduling import ScheduleVersion
        
        schedule = self.db.query(ScheduleVersion)\
            .filter(ScheduleVersion.version_id == schedule_version_id)\
            .first()
        
        if not schedule:
            return False
        
        # Published or archived schedules cannot be edited
        return schedule.status not in ['Published', 'Archived']
    
    def enforce_editable(self, schedule_version_id: str) -> None:
        """Enforce that schedule is editable, raise exception if not."""
        if not self.check_editable(schedule_version_id):
            raise HTTPException(
                status_code=403,
                detail="Cannot edit published or archived schedule. Create a new version instead."
            )
    
    def fork_version(
        self, 
        schedule_version_id: str, 
        new_name: str,
        forked_by: str
    ) -> str:
        """Create a new version by forking a published schedule."""
        from ..domain.models_scheduling import ScheduleVersion, Task
        import uuid
        
        original = self.db.query(ScheduleVersion)\
            .filter(ScheduleVersion.version_id == schedule_version_id)\
            .first()
        
        if not original:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Create new version
        new_version = ScheduleVersion(
            version_id=str(uuid.uuid4()),
            name=new_name,
            description=f"Forked from {original.name}",
            status="Draft",
            created_by=forked_by,
            parent_version_id=schedule_version_id
        )
        self.db.add(new_version)
        
        # Copy tasks
        original_tasks = self.db.query(Task)\
            .filter(Task.schedule_version_id == schedule_version_id)\
            .all()
        
        for task in original_tasks:
            new_task = Task(
                task_id=str(uuid.uuid4()),
                schedule_version_id=new_version.version_id,
                period_id=task.period_id,
                resource_id=task.resource_id,
                activity_area_id=task.activity_area_id,
                activity_name=task.activity_name,
                destination_node_id=task.destination_node_id,
                planned_quantity=task.planned_quantity,
                quantity_tonnes=task.quantity_tonnes,
                duration_hours=task.duration_hours,
                start_offset_hours=task.start_offset_hours
            )
            self.db.add(new_task)
        
        self.db.commit()
        
        return new_version.version_id
    
    def get_version_history(self, schedule_version_id: str) -> List[Dict]:
        """Get version history chain."""
        from ..domain.models_scheduling import ScheduleVersion
        
        history = []
        current_id = schedule_version_id
        
        while current_id:
            version = self.db.query(ScheduleVersion)\
                .filter(ScheduleVersion.version_id == current_id)\
                .first()
            
            if not version:
                break
            
            history.append({
                "version_id": version.version_id,
                "name": version.name,
                "status": version.status,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "created_by": version.created_by,
                "published_at": version.published_at.isoformat() if hasattr(version, 'published_at') and version.published_at else None
            })
            
            current_id = getattr(version, 'parent_version_id', None)
        
        return history


# =============================================================================
# Credential Storage Service
# =============================================================================

class CredentialService:
    """Secure credential storage and management."""
    
    def __init__(self):
        # In production, use proper secrets management (Vault, AWS Secrets, etc.)
        self._credentials: Dict[str, Dict] = {}
    
    def store_credential(
        self,
        service_name: str,
        credential_type: str,
        credential_value: str,
        metadata: Dict = None
    ) -> str:
        """Store a credential securely."""
        import hashlib
        
        credential_id = hashlib.sha256(
            f"{service_name}:{credential_type}".encode()
        ).hexdigest()[:16]
        
        self._credentials[credential_id] = {
            "service_name": service_name,
            "credential_type": credential_type,
            "value": credential_value,  # In production: encrypt this
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        return credential_id
    
    def get_credential(self, credential_id: str) -> Optional[str]:
        """Retrieve a credential value."""
        cred = self._credentials.get(credential_id)
        if cred:
            return cred["value"]
        return None
    
    def list_credentials(self) -> List[Dict]:
        """List credentials (without values)."""
        return [
            {
                "credential_id": cid,
                "service_name": c["service_name"],
                "credential_type": c["credential_type"],
                "created_at": c["created_at"]
            }
            for cid, c in self._credentials.items()
        ]
    
    def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential."""
        if credential_id in self._credentials:
            del self._credentials[credential_id]
            return True
        return False


# =============================================================================
# Route Protection Utilities
# =============================================================================

def require_permission(permission: Permission):
    """Decorator to require a specific permission for a route."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user context from request (would be set by auth middleware)
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            user = getattr(request.state, 'user', None) if request else None
            
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            rbac = RBACService()
            rbac.enforce_permission(user, permission)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            user = getattr(request.state, 'user', None) if request else None
            
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            rbac = RBACService()
            if not rbac.check_any_permission(user, permissions):
                raise HTTPException(
                    status_code=403,
                    detail=f"One of these permissions required: {[p.value for p in permissions]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Singleton Instances
# =============================================================================

credential_service = CredentialService()
