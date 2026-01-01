from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_flow, models_resource
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter(prefix="/stockpiles", tags=["Stockpiles"])

class StockpileState(BaseModel):
    node_id: str
    name: str
    current_tonnage: float
    current_grade: Dict[str, float]
    capacity_tonnes: Optional[float]

class DumpPayload(BaseModel):
    quantity: float
    # Quality Vector: {"CV_ARB": 20.0, "Ash_ADB": 15.0}
    quality: Dict[str, float]

@router.get("", response_model=List[StockpileState])
def get_stockpiles(site_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models_flow.FlowNode).filter(models_flow.FlowNode.node_type == "Stockpile")
    
    if site_id:
        query = query.join(models_flow.FlowNetwork).filter(models_flow.FlowNetwork.site_id == site_id)
        
    nodes = query.all()
    results = []
    
    for n in nodes:
        # Check if config exists, if not create default (or skip)
        # For this demo, we assume seed service created configs
        config = n.stockpile_config
        
        current_tons = 0.0
        current_grade = {}
        
        if config:
            current_tons = config.current_inventory_tonnes or 0.0
            current_grade = config.current_grade_vector or {}
            
        results.append(StockpileState(
            node_id=n.node_id,
            name=n.name,
            current_tonnage=current_tons,
            current_grade=current_grade,
            capacity_tonnes=config.max_capacity_tonnes if config else None
        ))
        
    return results

@router.post("/{node_id}/dump")
def dump_material(node_id: str, payload: DumpPayload, db: Session = Depends(get_db)):
    # 1. Fetch Node & Config
    node = db.query(models_flow.FlowNode).filter(models_flow.FlowNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Stockpile not found")
    
    if node.node_type != "Stockpile":
        raise HTTPException(status_code=400, detail="Target node is not a stockpile")
        
    config = node.stockpile_config
    if not config:
        # Auto-create config if missing (Robustness)
        config = models_flow.StockpileConfig(node_id=node.node_id)
        db.add(config)
        db.flush()
        
    # 2. Weighted Average Calculation
    current_tons = config.current_inventory_tonnes or 0.0
    current_grade = config.current_grade_vector or {}
    
    new_tons = payload.quantity
    new_grade = payload.quality
    
    total_tons = current_tons + new_tons
    
    updated_grade = {}
    
    if total_tons > 0:
        # Union of all quality keys
        all_keys = set(current_grade.keys()) | set(new_grade.keys())
        
        for key in all_keys:
            c_val = current_grade.get(key, 0.0)
            n_val = new_grade.get(key, 0.0)
            
            # Weighted Avg Formula: (M1*Q1 + M2*Q2) / (M1+M2)
            avg = ((current_tons * c_val) + (new_tons * n_val)) / total_tons
            updated_grade[key] = round(avg, 4)
    else:
        updated_grade = {}
        
    # 3. Update State
    config.current_inventory_tonnes = total_tons
    config.current_grade_vector = updated_grade
    
    db.commit()
    db.refresh(config)
    
    return {
        "node_id": node.node_id,
        "current_tonnage": config.current_inventory_tonnes,
        "current_grade": config.current_grade_vector
    }
