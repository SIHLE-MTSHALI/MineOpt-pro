"""
Geology Router - API endpoints for geology block data

Provides endpoints for:
- Geology blocks by site
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_resource

router = APIRouter(prefix="/geology", tags=["Geology"])


@router.get("/site/{site_id}/blocks")
def get_geology_blocks(site_id: str, db: Session = Depends(get_db)):
    """Get geology blocks for a site."""
    # Get activity areas which represent mining blocks with geology data
    areas = db.query(models_resource.ActivityArea)\
        .filter(models_resource.ActivityArea.site_id == site_id)\
        .all()
    
    blocks = []
    for area in areas:
        # Extract quality info from slice states if available
        quality_data = {}
        if area.slice_states and len(area.slice_states) > 0:
            first_slice = area.slice_states[0]
            quality_data = first_slice.get("quality_vector", {})
        
        blocks.append({
            "block_id": area.area_id,
            "name": area.name,
            "bench_level": area.bench_level,
            "elevation_rl": area.elevation_rl,
            "geometry": area.geometry,
            "slice_count": area.slice_count,
            "quality": quality_data,
            "priority": area.priority,
            "is_locked": area.is_locked,
            "lock_reason": area.lock_reason
        })
    
    return {"blocks": blocks, "site_id": site_id, "count": len(blocks)}
