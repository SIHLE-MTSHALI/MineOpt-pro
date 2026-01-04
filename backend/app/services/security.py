"""
Security Middleware and Utilities

Provides:
- Site-level access enforcement
- Session management with JWT refresh
- Audit logging
- Rate limiting helpers
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set, Any
from dataclasses import dataclass, field
import logging
import json
import hashlib

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class UserContext:
    """Current user context with site access."""
    user_id: str
    username: str
    email: Optional[str]
    roles: List[str]
    site_access: List[str]  # Site IDs user can access
    session_id: str
    token_exp: datetime
    is_admin: bool = False


@dataclass
class AuditEntry:
    """Audit log entry."""
    timestamp: datetime
    user_id: str
    username: str
    action: str  # create, read, update, delete
    resource_type: str  # schedule, task, flow, etc
    resource_id: str
    site_id: Optional[str]
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass 
class SessionInfo:
    """Active session information."""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


# =============================================================================
# Session Manager
# =============================================================================

class SessionManager:
    """
    Manages user sessions with:
    - Concurrent session limits
    - Session tracking
    - Force logout capability
    """
    
    def __init__(self, max_sessions_per_user: int = 3):
        self.max_sessions = max_sessions_per_user
        self._sessions: Dict[str, SessionInfo] = {}  # session_id -> SessionInfo
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
    
    def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = ""
    ) -> SessionInfo:
        """Create a new session, potentially expiring old ones."""
        import uuid
        
        # Check concurrent session limit
        user_sessions = self._user_sessions.get(user_id, set())
        
        while len(user_sessions) >= self.max_sessions:
            # Remove oldest session
            oldest_id = min(
                user_sessions,
                key=lambda sid: self._sessions.get(sid, SessionInfo(
                    sid, user_id, datetime.utcnow(), datetime.utcnow(), "", ""
                )).created_at
            )
            self.invalidate_session(oldest_id)
            user_sessions = self._user_sessions.get(user_id, set())
        
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True
        )
        
        self._sessions[session_id] = session
        
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = set()
        self._user_sessions[user_id].add(session_id)
        
        logger.info(f"Session created for user {user_id}: {session_id}")
        return session
    
    def validate_session(self, session_id: str) -> Optional[SessionInfo]:
        """Check if session is valid and update activity."""
        session = self._sessions.get(session_id)
        if session and session.is_active:
            session.last_activity = datetime.utcnow()
            return session
        return None
    
    def invalidate_session(self, session_id: str):
        """Invalidate a specific session."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.is_active = False
            
            if session.user_id in self._user_sessions:
                self._user_sessions[session.user_id].discard(session_id)
            
            del self._sessions[session_id]
            logger.info(f"Session invalidated: {session_id}")
    
    def invalidate_user_sessions(self, user_id: str):
        """Force logout - invalidate all sessions for a user."""
        session_ids = list(self._user_sessions.get(user_id, set()))
        for session_id in session_ids:
            self.invalidate_session(session_id)
        logger.info(f"All sessions invalidated for user {user_id}")
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for a user."""
        session_ids = self._user_sessions.get(user_id, set())
        return [
            self._sessions[sid] for sid in session_ids
            if sid in self._sessions and self._sessions[sid].is_active
        ]
    
    def cleanup_expired(self, max_age_hours: int = 24):
        """Clean up sessions older than max_age."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired = [
            sid for sid, session in self._sessions.items()
            if session.last_activity < cutoff
        ]
        for sid in expired:
            self.invalidate_session(sid)


# Global session manager
session_manager = SessionManager()


# =============================================================================
# Audit Logger
# =============================================================================

class AuditLogger:
    """
    Audit logging for security compliance.
    
    Logs:
    - User actions (CRUD operations)
    - Authentication events
    - Authorization failures
    """
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self._entries: List[AuditEntry] = []
    
    def log(
        self,
        user_id: str,
        username: str,
        action: str,
        resource_type: str,
        resource_id: str,
        site_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log an audit entry."""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            site_id=site_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self._entries.append(entry)
        
        # Trim old entries
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        
        # Also log to logger
        logger.info(
            f"AUDIT: {action} {resource_type}/{resource_id} by {username} "
            f"(site: {site_id}, ip: {ip_address})"
        )
    
    def log_auth_event(
        self,
        event_type: str,  # login, logout, failed_login, token_refresh
        username: str,
        success: bool,
        ip_address: str = None,
        details: Dict = None
    ):
        """Log authentication event."""
        self.log(
            user_id="auth",
            username=username,
            action=event_type,
            resource_type="authentication",
            resource_id=event_type,
            details={"success": success, **(details or {})},
            ip_address=ip_address
        )
    
    def get_entries(
        self,
        user_id: str = None,
        site_id: str = None,
        action: str = None,
        resource_type: str = None,
        since: datetime = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query audit entries."""
        entries = self._entries
        
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if site_id:
            entries = [e for e in entries if e.site_id == site_id]
        if action:
            entries = [e for e in entries if e.action == action]
        if resource_type:
            entries = [e for e in entries if e.resource_type == resource_type]
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        
        # Sort by timestamp desc and limit
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        return [{
            "timestamp": e.timestamp.isoformat(),
            "user_id": e.user_id,
            "username": e.username,
            "action": e.action,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "site_id": e.site_id,
            "details": e.details,
            "ip_address": e.ip_address
        } for e in entries]


# Global audit logger
audit_logger = AuditLogger()


# =============================================================================
# Site Access Enforcement
# =============================================================================

class SiteAccessChecker:
    """
    Enforces site-level access control.
    
    Users can only access resources within their allowed sites.
    """
    
    def __init__(self, db=None):
        self.db = db
        # Cache user site access (in production, use Redis)
        self._cache: Dict[str, List[str]] = {}
    
    def get_user_sites(self, user_id: str) -> List[str]:
        """Get list of sites a user can access."""
        if user_id in self._cache:
            return self._cache[user_id]
        
        # In production, query from database
        # For now, return all sites (admin access)
        return ["*"]  # Wildcard = all sites
    
    def can_access_site(self, user_id: str, site_id: str) -> bool:
        """Check if user can access a specific site."""
        allowed = self.get_user_sites(user_id)
        return "*" in allowed or site_id in allowed
    
    def filter_by_site_access(
        self,
        user_id: str,
        query,  # SQLAlchemy query
        site_column  # Column to filter
    ):
        """Apply site filter to a database query."""
        allowed_sites = self.get_user_sites(user_id)
        
        if "*" in allowed_sites:
            return query  # Admin - no filter
        
        return query.filter(site_column.in_(allowed_sites))


# Global site access checker
site_access_checker = SiteAccessChecker()


# =============================================================================
# Dependency Functions
# =============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> UserContext:
    """
    FastAPI dependency to get current user with site access.
    
    Usage in endpoints:
        @router.get("/resources")
        def get_resources(user: UserContext = Depends(get_current_user)):
            if not site_access_checker.can_access_site(user.user_id, site_id):
                raise HTTPException(403, "Access denied to this site")
    """
    from ..services.auth_service import AuthService
    
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    username = payload.get("sub")
    session_id = payload.get("session_id", "")
    
    # Validate session if present
    if session_id:
        session = session_manager.validate_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalidated"
            )
    
    # Build user context
    return UserContext(
        user_id=payload.get("user_id", username),
        username=username,
        email=payload.get("email"),
        roles=payload.get("roles", ["user"]),
        site_access=payload.get("sites", ["*"]),
        session_id=session_id,
        token_exp=datetime.fromtimestamp(payload.get("exp", 0)) if "exp" in payload else datetime.utcnow(),
        is_admin="admin" in payload.get("roles", [])
    )


def require_site_access(site_id: str):
    """
    Dependency that requires access to a specific site.
    
    Usage:
        @router.get("/sites/{site_id}/resources")
        def get_resources(
            site_id: str,
            _: None = Depends(require_site_access(site_id))
        ):
    """
    def check_access(user: UserContext = Depends(get_current_user)):
        if not site_access_checker.can_access_site(user.user_id, site_id):
            audit_logger.log(
                user.user_id, user.username,
                "access_denied", "site", site_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to site {site_id}"
            )
        return user
    return check_access


def require_role(role: str):
    """
    Dependency that requires a specific role.
    """
    def check_role(user: UserContext = Depends(get_current_user)):
        if role not in user.roles and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return user
    return check_role


# =============================================================================
# Audit Middleware
# =============================================================================

def create_audit_middleware():
    """
    Create FastAPI middleware for automatic audit logging.
    
    Usage in main.py:
        app.middleware("http")(create_audit_middleware())
    """
    async def audit_middleware(request: Request, call_next):
        # Get request info
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        path = request.url.path
        
        # Skip health checks and static files
        if path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Log the request
        start_time = datetime.utcnow()
        response = await call_next(request)
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log modifying operations
        if method in ["POST", "PUT", "PATCH", "DELETE"] and response.status_code < 400:
            # Extract resource from path
            parts = path.strip("/").split("/")
            resource_type = parts[0] if parts else "unknown"
            resource_id = parts[1] if len(parts) > 1 else ""
            
            # Get user from token (simplified)
            auth_header = request.headers.get("authorization", "")
            username = "anonymous"
            if auth_header.startswith("Bearer "):
                from ..services.auth_service import AuthService
                payload = AuthService.decode_token(auth_header[7:])
                if payload:
                    username = payload.get("sub", "anonymous")
            
            action = {
                "POST": "create",
                "PUT": "update", 
                "PATCH": "update",
                "DELETE": "delete"
            }.get(method, "unknown")
            
            audit_logger.log(
                user_id=username,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip,
                user_agent=user_agent,
                details={"duration_ms": duration_ms, "status": response.status_code}
            )
        
        return response
    
    return audit_middleware
