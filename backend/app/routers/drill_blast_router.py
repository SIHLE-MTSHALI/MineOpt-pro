"""
Drill & Blast REST API Router

Endpoints for pattern design, drilling, loading, and blast management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.database import get_db
from app.services.drill_blast_service import DrillBlastService, get_drill_blast_service
from app.domain.models_drill_blast import ExplosiveType, DrillHoleStatus


router = APIRouter(prefix="/drill-blast", tags=["Drill & Blast"])


# =============================================================================
# Schemas
# =============================================================================

class ExplosiveTypeEnum(str, Enum):
    anfo = "anfo"
    emulsion = "emulsion"
    heavy_anfo = "heavy_anfo"
    watergel = "watergel"
    dynamite = "dynamite"


class PatternCreate(BaseModel):
    site_id: str
    burden: float
    spacing: float
    num_rows: int
    num_holes_per_row: int
    hole_depth_m: float
    bench_name: Optional[str] = None
    pattern_type: str = "rectangular"
    hole_diameter_mm: float = 165
    subdrill_m: float = 0.5
    stemming_height_m: float = 3.0
    explosive_type: ExplosiveTypeEnum = ExplosiveTypeEnum.anfo
    origin_x: float = 0
    origin_y: float = 0
    origin_z: float = 0
    orientation_degrees: float = 0
    designed_by: Optional[str] = None


class PatternResponse(BaseModel):
    pattern_id: str
    site_id: str
    bench_name: Optional[str]
    pattern_type: str
    burden: float
    spacing: float
    num_rows: int
    num_holes_per_row: int
    hole_depth_m: float
    powder_factor_kg_bcm: Optional[float]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class HoleDrilledUpdate(BaseModel):
    actual_x: float
    actual_y: float
    actual_z: float
    actual_depth_m: float
    drilled_by: Optional[str] = None
    drill_rig_id: Optional[str] = None
    penetration_rate: Optional[float] = None
    water_present: bool = False
    cavity_detected: bool = False
    notes: Optional[str] = None


class HoleLoadUpdate(BaseModel):
    charge_weight_kg: float
    explosive_type: ExplosiveTypeEnum
    detonator_delay_ms: int
    stemming_height_m: float
    loaded_by: Optional[str] = None
    primer_type: Optional[str] = None
    detonator_type: Optional[str] = None


class HoleResponse(BaseModel):
    hole_id: str
    hole_number: int
    row_number: Optional[int]
    design_x: float
    design_y: float
    design_depth_m: float
    actual_depth_m: Optional[float]
    charge_weight_kg: Optional[float]
    detonator_delay_ms: Optional[int]
    status: str
    
    class Config:
        from_attributes = True


class BlastEventCreate(BaseModel):
    pattern_id: str
    site_id: str
    blast_date: datetime
    blast_number: Optional[str] = None
    shotfirer_name: Optional[str] = None
    supervisor_name: Optional[str] = None
    initiation_system: str = "electronic"


class BlastResultsUpdate(BaseModel):
    actual_fire_time: datetime
    all_clear_time: Optional[datetime] = None
    max_ppv_mm_s: Optional[float] = None
    max_overpressure_db: Optional[float] = None
    avg_fragment_size_cm: Optional[float] = None
    oversize_percent: Optional[float] = None
    misfires: int = 0
    flyrock_incident: bool = False
    flyrock_details: Optional[str] = None
    notes: Optional[str] = None


class BlastEventResponse(BaseModel):
    event_id: str
    pattern_id: str
    blast_number: Optional[str]
    blast_date: datetime
    total_holes: Optional[int]
    total_explosive_kg: Optional[float]
    total_volume_bcm: Optional[float]
    powder_factor_kg_bcm: Optional[float]
    status: str
    fragmentation_rating: Optional[str]
    
    class Config:
        from_attributes = True


class FragmentationPrediction(BaseModel):
    pattern_id: str
    model_used: str
    rock_factor: float
    uniformity_index: float
    x50_cm: float
    size_distribution: dict
    oversize_percent: float
    powder_factor_kg_bcm: float
    charge_per_hole_kg: float


# =============================================================================
# Pattern Endpoints
# =============================================================================

@router.post("/patterns", response_model=PatternResponse)
def create_pattern(data: PatternCreate, db: Session = Depends(get_db)):
    """Create a new blast pattern."""
    service = get_drill_blast_service(db)
    pattern = service.create_pattern(
        site_id=data.site_id,
        burden=data.burden,
        spacing=data.spacing,
        num_rows=data.num_rows,
        num_holes_per_row=data.num_holes_per_row,
        hole_depth_m=data.hole_depth_m,
        bench_name=data.bench_name,
        pattern_type=data.pattern_type,
        hole_diameter_mm=data.hole_diameter_mm,
        subdrill_m=data.subdrill_m,
        stemming_height_m=data.stemming_height_m,
        explosive_type=ExplosiveType(data.explosive_type.value),
        origin_x=data.origin_x,
        origin_y=data.origin_y,
        origin_z=data.origin_z,
        orientation_degrees=data.orientation_degrees,
        designed_by=data.designed_by
    )
    return PatternResponse(
        pattern_id=pattern.pattern_id,
        site_id=pattern.site_id,
        bench_name=pattern.bench_name,
        pattern_type=pattern.pattern_type,
        burden=pattern.burden,
        spacing=pattern.spacing,
        num_rows=pattern.num_rows,
        num_holes_per_row=pattern.num_holes_per_row,
        hole_depth_m=pattern.hole_depth_m,
        powder_factor_kg_bcm=pattern.powder_factor_kg_bcm,
        status=pattern.status,
        created_at=pattern.created_at
    )


@router.get("/patterns/{pattern_id}", response_model=PatternResponse)
def get_pattern(pattern_id: str, db: Session = Depends(get_db)):
    """Get pattern by ID."""
    service = get_drill_blast_service(db)
    pattern = service.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse(
        pattern_id=pattern.pattern_id,
        site_id=pattern.site_id,
        bench_name=pattern.bench_name,
        pattern_type=pattern.pattern_type,
        burden=pattern.burden,
        spacing=pattern.spacing,
        num_rows=pattern.num_rows,
        num_holes_per_row=pattern.num_holes_per_row,
        hole_depth_m=pattern.hole_depth_m,
        powder_factor_kg_bcm=pattern.powder_factor_kg_bcm,
        status=pattern.status,
        created_at=pattern.created_at
    )


@router.get("/sites/{site_id}/patterns", response_model=List[PatternResponse])
def list_patterns(
    site_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List patterns for site."""
    service = get_drill_blast_service(db)
    patterns = service.list_patterns(site_id, status)
    return [
        PatternResponse(
            pattern_id=p.pattern_id,
            site_id=p.site_id,
            bench_name=p.bench_name,
            pattern_type=p.pattern_type,
            burden=p.burden,
            spacing=p.spacing,
            num_rows=p.num_rows,
            num_holes_per_row=p.num_holes_per_row,
            hole_depth_m=p.hole_depth_m,
            powder_factor_kg_bcm=p.powder_factor_kg_bcm,
            status=p.status,
            created_at=p.created_at
        )
        for p in patterns
    ]


@router.post("/patterns/{pattern_id}/approve")
def approve_pattern(
    pattern_id: str,
    approved_by: str = Query(...),
    db: Session = Depends(get_db)
):
    """Approve pattern for drilling."""
    service = get_drill_blast_service(db)
    try:
        pattern = service.approve_pattern(pattern_id, approved_by)
        return {"message": "Pattern approved", "pattern_id": pattern_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Hole Endpoints
# =============================================================================

@router.get("/patterns/{pattern_id}/holes", response_model=List[HoleResponse])
def get_pattern_holes(pattern_id: str, db: Session = Depends(get_db)):
    """Get all holes for a pattern."""
    service = get_drill_blast_service(db)
    holes = service.get_pattern_holes(pattern_id)
    return [
        HoleResponse(
            hole_id=h.hole_id,
            hole_number=h.hole_number,
            row_number=h.row_number,
            design_x=h.design_x,
            design_y=h.design_y,
            design_depth_m=h.design_depth_m,
            actual_depth_m=h.actual_depth_m,
            charge_weight_kg=h.charge_weight_kg,
            detonator_delay_ms=h.detonator_delay_ms,
            status=h.status.value if h.status else "planned"
        )
        for h in holes
    ]


@router.patch("/holes/{hole_id}/drilled", response_model=HoleResponse)
def update_hole_drilled(
    hole_id: str,
    data: HoleDrilledUpdate,
    db: Session = Depends(get_db)
):
    """Update hole with actual drilled values."""
    service = get_drill_blast_service(db)
    try:
        hole = service.update_hole_actuals(
            hole_id=hole_id,
            actual_x=data.actual_x,
            actual_y=data.actual_y,
            actual_z=data.actual_z,
            actual_depth_m=data.actual_depth_m,
            drilled_by=data.drilled_by,
            drill_rig_id=data.drill_rig_id,
            penetration_rate=data.penetration_rate,
            water_present=data.water_present,
            cavity_detected=data.cavity_detected,
            notes=data.notes
        )
        return HoleResponse(
            hole_id=hole.hole_id,
            hole_number=hole.hole_number,
            row_number=hole.row_number,
            design_x=hole.design_x,
            design_y=hole.design_y,
            design_depth_m=hole.design_depth_m,
            actual_depth_m=hole.actual_depth_m,
            charge_weight_kg=hole.charge_weight_kg,
            detonator_delay_ms=hole.detonator_delay_ms,
            status=hole.status.value if hole.status else "drilled"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/holes/{hole_id}/loaded", response_model=HoleResponse)
def load_hole(
    hole_id: str,
    data: HoleLoadUpdate,
    db: Session = Depends(get_db)
):
    """Record hole loading."""
    service = get_drill_blast_service(db)
    try:
        hole = service.load_hole(
            hole_id=hole_id,
            charge_weight_kg=data.charge_weight_kg,
            explosive_type=ExplosiveType(data.explosive_type.value),
            detonator_delay_ms=data.detonator_delay_ms,
            stemming_height_m=data.stemming_height_m,
            loaded_by=data.loaded_by,
            primer_type=data.primer_type,
            detonator_type=data.detonator_type
        )
        return HoleResponse(
            hole_id=hole.hole_id,
            hole_number=hole.hole_number,
            row_number=hole.row_number,
            design_x=hole.design_x,
            design_y=hole.design_y,
            design_depth_m=hole.design_depth_m,
            actual_depth_m=hole.actual_depth_m,
            charge_weight_kg=hole.charge_weight_kg,
            detonator_delay_ms=hole.detonator_delay_ms,
            status=hole.status.value if hole.status else "loaded"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Fragmentation Endpoints
# =============================================================================

@router.get("/patterns/{pattern_id}/fragmentation", response_model=FragmentationPrediction)
def predict_fragmentation(
    pattern_id: str,
    model_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Predict fragmentation using Kuz-Ram model."""
    service = get_drill_blast_service(db)
    try:
        result = service.predict_fragmentation(pattern_id, model_id)
        return FragmentationPrediction(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Blast Event Endpoints
# =============================================================================

@router.post("/events", response_model=BlastEventResponse)
def create_blast_event(data: BlastEventCreate, db: Session = Depends(get_db)):
    """Create a blast event."""
    service = get_drill_blast_service(db)
    try:
        event = service.create_blast_event(
            pattern_id=data.pattern_id,
            site_id=data.site_id,
            blast_date=data.blast_date,
            blast_number=data.blast_number,
            shotfirer_name=data.shotfirer_name,
            supervisor_name=data.supervisor_name,
            initiation_system=data.initiation_system
        )
        return BlastEventResponse(
            event_id=event.event_id,
            pattern_id=event.pattern_id,
            blast_number=event.blast_number,
            blast_date=event.blast_date,
            total_holes=event.total_holes,
            total_explosive_kg=event.total_explosive_kg,
            total_volume_bcm=event.total_volume_bcm,
            powder_factor_kg_bcm=event.powder_factor_kg_bcm,
            status=event.status,
            fragmentation_rating=event.fragmentation_rating
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/events/{event_id}/results", response_model=BlastEventResponse)
def record_blast_results(
    event_id: str,
    data: BlastResultsUpdate,
    db: Session = Depends(get_db)
):
    """Record blast results after firing."""
    service = get_drill_blast_service(db)
    try:
        event = service.record_blast_results(
            event_id=event_id,
            actual_fire_time=data.actual_fire_time,
            all_clear_time=data.all_clear_time,
            max_ppv_mm_s=data.max_ppv_mm_s,
            max_overpressure_db=data.max_overpressure_db,
            avg_fragment_size_cm=data.avg_fragment_size_cm,
            oversize_percent=data.oversize_percent,
            misfires=data.misfires,
            flyrock_incident=data.flyrock_incident,
            flyrock_details=data.flyrock_details,
            notes=data.notes
        )
        return BlastEventResponse(
            event_id=event.event_id,
            pattern_id=event.pattern_id,
            blast_number=event.blast_number,
            blast_date=event.blast_date,
            total_holes=event.total_holes,
            total_explosive_kg=event.total_explosive_kg,
            total_volume_bcm=event.total_volume_bcm,
            powder_factor_kg_bcm=event.powder_factor_kg_bcm,
            status=event.status,
            fragmentation_rating=event.fragmentation_rating
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/patterns/{pattern_id}/drill-log")
def get_drill_log(pattern_id: str, db: Session = Depends(get_db)):
    """Generate drill log report."""
    service = get_drill_blast_service(db)
    try:
        return service.generate_drill_log(pattern_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
