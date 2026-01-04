from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_core
from ..services.auth_service import AuthService
from ..services.security import (
    session_manager, audit_logger, site_access_checker,
    get_current_user, UserContext
)
from datetime import datetime
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

from pydantic import BaseModel
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    password: str
    email: str = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
def register_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Check existing
    existing = db.query(models_core.User).filter(models_core.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # Handle empty strings for email to allow multiple users without emails (if DB unique constraint allows NULLs)
    email_value = user.email
    if not email_value or not email_value.strip():
        email_value = None

    new_user = models_core.User(
        username=user.username,
        email=email_value,
        password_hash=AuthService.get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Audit log
    audit_logger.log_auth_event(
        "register", user.username, True,
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "User created successfully", "username": new_user.username}


@router.post("/token")
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # 1. Find User (or create default admin if not exists for demo)
    user = db.query(models_core.User).filter(models_core.User.username == form_data.username).first()
    
    if not user:
        if form_data.username == "admin" and form_data.password == "admin":
            # Auto-create admin
            user = models_core.User(
                username="admin", 
                email="admin@mineopt.com",
                password_hash=AuthService.get_password_hash("admin")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            audit_logger.log_auth_event(
                "failed_login", form_data.username, False,
                ip_address=ip_address, details={"reason": "user_not_found"}
            )
            raise HTTPException(status_code=401, detail="Incorrect username or password")
            
    # 2. Verify Password
    if not AuthService.verify_password(form_data.password, user.password_hash):
        audit_logger.log_auth_event(
            "failed_login", form_data.username, False,
            ip_address=ip_address, details={"reason": "invalid_password"}
        )
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # 3. Create Session
    session = session_manager.create_session(user.username, ip_address, user_agent)
    
    # 4. Create Token with session info
    access_token = AuthService.create_access_token(data={
        "sub": user.username,
        "session_id": session.session_id,
        "roles": ["admin"] if user.username == "admin" else ["user"],
        "sites": ["*"]  # In production, query from user_site_access table
    })
    
    # 5. Audit log
    audit_logger.log_auth_event(
        "login", user.username, True,
        ip_address=ip_address, details={"session_id": session.session_id}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "session_id": session.session_id
    }


@router.post("/token/refresh")
def refresh_token(
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    """Refresh access token for an active session."""
    ip_address = request.client.host if request.client else "unknown"
    
    # Validate session is still active
    session = session_manager.validate_session(user.session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Create new token with same session
    new_token = AuthService.create_access_token(data={
        "sub": user.username,
        "session_id": user.session_id,
        "roles": user.roles,
        "sites": user.site_access
    })
    
    audit_logger.log_auth_event(
        "token_refresh", user.username, True,
        ip_address=ip_address
    )
    
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "session_id": user.session_id
    }


@router.post("/logout")
def logout(
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    """Logout - invalidate current session."""
    session_manager.invalidate_session(user.session_id)
    
    audit_logger.log_auth_event(
        "logout", user.username, True,
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "Logged out successfully"}


@router.post("/logout/all")
def logout_all_sessions(
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    """Force logout - invalidate all sessions for current user."""
    session_manager.invalidate_user_sessions(user.user_id)
    
    audit_logger.log_auth_event(
        "force_logout_all", user.username, True,
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "All sessions logged out"}


@router.get("/users/me")
def read_users_me(user: UserContext = Depends(get_current_user)):
    return {
        "username": user.username,
        "email": user.email,
        "roles": user.roles,
        "site_access": user.site_access,
        "session_id": user.session_id,
        "is_admin": user.is_admin
    }


@router.get("/sessions")
def get_user_sessions(user: UserContext = Depends(get_current_user)):
    """Get all active sessions for current user."""
    sessions = session_manager.get_user_sessions(user.user_id)
    
    return {
        "user_id": user.user_id,
        "sessions": [
            {
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "ip_address": s.ip_address,
                "user_agent": s.user_agent[:50] if s.user_agent else "",
                "is_current": s.session_id == user.session_id
            }
            for s in sessions
        ]
    }


@router.delete("/sessions/{session_id}")
def invalidate_session(
    session_id: str,
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    """Invalidate a specific session."""
    # Verify the session belongs to the current user
    sessions = session_manager.get_user_sessions(user.user_id)
    if not any(s.session_id == session_id for s in sessions):
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_manager.invalidate_session(session_id)
    
    audit_logger.log_auth_event(
        "session_invalidated", user.username, True,
        ip_address=request.client.host if request.client else None,
        details={"invalidated_session": session_id}
    )
    
    return {"message": "Session invalidated"}


# =============================================================================
# Audit Log Endpoints (Admin Only)
# =============================================================================

@router.get("/audit")
def get_audit_log(
    user_id: Optional[str] = None,
    site_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    current_user: UserContext = Depends(get_current_user)
):
    """Get audit log entries (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    entries = audit_logger.get_entries(
        user_id=user_id,
        site_id=site_id,
        action=action,
        resource_type=resource_type,
        limit=limit
    )
    
    return {
        "count": len(entries),
        "entries": entries
    }
