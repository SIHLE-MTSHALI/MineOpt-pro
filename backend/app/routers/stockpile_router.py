from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_flow
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/stockpiles", tags=["Stockpiles"])

class StockpileState(BaseModel):
    node_id: str
    name: str
    current_tonnage: float
    current_grade: float
    capacity_tonnes: Optional[float]

class DumpPayload(BaseModel):
    quantity: float
    grade: float

@router.get("", response_model=List[StockpileState])
def get_stockpiles(site_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models_flow.FlowNode).filter(models_flow.FlowNode.node_type == "Stockpile")
    # In a real app we would join network -> site to filter by site_id, but for simple MVP assuming one site/network or no filter is fine
    # But let's try to be correct if site_id is provided
    if site_id:
        query = query.join(models_flow.FlowNetwork).filter(models_flow.FlowNetwork.site_id == site_id)
        
    nodes = query.all()
    return [
        StockpileState(
            node_id=n.node_id,
            name=n.name,
            current_tonnage=n.current_tonnage or 0.0,
            current_grade=n.current_grade or 0.0,
            capacity_tonnes=n.capacity_tonnes
        ) for n in nodes
    ]

@router.post("/{node_id}/dump")
def dump_material(node_id: str, payload: DumpPayload, db: Session = Depends(get_db)):
    node = db.query(models_flow.FlowNode).filter(models_flow.FlowNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Stockpile not found")
        
    # Weighted Average Calculation
    current_tons = node.current_tonnage or 0.0
    current_grade = node.current_grade or 0.0
    
    new_tons = payload.quantity
    new_grade = payload.grade
    
    total_tons = current_tons + new_tons
    if total_tons > 0:
        avg_grade = ((current_tons * current_grade) + (new_tons * new_grade)) / total_tons
    else:
        avg_grade = 0.0
        
    node.current_tonnage = total_tons
    node.current_grade = avg_grade
    
    db.commit()
    db.refresh(node)
    
    return {
        "node_id": node.node_id,
        "current_tonnage": node.current_tonnage,
        "current_grade": node.current_grade
    }
