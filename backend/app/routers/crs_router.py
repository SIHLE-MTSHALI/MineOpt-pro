"""
CRS Router - Phase 1

REST API endpoints for Coordinate Reference System operations.

Endpoints:
- GET /crs/systems - List all supported CRS
- GET /crs/regions - List supported regions
- GET /crs/{epsg}/info - Get CRS information
- POST /crs/transform - Transform coordinates
- POST /crs/transform-file - Transform coordinates from file
- GET /crs/detect - Auto-detect best CRS for coordinates
- POST /crs/validate - Validate EPSG code or WKT
"""

from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import io

from ..services.crs_service import (
    get_crs_service, 
    CRSInfo, 
    CRSCategory, 
    TransformResult
)


router = APIRouter(prefix="/crs", tags=["Coordinate Reference Systems"])


# =============================================================================
# Request/Response Models
# =============================================================================

class CRSInfoResponse(BaseModel):
    """CRS information response."""
    epsg: int
    name: str
    category: str
    units: str
    description: str
    region: str
    bounds: Optional[List[float]] = None
    is_south_hemisphere: bool = False
    utm_zone: Optional[int] = None


class TransformRequest(BaseModel):
    """Request to transform coordinates."""
    points: List[List[float]] = Field(
        ..., 
        description="List of [x, y, z] coordinates"
    )
    from_epsg: int = Field(..., description="Source EPSG code")
    to_epsg: int = Field(..., description="Target EPSG code")


class TransformResponse(BaseModel):
    """Response from coordinate transformation."""
    success: bool
    source_crs: int
    target_crs: int
    source_points: List[List[float]]
    transformed_points: List[List[float]]
    point_count: int
    errors: List[str] = []


class DetectCRSResponse(BaseModel):
    """Response for CRS detection."""
    recommended_epsg: int
    crs_info: CRSInfoResponse
    alternatives: List[CRSInfoResponse] = []


class ValidateResponse(BaseModel):
    """Response for CRS validation."""
    is_valid: bool
    epsg: Optional[int] = None
    crs_name: Optional[str] = None
    error: Optional[str] = None
    wkt: Optional[str] = None


class FileTransformRequest(BaseModel):
    """Request for file-based coordinate transformation."""
    from_epsg: int
    to_epsg: int
    x_column: str = "X"
    y_column: str = "Y"
    z_column: str = "Z"
    delimiter: str = ","
    has_header: bool = True


# =============================================================================
# Helper Functions
# =============================================================================

def crs_info_to_response(info: CRSInfo) -> CRSInfoResponse:
    """Convert CRSInfo to response model."""
    return CRSInfoResponse(
        epsg=info.epsg,
        name=info.name,
        category=info.category.value,
        units=info.units,
        description=info.description,
        region=info.region,
        bounds=list(info.bounds) if info.bounds else None,
        is_south_hemisphere=info.is_south_hemisphere,
        utm_zone=info.utm_zone
    )


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/systems", response_model=List[CRSInfoResponse])
def list_coordinate_systems(
    region: Optional[str] = Query(None, description="Filter by region"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    List all supported coordinate reference systems.
    
    Optional filters by region or category.
    """
    service = get_crs_service()
    
    # Convert category string to enum if provided
    cat_enum = None
    if category:
        try:
            cat_enum = CRSCategory(category.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Valid options: geographic, projected, local, custom"
            )
    
    systems = service.get_supported_crs(region=region, category=cat_enum)
    return [crs_info_to_response(s) for s in systems]


@router.get("/regions", response_model=List[str])
def list_regions():
    """List all supported regions."""
    service = get_crs_service()
    return service.get_regions()


@router.get("/{epsg}/info", response_model=CRSInfoResponse)
def get_crs_info(epsg: int):
    """
    Get detailed information about a coordinate reference system.
    
    Accepts any valid EPSG code.
    """
    service = get_crs_service()
    info = service.get_crs_info(epsg)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"EPSG code {epsg} not found or invalid"
        )
    
    return crs_info_to_response(info)


@router.get("/{epsg}/wkt")
def get_crs_wkt(epsg: int):
    """
    Get the WKT (Well-Known Text) representation of a CRS.
    """
    service = get_crs_service()
    wkt = service.get_crs_wkt(epsg)
    
    if not wkt:
        raise HTTPException(
            status_code=404,
            detail=f"EPSG code {epsg} not found or invalid"
        )
    
    return {"epsg": epsg, "wkt": wkt}


@router.post("/transform", response_model=TransformResponse)
def transform_coordinates(request: TransformRequest):
    """
    Transform coordinates from one CRS to another.
    
    Accepts a list of [x, y, z] points.
    """
    service = get_crs_service()
    
    # Validate CRS codes
    valid_from, error_from = service.validate_epsg(request.from_epsg)
    if not valid_from:
        raise HTTPException(status_code=400, detail=error_from)
    
    valid_to, error_to = service.validate_epsg(request.to_epsg)
    if not valid_to:
        raise HTTPException(status_code=400, detail=error_to)
    
    # Convert input to tuples
    points = []
    for p in request.points:
        if len(p) < 2:
            raise HTTPException(
                status_code=400,
                detail="Each point must have at least [x, y] coordinates"
            )
        x, y = p[0], p[1]
        z = p[2] if len(p) >= 3 else 0.0
        points.append((x, y, z))
    
    # Transform
    result = service.transform_points(points, request.from_epsg, request.to_epsg)
    
    return TransformResponse(
        success=result.success,
        source_crs=result.source_crs,
        target_crs=result.target_crs,
        source_points=[[p[0], p[1], p[2]] for p in result.source_points],
        transformed_points=[[p[0], p[1], p[2]] for p in result.transformed_points],
        point_count=result.point_count,
        errors=result.errors
    )


@router.post("/transform-point")
def transform_single_point(
    x: float = Query(..., description="X coordinate"),
    y: float = Query(..., description="Y coordinate"),
    z: float = Query(0.0, description="Z coordinate"),
    from_epsg: int = Query(..., description="Source EPSG code"),
    to_epsg: int = Query(..., description="Target EPSG code")
):
    """
    Transform a single point between coordinate systems.
    
    Quick endpoint for single-point transformations.
    """
    service = get_crs_service()
    
    try:
        tx, ty, tz = service.transform_point(x, y, z, from_epsg, to_epsg)
        return {
            "source": {"x": x, "y": y, "z": z, "epsg": from_epsg},
            "transformed": {"x": tx, "y": ty, "z": tz, "epsg": to_epsg}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/detect", response_model=DetectCRSResponse)
def detect_crs(
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in degrees"),
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in degrees"),
    region: Optional[str] = Query(None, description="Region hint (e.g., 'South Africa')")
):
    """
    Auto-detect the best coordinate reference system for a location.
    
    Provides the recommended CRS and alternatives.
    """
    service = get_crs_service()
    
    recommended_epsg = service.detect_best_crs(longitude, latitude, region)
    recommended_info = service.get_crs_info(recommended_epsg)
    
    if not recommended_info:
        raise HTTPException(
            status_code=500,
            detail="Failed to get CRS info for recommended system"
        )
    
    # Get alternatives based on region/location
    alternatives = []
    if region:
        region_crs = service.get_crs_for_region(region)
        alternatives = [
            crs_info_to_response(c) for c in region_crs 
            if c.epsg != recommended_epsg
        ][:5]  # Limit to 5 alternatives
    else:
        # Provide UTM alternatives
        utm_north = service.detect_utm_zone(longitude, latitude)
        utm_info = service.get_crs_info(utm_north)
        if utm_info and utm_info.epsg != recommended_epsg:
            alternatives.append(crs_info_to_response(utm_info))
    
    return DetectCRSResponse(
        recommended_epsg=recommended_epsg,
        crs_info=crs_info_to_response(recommended_info),
        alternatives=alternatives
    )


@router.post("/validate", response_model=ValidateResponse)
def validate_crs(
    epsg: Optional[int] = Query(None, description="EPSG code to validate"),
    wkt: Optional[str] = Query(None, description="WKT string to validate")
):
    """
    Validate an EPSG code or WKT CRS definition.
    """
    service = get_crs_service()
    
    if epsg is None and wkt is None:
        raise HTTPException(
            status_code=400,
            detail="Either 'epsg' or 'wkt' parameter is required"
        )
    
    if epsg:
        is_valid, error = service.validate_epsg(epsg)
        if is_valid:
            info = service.get_crs_info(epsg)
            wkt_str = service.get_crs_wkt(epsg)
            return ValidateResponse(
                is_valid=True,
                epsg=epsg,
                crs_name=info.name if info else None,
                wkt=wkt_str
            )
        else:
            return ValidateResponse(is_valid=False, error=error)
    
    if wkt:
        is_valid, error = service.validate_wkt(wkt)
        return ValidateResponse(is_valid=is_valid, error=error, wkt=wkt if is_valid else None)
    
    return ValidateResponse(is_valid=False, error="No input provided")


@router.post("/transform-file")
async def transform_file(
    file: UploadFile = File(...),
    from_epsg: int = Query(..., description="Source EPSG code"),
    to_epsg: int = Query(..., description="Target EPSG code"),
    x_column: str = Query("X", description="X column name or index"),
    y_column: str = Query("Y", description="Y column name or index"),
    z_column: str = Query("Z", description="Z column name or index"),
    delimiter: str = Query(",", description="Column delimiter"),
    has_header: bool = Query(True, description="Whether file has header row")
):
    """
    Transform coordinates from an uploaded CSV file.
    
    Returns the transformed file content.
    """
    import pandas as pd
    
    service = get_crs_service()
    
    # Validate CRS codes
    valid_from, error_from = service.validate_epsg(from_epsg)
    if not valid_from:
        raise HTTPException(status_code=400, detail=error_from)
    
    valid_to, error_to = service.validate_epsg(to_epsg)
    if not valid_to:
        raise HTTPException(status_code=400, detail=error_to)
    
    # Read file
    try:
        content = await file.read()
        df = pd.read_csv(
            io.BytesIO(content),
            delimiter=delimiter,
            header=0 if has_header else None
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Get column names/indices
    try:
        if has_header:
            x_values = df[x_column].values
            y_values = df[y_column].values
            z_values = df[z_column].values if z_column in df.columns else [0.0] * len(df)
        else:
            x_idx = int(x_column) if x_column.isdigit() else 0
            y_idx = int(y_column) if y_column.isdigit() else 1
            z_idx = int(z_column) if z_column.isdigit() else 2
            x_values = df.iloc[:, x_idx].values
            y_values = df.iloc[:, y_idx].values
            z_values = df.iloc[:, z_idx].values if df.shape[1] > z_idx else [0.0] * len(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Column error: {str(e)}")
    
    # Transform points
    points = [(float(x), float(y), float(z)) for x, y, z in zip(x_values, y_values, z_values)]
    result = service.transform_points(points, from_epsg, to_epsg)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=f"Transform failed: {result.errors}")
    
    # Update dataframe
    df[x_column] = [p[0] for p in result.transformed_points]
    df[y_column] = [p[1] for p in result.transformed_points]
    if z_column in df.columns:
        df[z_column] = [p[2] for p in result.transformed_points]
    
    # Return as CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    return {
        "success": True,
        "source_crs": from_epsg,
        "target_crs": to_epsg,
        "points_transformed": len(result.transformed_points),
        "csv_content": output.getvalue()
    }


@router.get("/south-africa")
def list_south_africa_crs():
    """List all South African Lo Grid coordinate systems."""
    service = get_crs_service()
    systems = service.get_crs_for_region("South Africa")
    return [crs_info_to_response(s) for s in systems]


@router.get("/australia")
def list_australia_crs():
    """List all Australian MGA coordinate systems."""
    service = get_crs_service()
    systems = service.get_crs_for_region("Australia")
    return [crs_info_to_response(s) for s in systems]


@router.get("/indonesia")
def list_indonesia_crs():
    """List all Indonesian DGN95 coordinate systems."""
    service = get_crs_service()
    systems = service.get_crs_for_region("Indonesia")
    return [crs_info_to_response(s) for s in systems]


@router.get("/usa")
def list_usa_crs():
    """List all USA NAD83 coordinate systems."""
    service = get_crs_service()
    systems = service.get_crs_for_region("USA")
    return [crs_info_to_response(s) for s in systems]
