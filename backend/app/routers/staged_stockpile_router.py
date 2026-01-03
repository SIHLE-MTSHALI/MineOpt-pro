"""
Staged Stockpile Router - API endpoints for staged stockpiles

Provides endpoints for:
- Staged stockpile status queries
- Material acceptance and reclaim
- Build spec management
- State machine transitions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain.models_staged_stockpile import (
    StagedStockpileConfig, BuildSpec, StagedPileState
)
from ..services.staged_stockpile_service import StagedStockpileService
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid

router = APIRouter(prefix="/staged-stockpiles", tags=["Staged Stockpiles"])


# =============================================================================
# Pydantic Models
# =============================================================================

class PileStatusResponse(BaseModel):
    """Status of a single pile."""
    pile_index: int
    pile_name: str
    state: str
    current_tonnes: float
    target_tonnes: float
    current_quality: Dict[str, float]
    build_spec_name: Optional[str]
    progress_percent: float


class StagedStockpileStatusResponse(BaseModel):
    """Overall staged stockpile status."""
    node_id: str
    node_name: str
    number_of_piles: int
    total_tonnes: float
    piles: List[PileStatusResponse]
    building_pile_index: Optional[int]
    depleting_pile_index: Optional[int]
    active_build_spec: Optional[str]


class AcceptMaterialRequest(BaseModel):
    """Request to accept material."""
    quantity_tonnes: float
    quality_vector: Dict[str, float]
    source_reference: Optional[str] = None
    period_id: Optional[str] = None


class ReclaimRequest(BaseModel):
    """Request to reclaim material."""
    quantity_tonnes: float
    period_id: Optional[str] = None


class BuildSpecCreate(BaseModel):
    """Request to create a build spec."""
    build_name: str
    sequence: int
    target_tonnes: float
    min_threshold_tonnes: Optional[float] = None
    max_capacity_tonnes: Optional[float] = None
    quality_targets: Optional[List[Dict]] = None
    switching_rule: str = "tonnage_reached"


# =============================================================================
# Status Endpoints
# =============================================================================

@router.get("/{node_id}", response_model=StagedStockpileStatusResponse)
def get_staged_stockpile_status(node_id: str, db: Session = Depends(get_db)):
    """Get comprehensive status of a staged stockpile."""
    service = StagedStockpileService(db)
    status = service.get_staged_stockpile_status(node_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Staged stockpile not found")
    
    return StagedStockpileStatusResponse(
        node_id=status.node_id,
        node_name=status.node_name,
        number_of_piles=status.number_of_piles,
        total_tonnes=status.total_tonnes,
        piles=[
            PileStatusResponse(
                pile_index=p.pile_index,
                pile_name=p.pile_name,
                state=p.state,
                current_tonnes=p.current_tonnes,
                target_tonnes=p.target_tonnes,
                current_quality=p.current_quality,
                build_spec_name=p.build_spec_name,
                progress_percent=p.progress_percent
            )
            for p in status.piles
        ],
        building_pile_index=status.building_pile_index,
        depleting_pile_index=status.depleting_pile_index,
        active_build_spec=status.active_build_spec
    )


@router.get("/{node_id}/piles")
def get_pile_states(node_id: str, db: Session = Depends(get_db)):
    """Get all pile states for a staged stockpile."""
    config = db.query(StagedStockpileConfig)\
        .filter(StagedStockpileConfig.node_id == node_id)\
        .first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    piles = db.query(StagedPileState)\
        .filter(StagedPileState.staged_config_id == config.config_id)\
        .order_by(StagedPileState.pile_index)\
        .all()
    
    return {
        "node_id": node_id,
        "piles": [
            {
                "pile_index": p.pile_index,
                "pile_name": p.pile_name,
                "state": p.state,
                "current_tonnes": p.current_tonnes,
                "current_quality": p.current_quality_vector,
                "build_spec_id": p.current_build_spec_id,
                "last_state_change": p.last_state_change
            }
            for p in piles
        ]
    }


# =============================================================================
# Material Movement Endpoints
# =============================================================================

@router.post("/{node_id}/accept")
def accept_material(
    node_id: str, 
    request: AcceptMaterialRequest, 
    db: Session = Depends(get_db)
):
    """
    Accept material into the staged stockpile.
    Material is added to the pile currently in "Building" state.
    """
    service = StagedStockpileService(db)
    result = service.accept_material(
        node_id=node_id,
        quantity_tonnes=request.quantity_tonnes,
        quality_vector=request.quality_vector,
        source_reference=request.source_reference,
        period_id=request.period_id
    )
    
    if not result.accepted:
        raise HTTPException(status_code=400, detail=result.reason)
    
    return {
        "accepted": result.accepted,
        "pile_index": result.pile_index,
        "tonnes_accepted": result.tonnes_accepted,
        "message": result.reason
    }


@router.post("/{node_id}/reclaim")
def reclaim_material(
    node_id: str, 
    request: ReclaimRequest, 
    db: Session = Depends(get_db)
):
    """
    Reclaim material from the staged stockpile.
    Material is taken from the pile in "Depleting" state, or the first "Full" pile.
    """
    service = StagedStockpileService(db)
    tonnes, quality, message = service.reclaim_material(
        node_id=node_id,
        quantity_tonnes=request.quantity_tonnes,
        period_id=request.period_id
    )
    
    if tonnes == 0:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "reclaimed_tonnes": tonnes,
        "reclaimed_quality": quality,
        "message": message
    }


@router.post("/{node_id}/start-reclaim/{pile_index}")
def start_pile_reclaim(
    node_id: str, 
    pile_index: int, 
    db: Session = Depends(get_db)
):
    """
    Manually start reclaim on a specific pile.
    Transitions the pile from Full → Depleting.
    """
    service = StagedStockpileService(db)
    success, message = service.start_pile_reclaim(node_id, pile_index)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


# =============================================================================
# Build Spec Management
# =============================================================================

@router.get("/{node_id}/build-specs")
def get_build_specs(node_id: str, db: Session = Depends(get_db)):
    """Get all build specs for a staged stockpile."""
    config = db.query(StagedStockpileConfig)\
        .filter(StagedStockpileConfig.node_id == node_id)\
        .first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    specs = db.query(BuildSpec)\
        .filter(BuildSpec.staged_config_id == config.config_id)\
        .order_by(BuildSpec.sequence)\
        .all()
    
    return {
        "node_id": node_id,
        "build_specs": [
            {
                "spec_id": s.spec_id,
                "build_name": s.build_name,
                "sequence": s.sequence,
                "target_tonnes": s.target_tonnes,
                "quality_targets": s.quality_targets,
                "status": s.status
            }
            for s in specs
        ]
    }


@router.post("/{node_id}/build-specs")
def create_build_spec(
    node_id: str, 
    spec: BuildSpecCreate, 
    db: Session = Depends(get_db)
):
    """Create a new build spec for a staged stockpile."""
    config = db.query(StagedStockpileConfig)\
        .filter(StagedStockpileConfig.node_id == node_id)\
        .first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    db_spec = BuildSpec(
        spec_id=str(uuid.uuid4()),
        staged_config_id=config.config_id,
        build_name=spec.build_name,
        sequence=spec.sequence,
        target_tonnes=spec.target_tonnes,
        min_threshold_tonnes=spec.min_threshold_tonnes,
        max_capacity_tonnes=spec.max_capacity_tonnes,
        quality_targets=spec.quality_targets or [],
        switching_rule=spec.switching_rule,
        status="Pending"
    )
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    
    return {
        "spec_id": db_spec.spec_id,
        "build_name": db_spec.build_name,
        "sequence": db_spec.sequence,
        "status": db_spec.status
    }


@router.delete("/{node_id}/build-specs/{spec_id}")
def delete_build_spec(
    node_id: str, 
    spec_id: str, 
    db: Session = Depends(get_db)
):
    """Delete a build spec (only if Pending)."""
    spec = db.query(BuildSpec)\
        .filter(BuildSpec.spec_id == spec_id)\
        .first()
    
    if not spec:
        raise HTTPException(status_code=404, detail="Build spec not found")
    
    if spec.status != "Pending":
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete spec with status: {spec.status}"
        )
    
    db.delete(spec)
    db.commit()
    
    return {"message": f"Build spec '{spec.build_name}' deleted"}


# =============================================================================
# Initialization
# =============================================================================

@router.post("/{node_id}/initialize")
def initialize_staged_stockpile(node_id: str, db: Session = Depends(get_db)):
    """
    Initialize pile states for a staged stockpile.
    Creates empty pile state records based on config.
    """
    config = db.query(StagedStockpileConfig)\
        .filter(StagedStockpileConfig.node_id == node_id)\
        .first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    service = StagedStockpileService(db)
    service.initialize_pile_states(config.config_id, config.number_of_piles)
    
    return {
        "message": f"Initialized {config.number_of_piles} pile states",
        "node_id": node_id
    }
