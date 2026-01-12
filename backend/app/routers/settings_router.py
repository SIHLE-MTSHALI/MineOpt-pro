"""
Settings Router - API endpoints for site settings

Provides endpoints for:
- GET and PUT site settings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_core
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/settings", tags=["Settings"])


class SiteSettingsUpdate(BaseModel):
    name: Optional[str] = None
    time_zone: Optional[str] = None
    unit_system: Optional[str] = None
    crs_epsg: Optional[int] = None
    crs_name: Optional[str] = None
    default_quality_basis_preferences: Optional[Dict[str, Any]] = None


@router.get("/site/{site_id}")
def get_site_settings(site_id: str, db: Session = Depends(get_db)):
    """Get settings for a site."""
    site = db.query(models_core.Site).filter(models_core.Site.site_id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return {
        "site_id": site.site_id,
        "name": site.name,
        "time_zone": site.time_zone,
        "unit_system": site.unit_system,
        "crs_epsg": site.crs_epsg,
        "crs_name": site.crs_name,
        "crs_wkt": site.crs_wkt,
        "default_quality_basis_preferences": site.default_quality_basis_preferences
    }


@router.put("/site/{site_id}")
def update_site_settings(site_id: str, updates: SiteSettingsUpdate, db: Session = Depends(get_db)):
    """Update settings for a site."""
    site = db.query(models_core.Site).filter(models_core.Site.site_id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(site, key, value)
    
    db.commit()
    db.refresh(site)
    
    return {
        "message": "Settings updated successfully",
        "site_id": site.site_id,
        "name": site.name
    }


# User Preferences Schema
class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = None  # 'dark' or 'light'
    sidebar_collapsed: Optional[bool] = None
    default_site_id: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    date_format: Optional[str] = None
    number_format: Optional[str] = None


# Simple in-memory store for demo (would be database in production)
_user_preferences = {}


@router.get("/preferences")
def get_user_preferences():
    """Get current user preferences."""
    # In production, this would get preferences from database based on auth token
    default_prefs = {
        "theme": "dark",
        "sidebar_collapsed": False,
        "default_site_id": None,
        "notifications_enabled": True,
        "date_format": "DD/MM/YYYY",
        "number_format": "en-US"
    }
    
    # Merge with any stored preferences
    user_id = "default"  # Would come from auth in production
    stored = _user_preferences.get(user_id, {})
    
    return {**default_prefs, **stored}


@router.put("/preferences")
def update_user_preferences(updates: UserPreferencesUpdate):
    """Update current user preferences."""
    user_id = "default"  # Would come from auth in production
    
    update_data = updates.dict(exclude_unset=True)
    
    if user_id not in _user_preferences:
        _user_preferences[user_id] = {}
    
    for key, value in update_data.items():
        if value is not None:
            _user_preferences[user_id][key] = value
    
    return {
        "message": "Preferences updated successfully",
        "preferences": _user_preferences[user_id]
    }

