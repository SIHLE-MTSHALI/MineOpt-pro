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
