from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, engine, Base
from ..domain import models_core, models_calendar, models_resource, models_flow, models_scheduling
# from ..schemas import site_schemas
from ..services import seed_service

# Note: Database tables are now created in main.py lifespan


router = APIRouter(prefix="/config", tags=["Configuration"])

@router.post("/seed-demo-data")
def seed_data(db: Session = Depends(get_db)):
    result = seed_service.seed_enterprise_data(db)
    # Result is now {"site_id": x, "version_id": y}
    return {
        "message": "Enterprise Demo data seeded", 
        "site": {"name": "Enterprise Coal Mine", "site_id": result["site_id"]},
        "version": {"version_id": result["version_id"]}
    }


@router.post("/seed-comprehensive-demo")
def seed_comprehensive_data(db: Session = Depends(get_db)):
    """
    Seed comprehensive demo data with 3 coal mining sites,
    50+ equipment pieces, and 90 days of historical data.
    
    This creates realistic operational data for full app demonstration.
    """
    from ..services import comprehensive_seed_service
    result = comprehensive_seed_service.seed_all(db)
    return {
        "message": "Comprehensive demo data seeded successfully",
        **result
    }

@router.get("/sites")
def get_sites(db: Session = Depends(get_db)):
    return db.query(models_core.Site).all()

@router.get("/resources")
def get_resources(site_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models_resource.Resource)
    if site_id:
        query = query.filter(models_resource.Resource.site_id == site_id)
    return query.all()

@router.get("/activity-areas")
def get_activity_areas(site_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models_resource.ActivityArea)
    if site_id:
        query = query.filter(models_resource.ActivityArea.site_id == site_id)
    return query.all()

@router.get("/network-nodes")
def get_network_nodes(site_id: str = None, db: Session = Depends(get_db)):
    # Join Network to filter by Site
    query = db.query(models_flow.FlowNode).join(models_flow.FlowNetwork)
    if site_id:
        query = query.filter(models_flow.FlowNetwork.site_id == site_id)
    
    # Eager load configs
    # We rely on lazy loading default or simple JSON serialization
    return query.all()


# =============================================================================
# Additional Site Endpoints (Alias routes for frontend compatibility)
# =============================================================================

@router.get("/washplant/site/{site_id}")
def get_washplant_config(site_id: str, db: Session = Depends(get_db)):
    """Get wash plant configuration for a site."""
    # Get wash plant nodes (FlowNodes with type 'WashPlant')
    nodes = db.query(models_flow.FlowNode)\
        .join(models_flow.FlowNetwork)\
        .filter(models_flow.FlowNetwork.site_id == site_id)\
        .filter(models_flow.FlowNode.node_type == "WashPlant")\
        .all()
    
    result = []
    for node in nodes:
        result.append({
            "node_id": node.node_id,
            "name": node.name,
            "node_type": node.node_type,
            "capacity_tonnes_per_hour": node.capacity_tonnes_per_hour,
            "wash_plant_config": node.wash_plant_config.__dict__ if node.wash_plant_config else None
        })
    
    return {"wash_plants": result, "site_id": site_id}


@router.get("/geology/site/{site_id}/blocks")
def get_geology_blocks(site_id: str, db: Session = Depends(get_db)):
    """Get geology blocks for a site."""
    # Get activity areas which represent mining blocks with geology data
    areas = db.query(models_resource.ActivityArea)\
        .filter(models_resource.ActivityArea.site_id == site_id)\
        .all()
    
    blocks = []
    for area in areas:
        blocks.append({
            "block_id": area.area_id,
            "name": area.name,
            "bench_level": area.bench_level,
            "elevation_rl": area.elevation_rl,
            "geometry": area.geometry,
            "slice_states": area.slice_states,
            "priority": area.priority,
            "is_locked": area.is_locked
        })
    
    return {"blocks": blocks, "site_id": site_id, "count": len(blocks)}


@router.get("/settings/site/{site_id}")
def get_site_settings(site_id: str, db: Session = Depends(get_db)):
    """Get settings for a site."""
    site = db.query(models_core.Site).filter(models_core.Site.site_id == site_id).first()
    if not site:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Site not found")
    
    return {
        "site_id": site.site_id,
        "name": site.name,
        "time_zone": site.time_zone,
        "unit_system": site.unit_system,
        "crs_epsg": site.crs_epsg,
        "crs_name": site.crs_name,
        "default_quality_basis_preferences": site.default_quality_basis_preferences
    }


from pydantic import BaseModel
from typing import Optional, Dict, Any

class SiteSettingsUpdate(BaseModel):
    name: Optional[str] = None
    time_zone: Optional[str] = None
    unit_system: Optional[str] = None
    crs_epsg: Optional[int] = None
    crs_name: Optional[str] = None
    default_quality_basis_preferences: Optional[Dict[str, Any]] = None


@router.put("/settings/site/{site_id}")
def update_site_settings(site_id: str, updates: SiteSettingsUpdate, db: Session = Depends(get_db)):
    """Update settings for a site."""
    from fastapi import HTTPException
    
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
        "message": "Settings updated",
        "site_id": site.site_id,
        "name": site.name
    }


@router.get("/resources/maintenance")
def get_resources_maintenance(site_id: str = None, db: Session = Depends(get_db)):
    """Get maintenance schedule for resources."""
    query = db.query(models_resource.Resource)
    if site_id:
        query = query.filter(models_resource.Resource.site_id == site_id)
    
    resources = query.all()
    
    # Build maintenance schedule (placeholder - in production this would come from a maintenance table)
    maintenance = []
    for r in resources:
        maintenance.append({
            "resource_id": r.resource_id,
            "resource_name": r.name,
            "resource_type": r.resource_type,
            "next_scheduled_maintenance": None,
            "maintenance_status": "operational",
            "notes": None
        })
    
    return {"maintenance_schedule": maintenance, "count": len(maintenance)}
