"""
Quality Router - API endpoints for quality management

Provides endpoints for:
- Quality field CRUD operations
- Quality blending calculations
- Constraint evaluation
- Basis conversion
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain.models_resource import QualityField
from ..services.quality_service import (
    QualityService, 
    quality_service,
    THERMAL_COAL_QUALITY_FIELDS
)
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid

router = APIRouter(prefix="/quality", tags=["Quality Management"])


# =============================================================================
# Pydantic Models
# =============================================================================

class QualityFieldCreate(BaseModel):
    """Request body for creating a quality field."""
    site_id: str
    name: str
    display_name: Optional[str] = None
    unit: Optional[str] = None
    unit_basis: Optional[str] = None  # ARB, ADB, DB, DAF
    aggregation_rule: str = "WeightedAverage"  # WeightedAverage, Sum, Min, Max
    penalty_function_type: Optional[str] = "Linear"  # Linear, Quadratic, Step
    missing_data_policy: str = "Warning"  # Error, Warning, Ignore, UseDefault
    default_value: Optional[float] = None
    display_precision: int = 2


class QualityFieldUpdate(BaseModel):
    """Request body for updating a quality field."""
    display_name: Optional[str] = None
    unit: Optional[str] = None
    unit_basis: Optional[str] = None
    aggregation_rule: Optional[str] = None
    penalty_function_type: Optional[str] = None
    missing_data_policy: Optional[str] = None
    default_value: Optional[float] = None
    display_precision: Optional[int] = None


class BlendRequest(BaseModel):
    """Request body for blend calculation."""
    sources: List[Dict]  # Each: {quality_vector: {...}, quantity_tonnes: float}


class ConstraintCheckRequest(BaseModel):
    """Request body for constraint evaluation."""
    quality_vector: Dict[str, float]
    constraints: List[Dict]
    tolerance: float = 0.0


class BasisConversionRequest(BaseModel):
    """Request body for basis conversion."""
    value: float
    start_basis: str  # ARB, ADB, DB
    target_basis: str
    moisture_arb: float = 0.0
    moisture_adb: float = 0.0


# =============================================================================
# Quality Field CRUD Endpoints
# =============================================================================

@router.get("/fields/site/{site_id}")
def get_quality_fields(site_id: str, db: Session = Depends(get_db)):
    """Get all quality fields defined for a site."""
    fields = db.query(QualityField)\
        .filter(QualityField.site_id == site_id)\
        .all()
    return fields


@router.get("/fields/{field_id}")
def get_quality_field(field_id: str, db: Session = Depends(get_db)):
    """Get a specific quality field by ID."""
    field = db.query(QualityField)\
        .filter(QualityField.quality_field_id == field_id)\
        .first()
    if not field:
        raise HTTPException(status_code=404, detail="Quality field not found")
    return field


@router.post("/fields")
def create_quality_field(field: QualityFieldCreate, db: Session = Depends(get_db)):
    """Create a new quality field for a site."""
    # Check for duplicate name
    existing = db.query(QualityField)\
        .filter(QualityField.site_id == field.site_id)\
        .filter(QualityField.name == field.name)\
        .first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Quality field '{field.name}' already exists for this site"
        )
    
    db_field = QualityField(
        quality_field_id=str(uuid.uuid4()),
        site_id=field.site_id,
        name=field.name,
        display_name=field.display_name or field.name,
        unit=field.unit,
        unit_basis=field.unit_basis,
        aggregation_rule=field.aggregation_rule,
        penalty_function_type=field.penalty_function_type,
        missing_data_policy=field.missing_data_policy,
        default_value=field.default_value,
        display_precision=field.display_precision
    )
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    return db_field


@router.put("/fields/{field_id}")
def update_quality_field(
    field_id: str, 
    updates: QualityFieldUpdate, 
    db: Session = Depends(get_db)
):
    """Update a quality field."""
    field = db.query(QualityField)\
        .filter(QualityField.quality_field_id == field_id)\
        .first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Quality field not found")
    
    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(field, key, value)
    
    db.commit()
    db.refresh(field)
    return field


@router.delete("/fields/{field_id}")
def delete_quality_field(field_id: str, db: Session = Depends(get_db)):
    """Delete a quality field."""
    field = db.query(QualityField)\
        .filter(QualityField.quality_field_id == field_id)\
        .first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Quality field not found")
    
    db.delete(field)
    db.commit()
    return {"message": f"Quality field '{field.name}' deleted"}


@router.post("/fields/seed-thermal-coal/{site_id}")
def seed_thermal_coal_fields(site_id: str, db: Session = Depends(get_db)):
    """
    Seed standard thermal coal quality fields for a site.
    Creates CV, Ash, Moisture, Sulphur, VM, FC, HGI, and size fields.
    """
    created = []
    for field_def in THERMAL_COAL_QUALITY_FIELDS:
        # Check if already exists
        existing = db.query(QualityField)\
            .filter(QualityField.site_id == site_id)\
            .filter(QualityField.name == field_def["name"])\
            .first()
        
        if not existing:
            db_field = QualityField(
                quality_field_id=str(uuid.uuid4()),
                site_id=site_id,
                name=field_def["name"],
                display_name=field_def["display_name"],
                unit=field_def["unit"],
                unit_basis=field_def.get("unit_basis"),
                aggregation_rule=field_def["aggregation_rule"],
                display_precision=field_def["display_precision"]
            )
            db.add(db_field)
            created.append(field_def["name"])
    
    db.commit()
    return {
        "message": f"Created {len(created)} thermal coal quality fields",
        "fields_created": created,
        "total_fields": len(THERMAL_COAL_QUALITY_FIELDS)
    }


# =============================================================================
# Quality Calculation Endpoints
# =============================================================================

@router.post("/blend")
def calculate_blend(request: BlendRequest, db: Session = Depends(get_db)):
    """
    Calculate blended quality from multiple sources.
    
    Each source should have:
    - quality_vector: {field_name: value, ...}
    - quantity_tonnes: float
    """
    result = quality_service.calculate_blend_quality(request.sources)
    return {
        "quality_vector": result.quality_vector,
        "total_tonnes": result.total_tonnes,
        "source_count": result.source_count,
        "warnings": result.warnings
    }


@router.post("/check-constraints")
def check_constraints(request: ConstraintCheckRequest):
    """
    Evaluate quality against constraints.
    
    Each constraint should have:
    - field: quality field name
    - type: Min, Max, Target, or Range
    - value/min_value/max_value as appropriate
    - penalty_weight (optional, default 1.0)
    - penalty_type (optional: Linear, Quadratic, Step)
    - hard_constraint (optional, default false)
    """
    result = quality_service.evaluate_constraints(
        request.quality_vector,
        request.constraints,
        request.tolerance
    )
    return {
        "is_compliant": result.is_compliant,
        "compliance_percent": result.compliance_percent,
        "violations": result.violations,
        "penalties": result.penalties,
        "total_penalty": result.total_penalty,
        "hard_constraint_violated": result.hard_constraint_violated
    }


@router.post("/convert-basis")
def convert_basis(request: BasisConversionRequest):
    """
    Convert a quality value between bases.
    
    Supported: ARB <-> ADB <-> DB
    Requires moisture values for conversion.
    """
    result = quality_service.convert_basis(
        request.value,
        request.start_basis,
        request.target_basis,
        request.moisture_arb,
        request.moisture_adb
    )
    return {
        "original_value": request.value,
        "original_basis": request.start_basis,
        "converted_value": result,
        "target_basis": request.target_basis
    }


# =============================================================================
# Quality Tracking Endpoints
# =============================================================================

@router.get("/defaults/thermal-coal")
def get_thermal_coal_defaults():
    """Get the default thermal coal quality field definitions."""
    return {
        "fields": THERMAL_COAL_QUALITY_FIELDS,
        "count": len(THERMAL_COAL_QUALITY_FIELDS)
    }


@router.get("/aggregation-rules")
def get_aggregation_rules():
    """Get list of supported aggregation rules."""
    return {
        "rules": [
            {"name": "WeightedAverage", "description": "Mass-weighted average (default)"},
            {"name": "Sum", "description": "Sum of all values"},
            {"name": "Min", "description": "Minimum value"},
            {"name": "Max", "description": "Maximum value"}
        ]
    }


@router.get("/penalty-types")
def get_penalty_types():
    """Get list of supported penalty function types."""
    return {
        "types": [
            {"name": "Linear", "description": "penalty = weight × deviation"},
            {"name": "Quadratic", "description": "penalty = weight × deviation²"},
            {"name": "Step", "description": "penalty = step_value if violated"},
            {"name": "Exponential", "description": "penalty = weight × (e^deviation - 1)"}
        ]
    }


@router.get("/basis-types")
def get_basis_types():
    """Get list of supported quality bases."""
    return {
        "bases": [
            {"name": "ARB", "description": "As Received Basis (includes total moisture)"},
            {"name": "ADB", "description": "Air Dried Basis (includes inherent moisture)"},
            {"name": "DB", "description": "Dry Basis (moisture-free)"},
            {"name": "DAF", "description": "Dry Ash Free (moisture and ash-free)"}
        ]
    }
