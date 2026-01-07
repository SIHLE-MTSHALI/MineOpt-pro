"""
Raster Router - Phase 5

REST API endpoints for raster/DEM operations.

Endpoints:
- GET /raster/metadata - Get raster file metadata
- GET /raster/sample - Sample elevation at point
- POST /raster/sample-line - Sample along a line
- POST /raster/sample-points - Sample at multiple points
- POST /raster/tin - Generate TIN from DEM
- GET /raster/tile - Get map tile
- GET /raster/overview - Get overview image
- POST /raster/hillshade - Generate hillshade
"""

from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
import tempfile
import os

from ..database import get_db
from ..services.raster_service import (
    RasterService, get_raster_service,
    RasterMetadata, HillshadeParams
)


router = APIRouter(prefix="/raster", tags=["Raster/DEM"])


# =============================================================================
# Request/Response Models
# =============================================================================

class SampleLineRequest(BaseModel):
    """Request for sampling along a line."""
    file_path: str
    start: List[float] = Field(..., description="[x, y]")
    end: List[float] = Field(..., description="[x, y]")
    interval: float
    band: int = 1


class SamplePointsRequest(BaseModel):
    """Request for sampling at multiple points."""
    file_path: str
    points: List[List[float]] = Field(..., description="[[x, y], ...]")
    band: int = 1


class GenerateTINRequest(BaseModel):
    """Request for TIN generation from DEM."""
    file_path: str
    sample_spacing: float
    band: int = 1
    boundary: Optional[List[List[float]]] = Field(None, description="Boundary [[x, y], ...]")


class HillshadeRequest(BaseModel):
    """Request for hillshade generation."""
    file_path: str
    azimuth: float = 315.0
    altitude: float = 45.0
    z_factor: float = 1.0
    output_path: Optional[str] = None


class MetadataResponse(BaseModel):
    """Raster metadata response."""
    file_path: str
    format: str
    width: int
    height: int
    band_count: int
    dtype: str
    crs_epsg: Optional[int]
    bounds: List[float]
    resolution: List[float]
    nodata: Optional[float]
    driver: str


class ElevationSampleResponse(BaseModel):
    """Elevation sample response."""
    x: float
    y: float
    elevation: Optional[float]
    band: int


class TINResponse(BaseModel):
    """TIN generation response."""
    vertex_count: int
    triangle_count: int
    bounds: List[float]
    sample_spacing: float


# =============================================================================
# Metadata Endpoints
# =============================================================================

@router.get("/metadata", response_model=MetadataResponse)
def get_metadata(
    file_path: str = Query(..., description="Path to raster file")
):
    """Get metadata from a raster file."""
    service = get_raster_service()
    
    try:
        metadata = service.get_metadata(file_path)
        return MetadataResponse(
            file_path=metadata.file_path,
            format=metadata.format,
            width=metadata.width,
            height=metadata.height,
            band_count=metadata.band_count,
            dtype=metadata.dtype,
            crs_epsg=metadata.crs_epsg,
            bounds=list(metadata.bounds),
            resolution=list(metadata.resolution),
            nodata=metadata.nodata,
            driver=metadata.driver
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/check")
def check_readable(file_path: str = Query(...)):
    """Check if a raster file is readable."""
    service = get_raster_service()
    
    is_readable, error = service.is_readable(file_path)
    return {
        "file_path": file_path,
        "is_readable": is_readable,
        "error": error
    }


@router.get("/formats")
def get_supported_formats():
    """Get list of supported raster formats."""
    service = get_raster_service()
    return {"formats": service.get_supported_formats()}


# =============================================================================
# Sampling Endpoints
# =============================================================================

@router.get("/sample", response_model=ElevationSampleResponse)
def sample_elevation(
    file_path: str = Query(...),
    x: float = Query(...),
    y: float = Query(...),
    band: int = Query(1, ge=1)
):
    """Sample elevation at a specific point."""
    service = get_raster_service()
    
    try:
        elevation = service.sample_elevation(file_path, x, y, band)
        return ElevationSampleResponse(
            x=x,
            y=y,
            elevation=elevation,
            band=band
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sample-line")
def sample_along_line(request: SampleLineRequest):
    """Sample elevations along a line."""
    service = get_raster_service()
    
    try:
        start = tuple(request.start)
        end = tuple(request.end)
        
        samples = service.sample_along_line(
            request.file_path,
            start,
            end,
            request.interval,
            request.band
        )
        
        return {
            "sample_count": len(samples),
            "samples": [
                {"x": s.x, "y": s.y, "elevation": s.elevation, "band": s.band}
                for s in samples
            ]
        }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sample-points")
def sample_at_points(request: SamplePointsRequest):
    """Sample elevations at multiple points."""
    service = get_raster_service()
    
    try:
        points = [(p[0], p[1]) for p in request.points]
        samples = service.sample_elevations(
            request.file_path,
            points,
            request.band
        )
        
        return {
            "sample_count": len(samples),
            "samples": [
                {"x": s.x, "y": s.y, "elevation": s.elevation}
                for s in samples
            ]
        }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# TIN Generation
# =============================================================================

@router.post("/tin", response_model=TINResponse)
def generate_tin(request: GenerateTINRequest):
    """Generate TIN from DEM raster."""
    service = get_raster_service()
    
    try:
        boundary = None
        if request.boundary:
            boundary = [(p[0], p[1]) for p in request.boundary]
        
        result = service.generate_tin_from_dem(
            request.file_path,
            request.sample_spacing,
            request.band,
            boundary
        )
        
        return TINResponse(
            vertex_count=result["vertex_count"],
            triangle_count=result["triangle_count"],
            bounds=list(result["bounds"]),
            sample_spacing=result["sample_spacing"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tin/full")
def generate_tin_full(request: GenerateTINRequest):
    """Generate TIN from DEM raster, returning full geometry."""
    service = get_raster_service()
    
    try:
        boundary = None
        if request.boundary:
            boundary = [(p[0], p[1]) for p in request.boundary]
        
        result = service.generate_tin_from_dem(
            request.file_path,
            request.sample_spacing,
            request.band,
            boundary
        )
        
        return {
            "vertices": [[v[0], v[1], v[2]] for v in result["vertices"]],
            "triangles": [list(t) for t in result["triangles"]],
            "vertex_count": result["vertex_count"],
            "triangle_count": result["triangle_count"],
            "bounds": list(result["bounds"]),
            "sample_spacing": result["sample_spacing"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))


# =============================================================================
# Tile and Overview Endpoints
# =============================================================================

@router.get("/tile/{zoom}/{tile_x}/{tile_y}.png")
def get_tile(
    zoom: int,
    tile_x: int,
    tile_y: int,
    file_path: str = Query(...),
    tile_size: int = Query(256, ge=128, le=512)
):
    """Get a map tile at specified TMS coordinates."""
    service = get_raster_service()
    
    try:
        tile = service.generate_tile(file_path, tile_x, tile_y, zoom, tile_size)
        return Response(
            content=tile.data,
            media_type="image/png"
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overview")
def get_overview(
    file_path: str = Query(...),
    max_size: int = Query(512, ge=64, le=2048),
    band: int = Query(1, ge=1)
):
    """Get a downsampled overview image of the raster."""
    service = get_raster_service()
    
    try:
        image_bytes = service.generate_overview_image(file_path, max_size, band)
        return Response(
            content=image_bytes,
            media_type="image/png"
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Hillshade
# =============================================================================

@router.post("/hillshade")
def generate_hillshade(request: HillshadeRequest):
    """Generate hillshade from DEM."""
    service = get_raster_service()
    
    try:
        params = HillshadeParams(
            azimuth=request.azimuth,
            altitude=request.altitude,
            z_factor=request.z_factor
        )
        
        hillshade = service.generate_hillshade(
            request.file_path,
            params,
            request.output_path
        )
        
        return {
            "success": True,
            "output_path": request.output_path,
            "shape": list(hillshade.shape),
            "min_value": int(hillshade.min()),
            "max_value": int(hillshade.max())
        }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hillshade/preview")
def get_hillshade_preview(
    file_path: str = Query(...),
    azimuth: float = Query(315.0),
    altitude: float = Query(45.0),
    z_factor: float = Query(1.0),
    max_size: int = Query(512, ge=64, le=2048)
):
    """Get hillshade preview as PNG image."""
    service = get_raster_service()
    
    try:
        from PIL import Image
        import io
        import numpy as np
        
        params = HillshadeParams(
            azimuth=azimuth,
            altitude=altitude,
            z_factor=z_factor
        )
        
        hillshade = service.generate_hillshade(file_path, params)
        
        # Resize for preview
        img = Image.fromarray(hillshade, mode='L')
        
        if img.width > max_size or img.height > max_size:
            ratio = min(max_size / img.width, max_size / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/png"
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
