"""
Stockpile Router - API endpoints for stockpile management

Provides endpoints for:
- Stockpile state queries
- Material dumping (additions)
- Material reclaim (FIFO, LIFO, BlendedProportional)
- Capacity checking
- Inventory balance tracking
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_flow, models_resource
from ..services.stockpile_service import StockpileService
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter(prefix="/stockpiles", tags=["Stockpiles"])


# =============================================================================
# Pydantic Models
# =============================================================================

class StockpileState(BaseModel):
    """Current stockpile state response."""
    node_id: str
    name: str
    current_tonnage: float
    current_grade: Dict[str, float]
    capacity_tonnes: Optional[float]
    utilization_percent: float = 0.0
    parcel_count: int = 0
    inventory_method: str = "Aggregate"


class DumpPayload(BaseModel):
    """Request body for dumping material."""
    quantity: float
    quality: Dict[str, float]
    source_reference: Optional[str] = None
    period_id: Optional[str] = None
    create_parcel: bool = False


class ReclaimPayload(BaseModel):
    """Request body for reclaiming material."""
    quantity: float
    reclaim_method: str = "FIFO"  # FIFO, LIFO, BlendedProportional
    period_id: Optional[str] = None


class ReclaimResponse(BaseModel):
    """Response from reclaim operation."""
    reclaimed_tonnes: float
    reclaimed_quality: Dict[str, float]
    remaining_tonnes: float
    remaining_quality: Dict[str, float]
    parcels_used: List[str]
    warnings: List[str]


class BalanceResponse(BaseModel):
    """Inventory balance record."""
    period_id: str
    opening_tonnes: float
    additions_tonnes: float
    reclaim_tonnes: float
    closing_tonnes: float
    closing_quality: Dict[str, float]


class CapacityCheckResponse(BaseModel):
    """Capacity check result."""
    can_accept: bool
    available_capacity: float
    current_tonnes: float
    capacity_tonnes: Optional[float]


# =============================================================================
# Stockpile State Endpoints
# =============================================================================

@router.get("", response_model=List[StockpileState])
def get_stockpiles(site_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all stockpiles with their current state."""
    query = db.query(models_flow.FlowNode)\
        .filter(models_flow.FlowNode.node_type.in_(["Stockpile", "StagedStockpile"]))
    
    if site_id:
        query = query.join(models_flow.FlowNetwork)\
            .filter(models_flow.FlowNetwork.site_id == site_id)
        
    nodes = query.all()
    results = []
    
    service = StockpileService(db)
    
    for n in nodes:
        state = service.get_stockpile_state(n.node_id)
        if state:
            results.append(StockpileState(
                node_id=state.node_id,
                name=state.name,
                current_tonnage=state.current_tonnes,
                current_grade=state.current_quality,
                capacity_tonnes=state.capacity_tonnes,
                utilization_percent=state.utilization_percent,
                parcel_count=state.parcel_count,
                inventory_method=state.inventory_method
            ))
        
    return results


@router.get("/{node_id}", response_model=StockpileState)
def get_stockpile(node_id: str, db: Session = Depends(get_db)):
    """Get a specific stockpile's state."""
    service = StockpileService(db)
    state = service.get_stockpile_state(node_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Stockpile not found")
    
    return StockpileState(
        node_id=state.node_id,
        name=state.name,
        current_tonnage=state.current_tonnes,
        current_grade=state.current_quality,
        capacity_tonnes=state.capacity_tonnes,
        utilization_percent=state.utilization_percent,
        parcel_count=state.parcel_count,
        inventory_method=state.inventory_method
    )


# =============================================================================
# Dump & Reclaim Endpoints
# =============================================================================

@router.post("/{node_id}/dump")
def dump_material(node_id: str, payload: DumpPayload, db: Session = Depends(get_db)):
    """
    Deposit material onto a stockpile.
    
    Quality is blended with existing inventory using weighted average.
    Optionally creates a parcel record for tracking.
    """
    service = StockpileService(db)
    
    success, message, state = service.dump_material(
        node_id=node_id,
        quantity_tonnes=payload.quantity,
        quality_vector=payload.quality,
        source_reference=payload.source_reference,
        period_id=payload.period_id,
        create_parcel=payload.create_parcel
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "node_id": node_id,
        "current_tonnage": state.get("current_tonnes"),
        "current_grade": state.get("current_quality")
    }


@router.post("/{node_id}/reclaim", response_model=ReclaimResponse)
def reclaim_material(node_id: str, payload: ReclaimPayload, db: Session = Depends(get_db)):
    """
    Reclaim material from a stockpile.
    
    Reclaim methods:
    - FIFO: First-In-First-Out (oldest material first)
    - LIFO: Last-In-First-Out (newest material first)
    - BlendedProportional: Take proportionally from all parcels
    
    For aggregate stockpiles, the quality of reclaimed material
    equals the current blended quality.
    """
    if payload.reclaim_method not in ["FIFO", "LIFO", "BlendedProportional"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid reclaim_method. Use FIFO, LIFO, or BlendedProportional"
        )
    
    service = StockpileService(db)
    
    result = service.reclaim_material(
        node_id=node_id,
        quantity_tonnes=payload.quantity,
        reclaim_method=payload.reclaim_method,
        period_id=payload.period_id
    )
    
    return ReclaimResponse(
        reclaimed_tonnes=result.reclaimed_tonnes,
        reclaimed_quality=result.reclaimed_quality,
        remaining_tonnes=result.remaining_tonnes,
        remaining_quality=result.remaining_quality,
        parcels_used=result.parcels_used,
        warnings=result.warnings
    )


# =============================================================================
# Capacity Checking
# =============================================================================

@router.get("/{node_id}/capacity")
def check_capacity(node_id: str, additional: float = 0, db: Session = Depends(get_db)):
    """
    Check stockpile capacity.
    
    Args:
        additional: Optional amount to check if it would fit
    """
    service = StockpileService(db)
    state = service.get_stockpile_state(node_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Stockpile not found")
    
    can_accept, available = service.check_capacity(node_id, additional)
    
    return CapacityCheckResponse(
        can_accept=can_accept,
        available_capacity=available if available != float('inf') else -1,
        current_tonnes=state.current_tonnes,
        capacity_tonnes=state.capacity_tonnes
    )


# =============================================================================
# Inventory Balance Tracking
# =============================================================================

@router.get("/{node_id}/balance/{schedule_version_id}")
def get_balance_history(
    node_id: str, 
    schedule_version_id: str, 
    db: Session = Depends(get_db)
):
    """Get inventory balance history for a stockpile in a schedule."""
    service = StockpileService(db)
    balances = service.get_balance_history(schedule_version_id, node_id)
    
    return {
        "node_id": node_id,
        "schedule_version_id": schedule_version_id,
        "balance_count": len(balances),
        "balances": [
            {
                "period_id": b.period_id,
                "opening_tonnes": b.opening_tonnes,
                "additions_tonnes": b.additions_tonnes,
                "reclaim_tonnes": b.reclaim_tonnes,
                "closing_tonnes": b.closing_tonnes,
                "closing_quality": b.closing_quality
            }
            for b in balances
        ]
    }


@router.get("/{node_id}/balance/{schedule_version_id}/{period_id}")
def get_period_balance(
    node_id: str,
    schedule_version_id: str,
    period_id: str,
    db: Session = Depends(get_db)
):
    """Calculate balance for a specific period based on flow movements."""
    service = StockpileService(db)
    balance = service.calculate_period_balance(
        schedule_version_id, period_id, node_id
    )
    
    return {
        "node_id": node_id,
        "period_id": balance.period_id,
        "opening_tonnes": balance.opening_tonnes,
        "additions_tonnes": balance.additions_tonnes,
        "reclaim_tonnes": balance.reclaim_tonnes,
        "closing_tonnes": balance.closing_tonnes,
        "closing_quality": balance.closing_quality
    }


# =============================================================================
# Reclaim Methods Reference
# =============================================================================

@router.get("/methods/reclaim")
def get_reclaim_methods():
    """Get list of supported reclaim methods."""
    return {
        "methods": [
            {
                "name": "FIFO",
                "description": "First-In-First-Out - oldest material reclaimed first"
            },
            {
                "name": "LIFO",
                "description": "Last-In-First-Out - newest material reclaimed first"
            },
            {
                "name": "BlendedProportional",
                "description": "Take proportionally from all parcels, maintaining blend"
            }
        ]
    }

