"""
Wash Table Router - API endpoints for wash tables and wash plants

Provides endpoints for:
- Wash table CRUD operations
- Row interpolation
- Cutpoint selection analysis
- Plant processing simulation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain.models_wash_table import WashTable, WashTableRow, WashPlantOperatingPoint
from ..domain.models_flow import WashPlantConfig, FlowNode
from ..services.wash_plant_service import WashPlantService
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid

router = APIRouter(prefix="/wash-plants", tags=["Wash Plants"])


# =============================================================================
# Pydantic Models
# =============================================================================

class WashTableCreate(BaseModel):
    """Request body for creating a wash table."""
    site_id: str
    table_name: str
    source_description: Optional[str] = None
    table_type: str = "Cumulative"  # Cumulative or Incremental


class WashTableRowCreate(BaseModel):
    """Request body for adding a row to a wash table."""
    rd_cutpoint: float
    cumulative_yield: float
    product_quality_vector: Dict[str, float]
    reject_quality_vector: Optional[Dict[str, float]] = None
    sequence: Optional[int] = None


class InterpolateRequest(BaseModel):
    """Request for interpolation at a cutpoint."""
    rd_cutpoint: float


class TargetQualityRequest(BaseModel):
    """Request for target quality cutpoint selection."""
    target_field: str
    target_value: float
    target_type: str = "Max"  # Max, Min, Target
    feed_tonnes: float = 1000.0


class OptimizerRequest(BaseModel):
    """Request for optimizer cutpoint selection."""
    feed_tonnes: float
    product_price_per_tonne: float
    reject_cost_per_tonne: float = 0.0
    quality_penalties: Optional[List[Dict]] = None


class ProcessFeedRequest(BaseModel):
    """Request to process material through a wash plant."""
    feed_tonnes: float
    feed_quality: Dict[str, float]
    period_id: Optional[str] = None
    schedule_version_id: Optional[str] = None


# =============================================================================
# Wash Table CRUD
# =============================================================================

@router.get("/tables/site/{site_id}")
def get_wash_tables(site_id: str, db: Session = Depends(get_db)):
    """Get all wash tables for a site."""
    tables = db.query(WashTable)\
        .filter(WashTable.site_id == site_id)\
        .all()
    
    return {
        "site_id": site_id,
        "tables": [
            {
                "table_id": t.wash_table_id,
                "table_name": t.name,
                "source_description": t.source_reference,
                "table_type": t.table_format,
                "row_count": len(t.rows) if t.rows else 0
            }
            for t in tables
        ]
    }


@router.get("/tables/{table_id}")
def get_wash_table(table_id: str, db: Session = Depends(get_db)):
    """Get a wash table with all rows."""
    table = db.query(WashTable)\
        .filter(WashTable.wash_table_id == table_id)\
        .first()
    
    if not table:
        raise HTTPException(status_code=404, detail="Wash table not found")
    
    rows = sorted(table.rows, key=lambda r: r.rd_cutpoint) if table.rows else []
    
    return {
        "table_id": table.wash_table_id,
        "table_name": table.name,
        "source_description": table.source_reference,
        "table_type": table.table_format,
        "rows": [
            {
                "row_id": r.row_id,
                "rd_cutpoint": r.rd_cutpoint,
                "cumulative_yield": r.cumulative_yield_fraction,
                "product_quality": r.product_quality_vector,
                "reject_quality": r.reject_quality_vector
            }
            for r in rows
        ]
    }


@router.post("/tables")
def create_wash_table(table: WashTableCreate, db: Session = Depends(get_db)):
    """Create a new wash table."""
    db_table = WashTable(
        wash_table_id=str(uuid.uuid4()),
        site_id=table.site_id,
        name=table.table_name,
        source_reference=table.source_description,
        table_format=table.table_type
    )
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    
    return {
        "table_id": db_table.wash_table_id,
        "table_name": db_table.name,
        "message": "Wash table created"
    }


@router.post("/tables/{table_id}/rows")
def add_table_row(table_id: str, row: WashTableRowCreate, db: Session = Depends(get_db)):
    """Add a row to a wash table."""
    table = db.query(WashTable)\
        .filter(WashTable.wash_table_id == table_id)\
        .first()
    
    if not table:
        raise HTTPException(status_code=404, detail="Wash table not found")
    
    db_row = WashTableRow(
        row_id=str(uuid.uuid4()),
        wash_table_id=table_id,
        rd_cutpoint=row.rd_cutpoint,
        cumulative_yield_fraction=row.cumulative_yield,
        product_quality_vector=row.product_quality_vector,
        reject_quality_vector=row.reject_quality_vector,
        sequence=row.sequence
    )
    db.add(db_row)
    db.commit()
    
    return {"row_id": db_row.row_id, "message": "Row added"}


@router.delete("/tables/{table_id}")
def delete_wash_table(table_id: str, db: Session = Depends(get_db)):
    """Delete a wash table."""
    table = db.query(WashTable)\
        .filter(WashTable.wash_table_id == table_id)\
        .first()
    
    if not table:
        raise HTTPException(status_code=404, detail="Wash table not found")
    
    # Delete rows first
    db.query(WashTableRow)\
        .filter(WashTableRow.wash_table_id == table_id)\
        .delete()
    
    db.delete(table)
    db.commit()
    
    return {"message": f"Wash table '{table.name}' deleted"}


# =============================================================================
# Interpolation & Analysis
# =============================================================================

@router.post("/tables/{table_id}/interpolate")
def interpolate_at_rd(
    table_id: str, 
    request: InterpolateRequest, 
    db: Session = Depends(get_db)
):
    """Interpolate wash table at a specific RD cutpoint."""
    service = WashPlantService(db)
    yield_frac, prod_qual, reject_qual = service.interpolate_wash_table(
        table_id, request.rd_cutpoint
    )
    
    return {
        "rd_cutpoint": request.rd_cutpoint,
        "yield_fraction": yield_frac,
        "product_quality": prod_qual,
        "reject_quality": reject_qual
    }


@router.post("/tables/{table_id}/find-cutpoint-target")
def find_cutpoint_for_target(
    table_id: str,
    request: TargetQualityRequest,
    db: Session = Depends(get_db)
):
    """Find optimal RD cutpoint to achieve target quality."""
    service = WashPlantService(db)
    result = service.select_cutpoint_target_quality(
        table_id=table_id,
        target_field=request.target_field,
        target_value=request.target_value,
        target_type=request.target_type,
        feed_tonnes=request.feed_tonnes
    )
    
    return {
        "selected_rd": result.cutpoint_rd,
        "yield_fraction": result.yield_fraction,
        "product_tonnes": result.product_tonnes,
        "reject_tonnes": result.reject_tonnes,
        "product_quality": result.product_quality,
        "selection_mode": result.selection_mode,
        "rationale": result.rationale
    }


@router.post("/tables/{table_id}/optimize-cutpoint")
def optimize_cutpoint(
    table_id: str,
    request: OptimizerRequest,
    db: Session = Depends(get_db)
):
    """Find optimal RD cutpoint based on economic analysis."""
    service = WashPlantService(db)
    result, analysis = service.select_cutpoint_optimizer(
        table_id=table_id,
        feed_tonnes=request.feed_tonnes,
        product_price=request.product_price_per_tonne,
        reject_cost=request.reject_cost_per_tonne,
        quality_penalties=request.quality_penalties
    )
    
    return {
        "optimal_cutpoint": analysis.optimal_cutpoint,
        "yield_fraction": result.yield_fraction,
        "product_tonnes": result.product_tonnes,
        "reject_tonnes": result.reject_tonnes,
        "product_quality": result.product_quality,
        "selection_rationale": analysis.selection_rationale,
        "analysis_points": analysis.analyses[:10]  # Top 10 for brevity
    }


# =============================================================================
# Plant Processing
# =============================================================================

@router.get("/nodes")
def get_wash_plant_nodes(site_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all wash plant nodes."""
    query = db.query(FlowNode)\
        .filter(FlowNode.node_type == "WashPlant")
    
    if site_id:
        query = query.join(FlowNode.network).filter_by(site_id=site_id)
    
    nodes = query.all()
    
    return {
        "wash_plants": [
            {
                "node_id": n.node_id,
                "name": n.name,
                "has_config": n.wash_plant_config is not None
            }
            for n in nodes
        ]
    }


@router.get("/{node_id}/config")
def get_wash_plant_config(node_id: str, db: Session = Depends(get_db)):
    """Get wash plant configuration."""
    config = db.query(WashPlantConfig)\
        .filter(WashPlantConfig.node_id == node_id)\
        .first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Wash plant config not found")
    
    return {
        "node_id": node_id,
        "wash_table_id": config.wash_table_id,
        "feed_capacity_tph": config.feed_capacity_tph,
        "cutpoint_selection_mode": config.cutpoint_selection_mode,
        "default_cutpoint_rd": getattr(config, 'default_cutpoint_rd', None),
        "yield_adjustment_factor": config.yield_adjustment_factor
    }


@router.post("/{node_id}/process")
def process_feed(
    node_id: str,
    request: ProcessFeedRequest,
    db: Session = Depends(get_db)
):
    """Process material through a wash plant."""
    service = WashPlantService(db)
    result = service.process_feed(
        node_id=node_id,
        feed_tonnes=request.feed_tonnes,
        feed_quality=request.feed_quality,
        period_id=request.period_id,
        schedule_version_id=request.schedule_version_id
    )
    
    return {
        "feed_tonnes": result.feed_tonnes,
        "product_tonnes": result.product_tonnes,
        "reject_tonnes": result.reject_tonnes,
        "yield_fraction": result.product_tonnes / result.feed_tonnes if result.feed_tonnes > 0 else 0,
        "feed_quality": result.feed_quality,
        "product_quality": result.product_quality,
        "reject_quality": result.reject_quality
    }


@router.get("/{node_id}/operating-points/{schedule_version_id}")
def get_operating_points(
    node_id: str,
    schedule_version_id: str,
    db: Session = Depends(get_db)
):
    """Get wash plant operating points for a schedule."""
    points = db.query(WashPlantOperatingPoint)\
        .filter(WashPlantOperatingPoint.plant_node_id == node_id)\
        .filter(WashPlantOperatingPoint.schedule_version_id == schedule_version_id)\
        .order_by(WashPlantOperatingPoint.period_id)\
        .all()
    
    return {
        "node_id": node_id,
        "schedule_version_id": schedule_version_id,
        "operating_points": [
            {
                "period_id": p.period_id,
                "cutpoint_rd": p.selected_rd_cutpoint,
                "feed_tonnes": p.feed_tonnes,
                "product_tonnes": p.product_tonnes,
                "reject_tonnes": p.reject_tonnes,
                "yield_fraction": p.yield_fraction,
                "selection_mode": p.cutpoint_selection_mode,
                "rationale": p.selection_rationale
            }
            for p in points
        ]
    }


# =============================================================================
# Reference Data
# =============================================================================

@router.get("/selection-modes")
def get_selection_modes():
    """Get list of supported cutpoint selection modes."""
    return {
        "modes": [
            {
                "name": "FixedRD",
                "description": "Use a predetermined RD cutpoint"
            },
            {
                "name": "TargetQuality",
                "description": "Find RD that achieves target product quality"
            },
            {
                "name": "OptimizerSelected",
                "description": "Choose RD based on economic optimization"
            }
        ]
    }
