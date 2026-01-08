"""
Resources Router - API endpoints for resource management

Provides endpoints for:
- Resource maintenance schedules
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_resource

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/maintenance")
def get_resources_maintenance(site_id: str = None, db: Session = Depends(get_db)):
    """Get maintenance schedule for resources."""
    query = db.query(models_resource.Resource)
    if site_id:
        query = query.filter(models_resource.Resource.site_id == site_id)
    
    resources = query.all()
    
    # Build maintenance schedule
    maintenance = []
    for r in resources:
        maintenance.append({
            "resource_id": r.resource_id,
            "resource_name": r.name,
            "resource_type": r.resource_type,
            "base_rate": r.base_rate,
            "next_scheduled_maintenance": None,
            "maintenance_status": "operational",
            "availability": 1.0,
            "notes": None
        })
    
    return {"maintenance_schedule": maintenance, "count": len(maintenance)}
