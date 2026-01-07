"""
Annotation Router - Phase 4

REST API endpoints for annotation management.

Endpoints:
- CRUD operations for annotations
- Specialized annotation creation (elevation, distance, area, volume)
- Entity linking
- Batch operations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.annotation_service import AnnotationService, get_annotation_service


router = APIRouter(prefix="/annotations", tags=["Annotations"])


# =============================================================================
# Request/Response Models
# =============================================================================

class CreateAnnotationRequest(BaseModel):
    """Request to create an annotation."""
    site_id: str
    text: str
    x: float
    y: float
    z: float = 0.0
    annotation_type: str = "text"
    height: float = 2.0
    rotation: float = 0.0
    layer: str = "LABELS"
    color: Optional[str] = None
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[str] = None


class UpdateAnnotationRequest(BaseModel):
    """Request to update an annotation."""
    text: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None
    layer: Optional[str] = None
    color: Optional[str] = None
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[str] = None


class ElevationLabelRequest(BaseModel):
    """Request for elevation label."""
    site_id: str
    x: float
    y: float
    elevation: float
    prefix: str = "RL "
    suffix: str = ""
    decimals: int = 2
    layer: str = "ELEVATIONS"


class DistanceLabelRequest(BaseModel):
    """Request for distance label."""
    site_id: str
    start: List[float] = Field(..., description="[x, y, z]")
    end: List[float] = Field(..., description="[x, y, z]")
    layer: str = "DIMENSIONS"


class AreaLabelRequest(BaseModel):
    """Request for area label."""
    site_id: str
    centroid: List[float] = Field(..., description="[x, y, z]")
    area_m2: float
    layer: str = "AREAS"


class VolumeLabelRequest(BaseModel):
    """Request for volume label."""
    site_id: str
    position: List[float] = Field(..., description="[x, y, z]")
    volume_m3: float
    tonnage: Optional[float] = None
    layer: str = "VOLUMES"


class GradientLabelRequest(BaseModel):
    """Request for gradient label."""
    site_id: str
    position: List[float] = Field(..., description="[x, y, z]")
    gradient_percent: float
    direction: float = 0.0
    layer: str = "GRADIENTS"


class CoordinateLabelRequest(BaseModel):
    """Request for coordinate label."""
    site_id: str
    x: float
    y: float
    z: float
    show_z: bool = True
    layer: str = "COORDINATES"


class LinkEntityRequest(BaseModel):
    """Request to link to entity."""
    entity_type: str
    entity_id: str


class ContourLabelsRequest(BaseModel):
    """Request for contour labels."""
    site_id: str
    contour_data: List[Dict] = Field(..., description="Contour data with elevation and points")
    interval: float = 5.0
    label_interval: float = 25.0
    layer: str = "CONTOUR_LABELS"


class BoreholeLabelRequest(BaseModel):
    """Request for borehole labels."""
    site_id: str
    boreholes: List[Dict] = Field(..., description="Borehole data with hole_id, x, y, z")
    layer: str = "BOREHOLE_LABELS"


class AnnotationResponse(BaseModel):
    """Annotation response."""
    annotation_id: str
    text: str
    x: float
    y: float
    z: float
    height: float
    rotation: float
    layer: str
    color: Optional[str]
    linked_entity_type: Optional[str]
    linked_entity_id: Optional[str]


# =============================================================================
# Helper Functions
# =============================================================================

def annotation_to_response(annotation) -> AnnotationResponse:
    """Convert annotation to response model."""
    return AnnotationResponse(
        annotation_id=annotation.annotation_id,
        text=annotation.text,
        x=annotation.x,
        y=annotation.y,
        z=annotation.z,
        height=annotation.height,
        rotation=annotation.rotation,
        layer=annotation.layer,
        color=annotation.color,
        linked_entity_type=annotation.linked_entity_type,
        linked_entity_id=annotation.linked_entity_id
    )


# =============================================================================
# CRUD Endpoints
# =============================================================================

@router.post("/", response_model=AnnotationResponse)
def create_annotation(
    request: CreateAnnotationRequest,
    db: Session = Depends(get_db)
):
    """Create a new annotation."""
    service = get_annotation_service(db)
    
    annotation = service.create_annotation(
        site_id=request.site_id,
        text=request.text,
        x=request.x,
        y=request.y,
        z=request.z,
        annotation_type=request.annotation_type,
        height=request.height,
        rotation=request.rotation,
        layer=request.layer,
        color=request.color,
        linked_entity_type=request.linked_entity_type,
        linked_entity_id=request.linked_entity_id
    )
    
    return annotation_to_response(annotation)


@router.get("/{annotation_id}", response_model=AnnotationResponse)
def get_annotation(annotation_id: str, db: Session = Depends(get_db)):
    """Get an annotation by ID."""
    service = get_annotation_service(db)
    annotation = service.get_annotation(annotation_id)
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return annotation_to_response(annotation)


@router.get("/site/{site_id}", response_model=List[AnnotationResponse])
def list_annotations(
    site_id: str,
    layer: Optional[str] = Query(None),
    linked_entity_type: Optional[str] = Query(None),
    linked_entity_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List annotations for a site."""
    service = get_annotation_service(db)
    annotations = service.list_annotations(
        site_id=site_id,
        layer=layer,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id
    )
    
    return [annotation_to_response(a) for a in annotations]


@router.put("/{annotation_id}", response_model=AnnotationResponse)
def update_annotation(
    annotation_id: str,
    request: UpdateAnnotationRequest,
    db: Session = Depends(get_db)
):
    """Update an annotation."""
    service = get_annotation_service(db)
    
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    annotation = service.update_annotation(annotation_id, **updates)
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return annotation_to_response(annotation)


@router.delete("/{annotation_id}")
def delete_annotation(annotation_id: str, db: Session = Depends(get_db)):
    """Delete an annotation."""
    service = get_annotation_service(db)
    
    if not service.delete_annotation(annotation_id):
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {"success": True, "message": "Annotation deleted"}


# =============================================================================
# Specialized Creation Endpoints
# =============================================================================

@router.post("/elevation", response_model=AnnotationResponse)
def create_elevation_label(
    request: ElevationLabelRequest,
    db: Session = Depends(get_db)
):
    """Create an elevation label."""
    service = get_annotation_service(db)
    
    annotation = service.create_elevation_label(
        site_id=request.site_id,
        x=request.x,
        y=request.y,
        elevation=request.elevation,
        prefix=request.prefix,
        suffix=request.suffix,
        decimals=request.decimals,
        layer=request.layer
    )
    
    return annotation_to_response(annotation)


@router.post("/distance", response_model=AnnotationResponse)
def create_distance_label(
    request: DistanceLabelRequest,
    db: Session = Depends(get_db)
):
    """Create a distance label between two points."""
    service = get_annotation_service(db)
    
    start = tuple(request.start)
    end = tuple(request.end)
    
    annotation = service.create_distance_label(
        site_id=request.site_id,
        start=start,
        end=end,
        layer=request.layer
    )
    
    return annotation_to_response(annotation)


@router.post("/area", response_model=AnnotationResponse)
def create_area_label(
    request: AreaLabelRequest,
    db: Session = Depends(get_db)
):
    """Create an area label."""
    service = get_annotation_service(db)
    
    centroid = tuple(request.centroid)
    
    annotation = service.create_area_label(
        site_id=request.site_id,
        centroid=centroid,
        area_m2=request.area_m2,
        layer=request.layer
    )
    
    return annotation_to_response(annotation)


@router.post("/volume", response_model=AnnotationResponse)
def create_volume_label(
    request: VolumeLabelRequest,
    db: Session = Depends(get_db)
):
    """Create a volume label."""
    service = get_annotation_service(db)
    
    position = tuple(request.position)
    
    annotation = service.create_volume_label(
        site_id=request.site_id,
        position=position,
        volume_m3=request.volume_m3,
        tonnage=request.tonnage,
        layer=request.layer
    )
    
    return annotation_to_response(annotation)


@router.post("/gradient", response_model=AnnotationResponse)
def create_gradient_label(
    request: GradientLabelRequest,
    db: Session = Depends(get_db)
):
    """Create a gradient/slope label."""
    service = get_annotation_service(db)
    
    position = tuple(request.position)
    
    annotation = service.create_gradient_label(
        site_id=request.site_id,
        position=position,
        gradient_percent=request.gradient_percent,
        direction=request.direction,
        layer=request.layer
    )
    
    return annotation_to_response(annotation)


@router.post("/coordinate", response_model=AnnotationResponse)
def create_coordinate_label(
    request: CoordinateLabelRequest,
    db: Session = Depends(get_db)
):
    """Create a coordinate label."""
    service = get_annotation_service(db)
    
    annotation = service.create_coordinate_label(
        site_id=request.site_id,
        x=request.x,
        y=request.y,
        z=request.z,
        show_z=request.show_z,
        layer=request.layer
    )
    
    return annotation_to_response(annotation)


# =============================================================================
# Entity Linking Endpoints
# =============================================================================

@router.post("/{annotation_id}/link")
def link_to_entity(
    annotation_id: str,
    request: LinkEntityRequest,
    db: Session = Depends(get_db)
):
    """Link an annotation to an entity."""
    service = get_annotation_service(db)
    
    if not service.link_to_entity(annotation_id, request.entity_type, request.entity_id):
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {"success": True, "message": "Entity linked"}


@router.delete("/{annotation_id}/link")
def unlink_from_entity(annotation_id: str, db: Session = Depends(get_db)):
    """Remove entity link from an annotation."""
    service = get_annotation_service(db)
    
    if not service.unlink_from_entity(annotation_id):
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {"success": True, "message": "Entity unlinked"}


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AnnotationResponse])
def get_entity_annotations(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get all annotations linked to an entity."""
    service = get_annotation_service(db)
    annotations = service.get_entity_annotations(entity_type, entity_id)
    
    return [annotation_to_response(a) for a in annotations]


@router.delete("/entity/{entity_type}/{entity_id}")
def delete_entity_annotations(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Delete all annotations linked to an entity."""
    service = get_annotation_service(db)
    count = service.delete_entity_annotations(entity_type, entity_id)
    
    return {"success": True, "deleted_count": count}


# =============================================================================
# Batch Endpoints
# =============================================================================

@router.post("/batch/contours")
def create_contour_labels(
    request: ContourLabelsRequest,
    db: Session = Depends(get_db)
):
    """Create labels for contours."""
    service = get_annotation_service(db)
    
    annotations = service.create_contour_labels(
        site_id=request.site_id,
        contour_data=request.contour_data,
        interval=request.interval,
        label_interval=request.label_interval,
        layer=request.layer
    )
    
    return {
        "success": True,
        "count": len(annotations),
        "annotations": [annotation_to_response(a) for a in annotations]
    }


@router.post("/batch/boreholes")
def create_borehole_labels(
    request: BoreholeLabelRequest,
    db: Session = Depends(get_db)
):
    """Create labels for boreholes."""
    service = get_annotation_service(db)
    
    annotations = service.create_borehole_labels(
        site_id=request.site_id,
        boreholes=request.boreholes,
        layer=request.layer
    )
    
    return {
        "success": True,
        "count": len(annotations),
        "annotations": [annotation_to_response(a) for a in annotations]
    }


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/types")
def get_annotation_types(db: Session = Depends(get_db)):
    """Get available annotation types."""
    service = get_annotation_service(db)
    return {"types": service.get_annotation_types()}


@router.get("/style/{annotation_type}")
def get_default_style(annotation_type: str, db: Session = Depends(get_db)):
    """Get default style for an annotation type."""
    service = get_annotation_service(db)
    return service.get_default_style(annotation_type)
