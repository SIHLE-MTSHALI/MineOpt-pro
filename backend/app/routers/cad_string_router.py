"""
CAD String Router - Phase 2

REST API endpoints for CAD string operations.

Endpoints cover:
- CRUD operations
- Vertex manipulation
- Geometry operations (split, merge, offset, etc.)
- Analysis (length, area, gradient, intersections)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.cad_string_service import CADStringService, GradientInfo


router = APIRouter(prefix="/strings", tags=["CAD Strings"])


# =============================================================================
# Request/Response Models
# =============================================================================

class VertexModel(BaseModel):
    """A 3D vertex."""
    x: float
    y: float
    z: float = 0.0


class CreateStringRequest(BaseModel):
    """Request to create a CAD string."""
    site_id: str
    name: str
    vertices: List[List[float]] = Field(..., description="List of [x, y, z] coordinates")
    string_type: str = "custom"
    is_closed: bool = False
    layer: str = "DEFAULT"
    description: Optional[str] = None
    color: Optional[str] = None
    line_weight: float = 1.0
    elevation: Optional[float] = None
    surface_id: Optional[str] = None


class UpdateStringRequest(BaseModel):
    """Request to update string properties."""
    name: Optional[str] = None
    description: Optional[str] = None
    layer: Optional[str] = None
    string_type: Optional[str] = None
    is_closed: Optional[bool] = None
    color: Optional[str] = None
    line_weight: Optional[float] = None
    elevation: Optional[float] = None
    surface_id: Optional[str] = None


class SetVerticesRequest(BaseModel):
    """Request to set all vertices."""
    vertices: List[List[float]] = Field(..., description="List of [x, y, z] coordinates")


class InsertVertexRequest(BaseModel):
    """Request to insert a vertex."""
    index: int
    x: float
    y: float
    z: float = 0.0


class MoveVertexRequest(BaseModel):
    """Request to move a vertex."""
    index: int
    x: float
    y: float
    z: float


class MergeStringsRequest(BaseModel):
    """Request to merge two strings."""
    string_id_1: str
    string_id_2: str
    new_name: Optional[str] = None


class StringResponse(BaseModel):
    """CAD string response."""
    string_id: str
    site_id: str
    name: str
    description: Optional[str]
    layer: str
    string_type: str
    vertices: List[List[float]]
    vertex_count: int
    is_closed: bool
    surface_id: Optional[str]
    elevation: Optional[float]
    color: Optional[str]
    line_weight: float
    length: Optional[float]


class GradientResponse(BaseModel):
    """Gradient analysis response."""
    min_gradient: float
    max_gradient: float
    avg_gradient: float
    segment_gradients: List[float]


class IntersectionResponse(BaseModel):
    """Intersection point response."""
    x: float
    y: float
    z: Optional[float]


class StringTypesResponse(BaseModel):
    """Available string types response."""
    types: List[Dict[str, str]]


# =============================================================================
# Helper Functions
# =============================================================================

def string_to_response(string) -> StringResponse:
    """Convert CADString to response model."""
    return StringResponse(
        string_id=string.string_id,
        site_id=string.site_id,
        name=string.name,
        description=string.description,
        layer=string.layer,
        string_type=string.string_type,
        vertices=[list(v) for v in string.vertices],
        vertex_count=len(string.vertices),
        is_closed=string.is_closed,
        surface_id=string.surface_id,
        elevation=string.elevation,
        color=string.color,
        line_weight=string.line_weight,
        length=string.length
    )


# =============================================================================
# CRUD Endpoints
# =============================================================================

@router.post("/", response_model=StringResponse)
def create_string(request: CreateStringRequest, db: Session = Depends(get_db)):
    """Create a new CAD string."""
    service = CADStringService(db)
    
    # Convert vertices
    vertices = [tuple(v) for v in request.vertices]
    
    try:
        string = service.create_string(
            site_id=request.site_id,
            name=request.name,
            vertices=vertices,
            string_type=request.string_type,
            is_closed=request.is_closed,
            layer=request.layer,
            description=request.description,
            color=request.color,
            line_weight=request.line_weight,
            elevation=request.elevation,
            surface_id=request.surface_id
        )
        return string_to_response(string)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{string_id}", response_model=StringResponse)
def get_string(string_id: str, db: Session = Depends(get_db)):
    """Get a CAD string by ID."""
    service = CADStringService(db)
    string = service.get_string(string_id)
    
    if not string:
        raise HTTPException(status_code=404, detail="String not found")
    
    return string_to_response(string)


@router.get("/site/{site_id}", response_model=List[StringResponse])
def list_strings(
    site_id: str,
    string_type: Optional[str] = Query(None),
    layer: Optional[str] = Query(None),
    surface_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List CAD strings for a site."""
    service = CADStringService(db)
    strings = service.list_strings(
        site_id=site_id,
        string_type=string_type,
        layer=layer,
        surface_id=surface_id
    )
    return [string_to_response(s) for s in strings]


@router.put("/{string_id}", response_model=StringResponse)
def update_string(
    string_id: str,
    request: UpdateStringRequest,
    db: Session = Depends(get_db)
):
    """Update CAD string properties."""
    service = CADStringService(db)
    
    # Filter out None values
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    string = service.update_string(string_id, **updates)
    
    if not string:
        raise HTTPException(status_code=404, detail="String not found")
    
    return string_to_response(string)


@router.delete("/{string_id}")
def delete_string(string_id: str, db: Session = Depends(get_db)):
    """Delete a CAD string."""
    service = CADStringService(db)
    
    if not service.delete_string(string_id):
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"success": True, "message": "String deleted"}


# =============================================================================
# Vertex Endpoints
# =============================================================================

@router.get("/{string_id}/vertices")
def get_vertices(string_id: str, db: Session = Depends(get_db)):
    """Get vertices of a string."""
    service = CADStringService(db)
    vertices = service.get_vertices(string_id)
    
    if vertices is None:
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"vertices": [list(v) for v in vertices], "count": len(vertices)}


@router.put("/{string_id}/vertices")
def set_vertices(
    string_id: str,
    request: SetVerticesRequest,
    db: Session = Depends(get_db)
):
    """Replace all vertices of a string."""
    service = CADStringService(db)
    
    vertices = [tuple(v) for v in request.vertices]
    
    try:
        if not service.set_vertices(string_id, vertices):
            raise HTTPException(status_code=404, detail="String not found")
        return {"success": True, "vertex_count": len(vertices)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{string_id}/vertices/insert")
def insert_vertex(
    string_id: str,
    request: InsertVertexRequest,
    db: Session = Depends(get_db)
):
    """Insert a vertex at the specified index."""
    service = CADStringService(db)
    
    try:
        if not service.insert_vertex(string_id, request.index, request.x, request.y, request.z):
            raise HTTPException(status_code=404, detail="String not found")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{string_id}/vertices/{index}")
def delete_vertex(
    string_id: str,
    index: int,
    db: Session = Depends(get_db)
):
    """Delete a vertex at the specified index."""
    service = CADStringService(db)
    
    try:
        if not service.delete_vertex(string_id, index):
            raise HTTPException(status_code=404, detail="String not found")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{string_id}/vertices/{index}")
def move_vertex(
    string_id: str,
    index: int,
    request: MoveVertexRequest,
    db: Session = Depends(get_db)
):
    """Move a vertex to a new position."""
    service = CADStringService(db)
    
    try:
        if not service.move_vertex(string_id, index, request.x, request.y, request.z):
            raise HTTPException(status_code=404, detail="String not found")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Geometry Operation Endpoints
# =============================================================================

@router.post("/{string_id}/split")
def split_string(
    string_id: str,
    vertex_index: int = Query(..., description="Index of vertex to split at"),
    db: Session = Depends(get_db)
):
    """Split a string at the specified vertex."""
    service = CADStringService(db)
    
    try:
        string1, string2 = service.split_string(string_id, vertex_index)
        
        if not string1 or not string2:
            raise HTTPException(status_code=404, detail="String not found")
        
        return {
            "success": True,
            "part1": string_to_response(string1),
            "part2": string_to_response(string2)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/merge")
def merge_strings(request: MergeStringsRequest, db: Session = Depends(get_db)):
    """Merge two strings into one."""
    service = CADStringService(db)
    
    try:
        merged = service.merge_strings(
            request.string_id_1,
            request.string_id_2,
            request.new_name
        )
        
        if not merged:
            raise HTTPException(status_code=404, detail="One or both strings not found")
        
        return {"success": True, "merged_string": string_to_response(merged)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{string_id}/reverse")
def reverse_string(string_id: str, db: Session = Depends(get_db)):
    """Reverse the direction of a string."""
    service = CADStringService(db)
    
    if not service.reverse_string(string_id):
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"success": True, "message": "String reversed"}


@router.post("/{string_id}/close")
def close_string(string_id: str, db: Session = Depends(get_db)):
    """Close an open string."""
    service = CADStringService(db)
    
    if not service.close_string(string_id):
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"success": True, "message": "String closed"}


@router.post("/{string_id}/open")
def open_string(string_id: str, db: Session = Depends(get_db)):
    """Open a closed string."""
    service = CADStringService(db)
    
    if not service.open_string(string_id):
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"success": True, "message": "String opened"}


@router.post("/{string_id}/offset", response_model=StringResponse)
def offset_string(
    string_id: str,
    distance: float = Query(..., description="Offset distance"),
    side: str = Query("left", description="Side: 'left' or 'right'"),
    db: Session = Depends(get_db)
):
    """Create an offset (parallel) string."""
    service = CADStringService(db)
    
    try:
        offset = service.offset_string(string_id, distance, side)
        
        if not offset:
            raise HTTPException(status_code=400, detail="Offset failed")
        
        return string_to_response(offset)
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))


@router.post("/{string_id}/smooth")
def smooth_string(
    string_id: str,
    factor: float = Query(0.5, ge=0.0, le=1.0, description="Smoothing factor"),
    db: Session = Depends(get_db)
):
    """Smooth string vertices."""
    service = CADStringService(db)
    
    if not service.smooth_string(string_id, factor):
        raise HTTPException(status_code=404, detail="String not found or smoothing failed")
    
    return {"success": True, "message": f"String smoothed with factor {factor}"}


@router.post("/{string_id}/simplify")
def simplify_string(
    string_id: str,
    tolerance: float = Query(1.0, gt=0, description="Simplification tolerance"),
    db: Session = Depends(get_db)
):
    """Simplify string using Douglas-Peucker algorithm."""
    service = CADStringService(db)
    
    try:
        if not service.simplify_string(string_id, tolerance):
            raise HTTPException(status_code=404, detail="String not found or simplification failed")
        
        return {"success": True, "message": f"String simplified with tolerance {tolerance}"}
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))


@router.post("/{string_id}/densify")
def densify_string(
    string_id: str,
    max_segment: float = Query(..., gt=0, description="Maximum segment length"),
    db: Session = Depends(get_db)
):
    """Add vertices to ensure no segment exceeds max length."""
    service = CADStringService(db)
    
    if not service.densify_string(string_id, max_segment):
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"success": True, "message": f"String densified with max segment {max_segment}"}


@router.post("/{string_id}/project-to-elevation")
def project_to_elevation(
    string_id: str,
    elevation: float = Query(..., description="Target elevation"),
    db: Session = Depends(get_db)
):
    """Set all vertices to a constant elevation."""
    service = CADStringService(db)
    
    if not service.project_to_elevation(string_id, elevation):
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"success": True, "message": f"String projected to elevation {elevation}"}


@router.post("/{string_id}/buffer", response_model=StringResponse)
def buffer_string(
    string_id: str,
    distance: float = Query(..., gt=0, description="Buffer distance"),
    db: Session = Depends(get_db)
):
    """Create a buffer polygon around a string."""
    service = CADStringService(db)
    
    try:
        buffered = service.buffer_string(string_id, distance)
        
        if not buffered:
            raise HTTPException(status_code=400, detail="Buffer failed")
        
        return string_to_response(buffered)
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))


@router.post("/{string_id}/snap-to-grid")
def snap_to_grid(
    string_id: str,
    grid_size: float = Query(..., gt=0, description="Grid cell size"),
    db: Session = Depends(get_db)
):
    """Snap all vertices to a regular grid."""
    service = CADStringService(db)
    
    if not service.snap_to_grid(string_id, grid_size):
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"success": True, "message": f"String snapped to {grid_size}m grid"}


# =============================================================================
# Analysis Endpoints
# =============================================================================

@router.get("/{string_id}/length")
def get_string_length(string_id: str, db: Session = Depends(get_db)):
    """Calculate 3D polyline length."""
    service = CADStringService(db)
    
    length = service.calculate_length(string_id)
    
    if length is None:
        raise HTTPException(status_code=404, detail="String not found")
    
    return {"length_3d": length, "unit": "m"}


@router.get("/{string_id}/area")
def get_string_area(string_id: str, db: Session = Depends(get_db)):
    """Calculate area of closed polygon."""
    service = CADStringService(db)
    
    area = service.calculate_area(string_id)
    
    if area is None:
        raise HTTPException(status_code=400, detail="String not found or not closed")
    
    return {"area": area, "unit": "m²"}


@router.get("/{string_id}/gradient", response_model=GradientResponse)
def get_string_gradient(string_id: str, db: Session = Depends(get_db)):
    """Calculate gradient (slope) along string."""
    service = CADStringService(db)
    
    gradient = service.calculate_gradient(string_id)
    
    if gradient is None:
        raise HTTPException(status_code=404, detail="String not found")
    
    return GradientResponse(
        min_gradient=gradient.min_gradient,
        max_gradient=gradient.max_gradient,
        avg_gradient=gradient.avg_gradient,
        segment_gradients=gradient.segment_gradients
    )


@router.get("/intersections")
def find_intersections(
    string_id_1: str = Query(...),
    string_id_2: str = Query(...),
    db: Session = Depends(get_db)
):
    """Find intersection points between two strings."""
    service = CADStringService(db)
    
    try:
        intersections = service.find_intersections(string_id_1, string_id_2)
        
        return {
            "count": len(intersections),
            "intersections": [
                {"x": i.x, "y": i.y, "z": i.z}
                for i in intersections
            ]
        }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/types", response_model=StringTypesResponse)
def get_string_types(db: Session = Depends(get_db)):
    """Get list of available string types."""
    service = CADStringService(db)
    return StringTypesResponse(types=service.get_string_types())


@router.get("/{string_id}/export/dxf")
def export_string_dxf(string_id: str, db: Session = Depends(get_db)):
    """Export string as DXF entity data."""
    service = CADStringService(db)
    
    data = service.export_to_dxf_entities(string_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="String not found")
    
    return data
