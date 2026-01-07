"""
Surface Router - Phase 2 TIN Surface Generation API

REST API endpoints for surface creation, querying, and export.
"""

from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from ..database import get_db
from sqlalchemy.orm import Session
from ..services.surface_service import get_surface_service, TINSurface, Point3D, VolumeResult, SeamTonnage
from ..services.ascii_grid_service import get_ascii_grid_service
from ..services.dxf_service import get_dxf_service
from fastapi.responses import Response


router = APIRouter(prefix="/surfaces", tags=["Surfaces"])


# =============================================================================
# Request/Response Models
# =============================================================================

class PointInput(BaseModel):
    """A 3D point input."""
    x: float
    y: float
    z: float


class CreateFromPointsRequest(BaseModel):
    """Request to create TIN from points."""
    site_id: str
    name: str
    surface_type: str = "terrain"
    points: List[List[float]]  # [[x, y, z], ...]
    seam_name: Optional[str] = None


class CreateFromBoreholesRequest(BaseModel):
    """Request to create surface from borehole data."""
    site_id: str
    name: str
    surface_type: str = "terrain"  # terrain, seam_roof, seam_floor
    collar_ids: List[str]
    seam_name: Optional[str] = None


class VolumeRequest(BaseModel):
    """Request to calculate volume between surfaces."""
    upper_surface_id: str
    lower_surface_id: str
    grid_spacing: float = 5.0
    boundary: Optional[List[List[float]]] = None  # [[x, y], ...]
    density_t_m3: float = 1.4
    swell_factor: float = 1.0


class SeamTonnageRequest(BaseModel):
    """Request to calculate seam tonnage."""
    roof_surface_id: str
    floor_surface_id: str
    density_t_m3: float = 1.4
    mining_loss_pct: float = 5.0
    yield_pct: float = 85.0
    grid_spacing: float = 5.0
    boundary: Optional[List[List[float]]] = None


class SurfaceResponse(BaseModel):
    """Response containing surface data."""
    surface_id: str
    name: str
    surface_type: str
    seam_name: Optional[str]
    vertex_count: int
    triangle_count: int
    area_m2: Optional[float]
    extent_min: Optional[List[float]]
    extent_max: Optional[List[float]]
    created_at: datetime


class SurfaceDetailResponse(SurfaceResponse):
    """Detailed surface response with geometry."""
    vertices: List[List[float]]
    triangles: List[List[int]]


class VolumeResponse(BaseModel):
    """Volume calculation response."""
    volume_m3: float
    tonnage: float
    cut_volume: float
    fill_volume: float
    net_volume: float
    area_m2: float
    density_used: float
    swell_factor: float


class SeamTonnageResponse(BaseModel):
    """Seam tonnage calculation response."""
    in_situ_tonnes: float
    rom_tonnes: float
    product_tonnes: float
    seam_name: str
    thickness_avg: float
    thickness_min: float
    thickness_max: float
    area_m2: float
    volume_m3: float


class ContourResponse(BaseModel):
    """Contour line response."""
    elevation: float
    points: List[List[float]]
    is_closed: bool


class ElevationQueryResponse(BaseModel):
    """Elevation query response."""
    x: float
    y: float
    elevation: Optional[float]
    found: bool


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/create-from-points", response_model=SurfaceResponse)
async def create_surface_from_points(
    request: CreateFromPointsRequest,
    db: Session = Depends(get_db)
):
    """
    Create a TIN surface from a list of 3D points.
    
    Uses Delaunay triangulation to create a triangulated mesh.
    """
    service = get_surface_service(db)
    
    try:
        # Convert points
        points = [(p[0], p[1], p[2]) for p in request.points if len(p) >= 3]
        
        if len(points) < 3:
            raise HTTPException(status_code=400, detail="At least 3 points required")
        
        # Create TIN
        tin = service.create_tin_from_points(
            points=points,
            name=request.name,
            surface_type=request.surface_type
        )
        tin.seam_name = request.seam_name
        
        # Save to database
        surface_id = service.save_surface(tin, request.site_id)
        
        extent_min, extent_max = tin.get_extent()
        
        return SurfaceResponse(
            surface_id=surface_id,
            name=tin.name,
            surface_type=tin.surface_type,
            seam_name=tin.seam_name,
            vertex_count=tin.vertex_count,
            triangle_count=tin.triangle_count,
            area_m2=service.calculate_surface_area(tin),
            extent_min=[extent_min.x, extent_min.y, extent_min.z],
            extent_max=[extent_max.x, extent_max.y, extent_max.z],
            created_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create surface: {str(e)}")


@router.post("/create-from-file")
async def create_surface_from_file(
    site_id: str = Query(...),
    name: str = Query(...),
    surface_type: str = Query("terrain"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Create a TIN surface from an uploaded XYZ or ASC file.
    """
    service = get_surface_service(db)
    grid_service = get_ascii_grid_service()
    
    content = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.xyz') or filename.endswith('.txt'):
            result = grid_service.parse_xyz_bytes(content, file.filename)
            if not result.success:
                raise HTTPException(status_code=400, detail=result.errors[0])
            points = [(p.x, p.y, p.z) for p in result.points]
            
        elif filename.endswith('.asc'):
            result = grid_service.parse_asc_bytes(content, file.filename)
            if not result.success:
                raise HTTPException(status_code=400, detail=result.errors[0])
            points = [(p.x, p.y, p.z) for p in result.grid.to_points()]
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Use .xyz, .txt, or .asc"
            )
        
        # Create TIN
        tin = service.create_tin_from_points(
            points=points,
            name=name,
            surface_type=surface_type
        )
        
        # Save to database
        surface_id = service.save_surface(tin, site_id)
        
        return {
            "surface_id": surface_id,
            "name": name,
            "vertex_count": tin.vertex_count,
            "triangle_count": tin.triangle_count,
            "source_file": file.filename,
            "points_imported": len(points)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{surface_id}", response_model=SurfaceDetailResponse)
async def get_surface(
    surface_id: str,
    db: Session = Depends(get_db)
):
    """Get a surface by ID with full geometry."""
    from ..domain.models_surface import Surface
    
    surface = db.query(Surface).filter(Surface.surface_id == surface_id).first()
    
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    return SurfaceDetailResponse(
        surface_id=surface.surface_id,
        name=surface.name,
        surface_type=surface.surface_type,
        seam_name=surface.seam_name,
        vertex_count=surface.vertex_count,
        triangle_count=surface.triangle_count,
        area_m2=surface.area_m2,
        extent_min=[surface.min_x, surface.min_y, surface.min_z] if surface.min_x else None,
        extent_max=[surface.max_x, surface.max_y, surface.max_z] if surface.max_x else None,
        vertices=surface.vertex_data or [],
        triangles=surface.triangle_data or [],
        created_at=surface.created_at
    )


@router.get("/site/{site_id}", response_model=List[SurfaceResponse])
async def list_surfaces_for_site(
    site_id: str,
    surface_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all surfaces for a site."""
    from ..domain.models_surface import Surface
    
    query = db.query(Surface).filter(Surface.site_id == site_id, Surface.is_active == True)
    
    if surface_type:
        query = query.filter(Surface.surface_type == surface_type)
    
    surfaces = query.all()
    
    return [
        SurfaceResponse(
            surface_id=s.surface_id,
            name=s.name,
            surface_type=s.surface_type,
            seam_name=s.seam_name,
            vertex_count=s.vertex_count,
            triangle_count=s.triangle_count,
            area_m2=s.area_m2,
            extent_min=[s.min_x, s.min_y, s.min_z] if s.min_x else None,
            extent_max=[s.max_x, s.max_y, s.max_z] if s.max_x else None,
            created_at=s.created_at
        )
        for s in surfaces
    ]


@router.get("/{surface_id}/query")
async def query_elevation(
    surface_id: str,
    x: float = Query(...),
    y: float = Query(...),
    db: Session = Depends(get_db)
):
    """Query elevation at a specific XY location on the surface."""
    service = get_surface_service(db)
    
    tin = service.load_surface(surface_id)
    if not tin:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    elevation = service.query_elevation(tin, x, y)
    
    return ElevationQueryResponse(
        x=x,
        y=y,
        elevation=elevation,
        found=elevation is not None
    )


@router.post("/volume-between", response_model=VolumeResponse)
async def calculate_volume_between(
    request: VolumeRequest,
    db: Session = Depends(get_db)
):
    """Calculate volume between two surfaces."""
    service = get_surface_service(db)
    
    upper = service.load_surface(request.upper_surface_id)
    if not upper:
        raise HTTPException(status_code=404, detail="Upper surface not found")
    
    lower = service.load_surface(request.lower_surface_id)
    if not lower:
        raise HTTPException(status_code=404, detail="Lower surface not found")
    
    boundary = None
    if request.boundary:
        boundary = [(p[0], p[1]) for p in request.boundary]
    
    result = service.calculate_volume_between_surfaces(
        upper=upper,
        lower=lower,
        grid_spacing=request.grid_spacing,
        boundary=boundary
    )
    
    # Calculate tonnage
    result.tonnage = result.volume_m3 * request.density_t_m3
    result.density_used = request.density_t_m3
    
    return VolumeResponse(
        volume_m3=result.volume_m3,
        tonnage=result.tonnage,
        cut_volume=result.cut_volume,
        fill_volume=result.fill_volume,
        net_volume=result.net_volume,
        area_m2=result.area_m2,
        density_used=result.density_used,
        swell_factor=request.swell_factor
    )


@router.post("/seam-tonnage", response_model=SeamTonnageResponse)
async def calculate_seam_tonnage(
    request: SeamTonnageRequest,
    db: Session = Depends(get_db)
):
    """Calculate coal seam tonnage between roof and floor surfaces."""
    service = get_surface_service(db)
    
    roof = service.load_surface(request.roof_surface_id)
    if not roof:
        raise HTTPException(status_code=404, detail="Roof surface not found")
    
    floor = service.load_surface(request.floor_surface_id)
    if not floor:
        raise HTTPException(status_code=404, detail="Floor surface not found")
    
    boundary = None
    if request.boundary:
        boundary = [(p[0], p[1]) for p in request.boundary]
    
    result = service.calculate_seam_tonnage(
        roof=roof,
        floor=floor,
        density_t_m3=request.density_t_m3,
        mining_loss_pct=request.mining_loss_pct,
        yield_pct=request.yield_pct,
        grid_spacing=request.grid_spacing,
        boundary=boundary
    )
    
    return SeamTonnageResponse(
        in_situ_tonnes=result.in_situ_tonnes,
        rom_tonnes=result.rom_tonnes,
        product_tonnes=result.product_tonnes,
        seam_name=result.seam_name,
        thickness_avg=result.thickness_avg,
        thickness_min=result.thickness_min,
        thickness_max=result.thickness_max,
        area_m2=result.area_m2,
        volume_m3=result.volume_m3
    )


@router.get("/{surface_id}/contours", response_model=List[ContourResponse])
async def generate_contours(
    surface_id: str,
    interval: float = Query(5.0, description="Contour interval in meters"),
    db: Session = Depends(get_db)
):
    """Generate contour lines for a surface."""
    service = get_surface_service(db)
    
    tin = service.load_surface(surface_id)
    if not tin:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    contours = service.generate_contours(tin, interval=interval)
    
    return [
        ContourResponse(
            elevation=c.elevation,
            points=[list(p) for p in c.points],
            is_closed=c.is_closed
        )
        for c in contours
    ]


@router.get("/{surface_id}/export")
async def export_surface(
    surface_id: str,
    format: str = Query("dxf", regex="^(dxf|xyz|asc)$"),
    db: Session = Depends(get_db)
):
    """Export a surface to file format (DXF, XYZ, or ASC)."""
    service = get_surface_service(db)
    
    tin = service.load_surface(surface_id)
    if not tin:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    if format == "dxf":
        content = service.export_to_dxf(tin)
        filename = f"{tin.name}.dxf"
        media_type = "application/dxf"
    elif format == "xyz":
        content = service.export_to_xyz(tin)
        if content:
            content = content.encode('utf-8')
        filename = f"{tin.name}.xyz"
        media_type = "text/plain"
    else:
        # ASC format - would need grid conversion
        raise HTTPException(status_code=400, detail="ASC export not yet supported for TIN")
    
    if not content:
        raise HTTPException(status_code=500, detail="Failed to generate export")
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/{surface_id}")
async def delete_surface(
    surface_id: str,
    db: Session = Depends(get_db)
):
    """Delete a surface (soft delete)."""
    from ..domain.models_surface import Surface
    
    surface = db.query(Surface).filter(Surface.surface_id == surface_id).first()
    
    if not surface:
        raise HTTPException(status_code=404, detail="Surface not found")
    
    surface.is_active = False
    surface.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Surface deleted", "surface_id": surface_id}
