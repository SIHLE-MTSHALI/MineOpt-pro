"""
Washplant Router - API endpoints for wash plant configuration

Provides endpoints for:
- Wash plant configuration by site
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_flow

router = APIRouter(prefix="/washplant", tags=["Wash Plant"])


@router.get("/site/{site_id}")
def get_washplant_by_site(site_id: str, db: Session = Depends(get_db)):
    """Get wash plant configuration for a site."""
    # Get wash plant nodes (FlowNodes with type 'WashPlant' or 'Processor')
    nodes = db.query(models_flow.FlowNode)\
        .join(models_flow.FlowNetwork)\
        .filter(models_flow.FlowNetwork.site_id == site_id)\
        .filter(models_flow.FlowNode.node_type.in_(["WashPlant", "Processor"]))\
        .all()
    
    result = []
    for node in nodes:
        config = None
        if node.wash_plant_config:
            config = {
                "wash_plant_id": node.wash_plant_config.config_id,
                "capacity_tph": node.wash_plant_config.feed_capacity_tph,
                "yield_fraction": node.wash_plant_config.yield_adjustment_factor
            }
        
        result.append({
            "node_id": node.node_id,
            "name": node.name,
            "node_type": node.node_type,
            "capacity_tonnes_per_hour": node.wash_plant_config.feed_capacity_tph if node.wash_plant_config else 0,
            "wash_plant_config": config
        })
    
    return {"wash_plants": result, "site_id": site_id, "count": len(result)}
