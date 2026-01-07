"""
Surface Tools Router - Phase 3

REST API endpoints for advanced surface manipulation and analysis.

Endpoints:
- POST /surface-tools/clip - Clip surface to boundary
- POST /surface-tools/merge - Merge multiple surfaces
- POST /surface-tools/transform - Translate/rotate/scale/mirror
- POST /surface-tools/smooth - Laplacian smoothing
- POST /surface-tools/simplify - Reduce vertex count
- POST /surface-tools/densify - Add vertices
- POST /surface-tools/resample - Resample to grid
- GET /surface-tools/slope - Calculate slope/aspect at point
- GET /surface-tools/slope-map - Generate slope map
- POST /surface-tools/profile - Generate elevation profile
- POST /surface-tools/isopach - Calculate thickness between surfaces
- POST /surface-tools/drape - Drape points/lines onto surface
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.surface_service import SurfaceService
from ..services.surface_tools_service import (
    SurfaceToolsService, get_surface_tools_service,
    SlopeResult, SlopeMap, SurfaceProfile, IsopachResult
)


router = APIRouter(prefix="/surface-tools", tags=["Surface Tools"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ClipRequest(BaseModel):
    """Request to clip a surface to a boundary."""
    surface_id: str
    boundary: List[List[float]] = Field(..., description="Boundary polygon [[x, y], ...]")
    output_name: Optional[str] = None


class MergeRequest(BaseModel):
    """Request to merge multiple surfaces."""
    surface_ids: List[str]
    output_name: str = "Merged Surface"


class TranslateRequest(BaseModel):
    """Request to translate a surface."""
    surface_id: str
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0


class RotateRequest(BaseModel):
    """Request to rotate a surface."""
    surface_id: str
    angle_degrees: float
    center_x: float
    center_y: float


class ScaleRequest(BaseModel):
    """Request to scale a surface."""
    surface_id: str
    factor_xy: float
    factor_z: float = 1.0
    center_x: Optional[float] = None
    center_y: Optional[float] = None


class MirrorRequest(BaseModel):
    """Request to mirror a surface."""
    surface_id: str
    axis_point1: List[float] = Field(..., description="[x, y]")
    axis_point2: List[float] = Field(..., description="[x, y]")


class SmoothRequest(BaseModel):
    """Request to smooth a surface."""
    surface_id: str
    iterations: int = 1
    factor: float = 0.5


class SimplifyRequest(BaseModel):
    """Request to simplify a surface."""
    surface_id: str
    target_vertex_count: int


class DensifyRequest(BaseModel):
    """Request to densify a surface."""
    surface_id: str
    max_triangle_area: float


class ResampleRequest(BaseModel):
    """Request to resample a surface."""
    surface_id: str
    grid_spacing: float


class ProfileRequest(BaseModel):
    """Request for elevation profile."""
    surface_id: str
    start: List[float] = Field(..., description="[x, y]")
    end: List[float] = Field(..., description="[x, y]")
    interval: float = 5.0


class IsopachRequest(BaseModel):
    """Request for isopach calculation."""
    upper_surface_id: str
    lower_surface_id: str
    grid_spacing: float = 10.0


class DrapePointsRequest(BaseModel):
    """Request to drape points onto a surface."""
    surface_id: str
    points: List[List[float]] = Field(..., description="[[x, y], ...]")


class SampleLineRequest(BaseModel):
    """Request to sample along a line."""
    surface_id: str
    start: List[float] = Field(..., description="[x, y]")
    end: List[float] = Field(..., description="[x, y]")
    interval: float


class SlopeResponse(BaseModel):
    """Slope calculation response."""
    slope_degrees: float
    slope_percent: float
    aspect_degrees: float


class ProfilePointResponse(BaseModel):
    """Profile point response."""
    distance: float
    x: float
    y: float
    z: float
    slope_to_next: Optional[float] = None


class ProfileResponse(BaseModel):
    """Elevation profile response."""
    points: List[ProfilePointResponse]
    total_distance: float
    min_elevation: float
    max_elevation: float
    avg_elevation: float


class SurfaceResponse(BaseModel):
    """Basic surface response."""
    surface_id: str
    name: str
    vertex_count: int
    triangle_count: int


# =============================================================================
# Helper Functions
# =============================================================================

def get_services(db: Session):
    """Get surface services."""
    base_service = SurfaceService(db)
    tools_service = get_surface_tools_service(base_service)
    return base_service, tools_service


# =============================================================================
# Geometry Endpoints
# =============================================================================

@router.post("/clip")
def clip_surface(request: ClipRequest, db: Session = Depends(get_db)):
    """Clip a surface to a boundary polygon."""
    base_svc, tools_svc = get_services(db)
    
    # Load surface
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    try:
        boundary = [(p[0], p[1]) for p in request.boundary]
        clipped = tools_svc.clip_to_boundary(surface, boundary, request.output_name)
        
        return {
            "success": True,
            "name": clipped.name,
            "vertex_count": clipped.vertex_count,
            "triangle_count": clipped.triangle_count
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/merge")
def merge_surfaces(request: MergeRequest, db: Session = Depends(get_db)):
    """Merge multiple surfaces into one."""
    base_svc, tools_svc = get_services(db)
    
    # Load all surfaces
    surfaces = []
    for sid in request.surface_ids:
        surface = base_svc.load_surface(sid)
        if not surface:
            raise HTTPException(status_code=404, detail=f"Surface {sid} not found")
        surfaces.append(surface)
    
    try:
        merged = tools_svc.merge_surfaces(surfaces, request.output_name)
        
        return {
            "success": True,
            "name": merged.name,
            "vertex_count": merged.vertex_count,
            "triangle_count": merged.triangle_count
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Transformation Endpoints
# =============================================================================

@router.post("/translate")
def translate_surface(request: TranslateRequest, db: Session = Depends(get_db)):
    """Translate (move) a surface."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    result = tools_svc.translate_surface(surface, request.dx, request.dy, request.dz)
    
    return {
        "success": True,
        "name": result.name,
        "vertex_count": result.vertex_count,
        "translation": {"dx": request.dx, "dy": request.dy, "dz": request.dz}
    }


@router.post("/rotate")
def rotate_surface(request: RotateRequest, db: Session = Depends(get_db)):
    """Rotate a surface around a point."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    result = tools_svc.rotate_surface(
        surface, request.angle_degrees, 
        request.center_x, request.center_y
    )
    
    return {
        "success": True,
        "name": result.name,
        "vertex_count": result.vertex_count,
        "rotation": {
            "angle_degrees": request.angle_degrees,
            "center": [request.center_x, request.center_y]
        }
    }


@router.post("/scale")
def scale_surface(request: ScaleRequest, db: Session = Depends(get_db)):
    """Scale a surface from a center point."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    result = tools_svc.scale_surface(
        surface, request.factor_xy, request.factor_z,
        request.center_x, request.center_y
    )
    
    return {
        "success": True,
        "name": result.name,
        "vertex_count": result.vertex_count,
        "scale": {"xy": request.factor_xy, "z": request.factor_z}
    }


@router.post("/mirror")
def mirror_surface(request: MirrorRequest, db: Session = Depends(get_db)):
    """Mirror a surface across an axis line."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    try:
        axis_p1 = (request.axis_point1[0], request.axis_point1[1])
        axis_p2 = (request.axis_point2[0], request.axis_point2[1])
        
        result = tools_svc.mirror_surface(surface, axis_p1, axis_p2)
        
        return {
            "success": True,
            "name": result.name,
            "vertex_count": result.vertex_count
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Refinement Endpoints
# =============================================================================

@router.post("/smooth")
def smooth_surface(request: SmoothRequest, db: Session = Depends(get_db)):
    """Smooth a surface using Laplacian smoothing."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    result = tools_svc.smooth_surface(surface, request.iterations, request.factor)
    
    return {
        "success": True,
        "name": result.name,
        "vertex_count": result.vertex_count,
        "iterations": request.iterations,
        "factor": request.factor
    }


@router.post("/simplify")
def simplify_surface(request: SimplifyRequest, db: Session = Depends(get_db)):
    """Simplify a surface by reducing vertex count."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    original_count = surface.vertex_count
    
    try:
        result = tools_svc.simplify_surface(surface, request.target_vertex_count)
        
        return {
            "success": True,
            "name": result.name,
            "original_vertex_count": original_count,
            "new_vertex_count": result.vertex_count,
            "reduction_percent": round((1 - result.vertex_count / original_count) * 100, 1)
        }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))


@router.post("/densify")
def densify_surface(request: DensifyRequest, db: Session = Depends(get_db)):
    """Densify a surface by adding vertices to large triangles."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    original_count = surface.vertex_count
    result = tools_svc.densify_surface(surface, request.max_triangle_area)
    
    return {
        "success": True,
        "name": result.name,
        "original_vertex_count": original_count,
        "new_vertex_count": result.vertex_count,
        "vertices_added": result.vertex_count - original_count
    }


@router.post("/resample")
def resample_surface(request: ResampleRequest, db: Session = Depends(get_db)):
    """Resample a surface to a regular grid."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    try:
        result = tools_svc.resample_to_grid(surface, request.grid_spacing)
        
        return {
            "success": True,
            "name": result.name,
            "vertex_count": result.vertex_count,
            "triangle_count": result.triangle_count,
            "grid_spacing": request.grid_spacing
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Analysis Endpoints
# =============================================================================

@router.get("/slope", response_model=SlopeResponse)
def get_slope_at_point(
    surface_id: str = Query(...),
    x: float = Query(...),
    y: float = Query(...),
    db: Session = Depends(get_db)
):
    """Calculate slope and aspect at a specific point."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    result = tools_svc.calculate_slope_at_point(surface, x, y)
    
    if result is None:
        raise HTTPException(status_code=400, detail="Point outside surface")
    
    return SlopeResponse(
        slope_degrees=result.slope_degrees,
        slope_percent=result.slope_percent,
        aspect_degrees=result.aspect_degrees
    )


@router.get("/slope-map")
def get_slope_map(
    surface_id: str = Query(...),
    grid_spacing: float = Query(10.0, gt=0),
    db: Session = Depends(get_db)
):
    """Generate a slope map for the entire surface."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    result = tools_svc.calculate_slope_map(surface, grid_spacing)
    
    return {
        "grid_spacing": result.grid_spacing,
        "origin": result.origin,
        "rows": result.rows,
        "cols": result.cols,
        "slope_grid": result.slopes,
        "aspect_grid": result.aspects
    }


@router.post("/profile", response_model=ProfileResponse)
def generate_profile(request: ProfileRequest, db: Session = Depends(get_db)):
    """Generate an elevation profile along a line."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    start = (request.start[0], request.start[1])
    end = (request.end[0], request.end[1])
    
    result = tools_svc.generate_profile(surface, start, end, request.interval)
    
    return ProfileResponse(
        points=[
            ProfilePointResponse(
                distance=p.distance,
                x=p.x,
                y=p.y,
                z=p.z,
                slope_to_next=p.slope_to_next
            )
            for p in result.points
        ],
        total_distance=result.total_distance,
        min_elevation=result.min_elevation,
        max_elevation=result.max_elevation,
        avg_elevation=result.avg_elevation
    )


@router.post("/isopach")
def calculate_isopach(request: IsopachRequest, db: Session = Depends(get_db)):
    """Calculate thickness (isopach) between two surfaces."""
    base_svc, tools_svc = get_services(db)
    
    upper = base_svc.load_surface(request.upper_surface_id)
    lower = base_svc.load_surface(request.lower_surface_id)
    
    if not upper:
        raise HTTPException(status_code=404, detail="Upper surface not found")
    if not lower:
        raise HTTPException(status_code=404, detail="Lower surface not found")
    
    try:
        result = tools_svc.calculate_isopach(upper, lower, request.grid_spacing)
        
        return {
            "grid_spacing": result.grid_spacing,
            "origin": result.origin,
            "rows": result.rows,
            "cols": result.cols,
            "thickness_grid": result.thickness,
            "min_thickness": result.min_thickness,
            "max_thickness": result.max_thickness,
            "avg_thickness": result.avg_thickness
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Interpolation Endpoints
# =============================================================================

@router.post("/drape")
def drape_points(request: DrapePointsRequest, db: Session = Depends(get_db)):
    """Project XY points onto a surface (drape)."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    points = [(p[0], p[1]) for p in request.points]
    result = tools_svc.drape_points(surface, points)
    
    return {
        "input_count": len(points),
        "output_count": len(result),
        "draped_points": [[p[0], p[1], p[2]] for p in result]
    }


@router.post("/sample-line")
def sample_along_line(request: SampleLineRequest, db: Session = Depends(get_db)):
    """Sample elevations along a line at regular intervals."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(request.surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    start = (request.start[0], request.start[1])
    end = (request.end[0], request.end[1])
    
    result = tools_svc.sample_along_line(surface, start, end, request.interval)
    
    return {
        "interval": request.interval,
        "sample_count": len(result),
        "samples": [[p[0], p[1], p[2]] for p in result]
    }


@router.post("/sample-points")
def sample_at_points(
    surface_id: str = Query(...),
    points: List[List[float]] = None,
    db: Session = Depends(get_db)
):
    """Sample surface elevation at multiple XY points."""
    base_svc, tools_svc = get_services(db)
    
    surface = base_svc.load_surface(surface_id)
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    if not points:
        raise HTTPException(status_code=400, detail="No points provided")
    
    xy_points = [(p[0], p[1]) for p in points]
    elevations = tools_svc.sample_at_points(surface, xy_points)
    
    return {
        "sample_count": len(elevations),
        "elevations": elevations
    }
