"""
Borehole Router - Phase 2 Borehole Data Workflows

REST API endpoints for borehole data management:
- POST /boreholes/import - Import borehole data from files
- GET /boreholes/{site_id} - List boreholes for a site
- GET /boreholes/{collar_id}/details - Get borehole details with intervals
- GET /boreholes/{collar_id}/trace - Get 3D trace coordinates
- DELETE /boreholes/{collar_id} - Delete a borehole
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.borehole_import_service import get_borehole_import_service, BoreholeImportResult
from ..domain.models_borehole import (
    BoreholeCollar, BoreholeSurvey, BoreholeInterval, 
    BoreholeAssay, Borehole3DTrace
)


router = APIRouter(prefix="/boreholes", tags=["Boreholes"])


# Response Models

class ImportErrorResponse(BaseModel):
    """Import error/warning in response."""
    hole_id: str
    field: str
    message: str
    row_number: Optional[int]
    severity: str


class BoreholeImportResponse(BaseModel):
    """Response from borehole import operation."""
    success: bool
    collars_imported: int
    surveys_imported: int
    intervals_imported: int
    assays_imported: int
    traces_calculated: int
    errors: List[ImportErrorResponse]
    warnings: List[ImportErrorResponse]
    collar_ids: List[str]


class CollarSummaryResponse(BaseModel):
    """Summary of a borehole collar."""
    collar_id: str
    hole_id: str
    easting: float
    northing: float
    elevation: float
    total_depth: Optional[float]
    hole_type: str
    interval_count: int
    has_surveys: bool


class SurveyResponse(BaseModel):
    """Survey measurement response."""
    survey_id: str
    depth: float
    azimuth: float
    dip: float


class IntervalResponse(BaseModel):
    """Interval response with quality data."""
    interval_id: str
    from_depth: float
    to_depth: float
    thickness: float
    seam_name: Optional[str]
    lithology_code: Optional[str]
    quality_vector: Optional[Dict[str, float]]


class TracePointResponse(BaseModel):
    """3D trace point response."""
    sequence: int
    depth: float
    easting: float
    northing: float
    elevation: float


class BoreholeDetailResponse(BaseModel):
    """Full borehole details."""
    collar_id: str
    hole_id: str
    hole_name: Optional[str]
    easting: float
    northing: float
    elevation: float
    azimuth: float
    dip: float
    total_depth: Optional[float]
    hole_type: str
    status: str
    source_format: Optional[str]
    source_file: Optional[str]
    surveys: List[SurveyResponse]
    intervals: List[IntervalResponse]
    trace_point_count: int


# Endpoints

@router.post("/import", response_model=BoreholeImportResponse)
async def import_boreholes(
    site_id: str = Form(...),
    collar_file: UploadFile = File(..., description="Collar CSV file"),
    survey_file: Optional[UploadFile] = File(None, description="Optional survey CSV file"),
    assay_file: Optional[UploadFile] = File(None, description="Optional assay CSV file"),
    source_format: str = Form("CSV"),
    db: Session = Depends(get_db)
):
    """
    Import borehole data from CSV files.
    
    Supports Vulcan, Minex, Surpac, and GeoBank CSV formats.
    
    Required:
    - site_id: Target site ID
    - collar_file: CSV with collar locations (HoleID, Easting, Northing, Elevation)
    
    Optional:
    - survey_file: CSV with deviation surveys (HoleID, Depth, Azimuth, Dip)
    - assay_file: CSV with quality data (HoleID, From, To, quality columns...)
    """
    service = get_borehole_import_service(db)
    
    # Read file contents
    collar_content = await collar_file.read()
    
    survey_content = None
    survey_filename = None
    if survey_file:
        survey_content = await survey_file.read()
        survey_filename = survey_file.filename
    
    assay_content = None
    assay_filename = None
    if assay_file:
        assay_content = await assay_file.read()
        assay_filename = assay_file.filename
    
    # Import
    result = service.import_boreholes(
        site_id=site_id,
        collar_content=collar_content,
        collar_filename=collar_file.filename,
        survey_content=survey_content,
        survey_filename=survey_filename,
        assay_content=assay_content,
        assay_filename=assay_filename,
        source_format=source_format
    )
    
    # Convert to response
    return BoreholeImportResponse(
        success=result.success,
        collars_imported=result.collars_imported,
        surveys_imported=result.surveys_imported,
        intervals_imported=result.intervals_imported,
        assays_imported=result.assays_imported,
        traces_calculated=result.traces_calculated,
        errors=[
            ImportErrorResponse(
                hole_id=e.hole_id,
                field=e.field,
                message=e.message,
                row_number=e.row_number,
                severity=e.severity
            ) for e in result.errors
        ],
        warnings=[
            ImportErrorResponse(
                hole_id=e.hole_id,
                field=e.field,
                message=e.message,
                row_number=e.row_number,
                severity=e.severity
            ) for e in result.warnings
        ],
        collar_ids=result.collar_ids
    )


@router.get("/site/{site_id}", response_model=List[CollarSummaryResponse])
async def list_boreholes(
    site_id: str,
    hole_type: Optional[str] = Query(None, description="Filter by hole type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """List all boreholes for a site."""
    query = db.query(BoreholeCollar).filter(BoreholeCollar.site_id == site_id)
    
    if hole_type:
        query = query.filter(BoreholeCollar.hole_type == hole_type)
    if status:
        query = query.filter(BoreholeCollar.status == status)
    
    collars = query.order_by(BoreholeCollar.hole_id).all()
    
    results = []
    for collar in collars:
        interval_count = db.query(BoreholeInterval).filter(
            BoreholeInterval.collar_id == collar.collar_id
        ).count()
        
        has_surveys = db.query(BoreholeSurvey).filter(
            BoreholeSurvey.collar_id == collar.collar_id
        ).first() is not None
        
        results.append(CollarSummaryResponse(
            collar_id=collar.collar_id,
            hole_id=collar.hole_id,
            easting=collar.easting,
            northing=collar.northing,
            elevation=collar.elevation,
            total_depth=collar.total_depth,
            hole_type=collar.hole_type,
            interval_count=interval_count,
            has_surveys=has_surveys
        ))
    
    return results


@router.get("/{collar_id}", response_model=BoreholeDetailResponse)
async def get_borehole_details(
    collar_id: str,
    db: Session = Depends(get_db)
):
    """Get full details for a borehole including surveys and intervals."""
    collar = db.query(BoreholeCollar).filter(
        BoreholeCollar.collar_id == collar_id
    ).first()
    
    if not collar:
        raise HTTPException(404, "Borehole not found")
    
    # Get surveys
    surveys = db.query(BoreholeSurvey).filter(
        BoreholeSurvey.collar_id == collar_id
    ).order_by(BoreholeSurvey.depth).all()
    
    # Get intervals
    intervals = db.query(BoreholeInterval).filter(
        BoreholeInterval.collar_id == collar_id
    ).order_by(BoreholeInterval.from_depth).all()
    
    # Get trace count
    trace_count = db.query(Borehole3DTrace).filter(
        Borehole3DTrace.collar_id == collar_id
    ).count()
    
    return BoreholeDetailResponse(
        collar_id=collar.collar_id,
        hole_id=collar.hole_id,
        hole_name=collar.hole_name,
        easting=collar.easting,
        northing=collar.northing,
        elevation=collar.elevation,
        azimuth=collar.azimuth,
        dip=collar.dip,
        total_depth=collar.total_depth,
        hole_type=collar.hole_type,
        status=collar.status,
        source_format=collar.source_format,
        source_file=collar.source_file,
        surveys=[
            SurveyResponse(
                survey_id=s.survey_id,
                depth=s.depth,
                azimuth=s.azimuth,
                dip=s.dip
            ) for s in surveys
        ],
        intervals=[
            IntervalResponse(
                interval_id=i.interval_id,
                from_depth=i.from_depth,
                to_depth=i.to_depth,
                thickness=i.thickness,
                seam_name=i.seam_name,
                lithology_code=i.lithology_code,
                quality_vector=i.quality_vector
            ) for i in intervals
        ],
        trace_point_count=trace_count
    )


@router.get("/{collar_id}/trace", response_model=List[TracePointResponse])
async def get_borehole_trace(
    collar_id: str,
    db: Session = Depends(get_db)
):
    """Get the 3D trace coordinates for a borehole."""
    collar = db.query(BoreholeCollar).filter(
        BoreholeCollar.collar_id == collar_id
    ).first()
    
    if not collar:
        raise HTTPException(404, "Borehole not found")
    
    traces = db.query(Borehole3DTrace).filter(
        Borehole3DTrace.collar_id == collar_id
    ).order_by(Borehole3DTrace.sequence).all()
    
    return [
        TracePointResponse(
            sequence=t.sequence,
            depth=t.depth,
            easting=t.easting,
            northing=t.northing,
            elevation=t.elevation
        ) for t in traces
    ]


@router.get("/{collar_id}/assays/{quality_field}")
async def get_borehole_assays(
    collar_id: str,
    quality_field: str,
    db: Session = Depends(get_db)
):
    """
    Get assay values for a specific quality field.
    
    Returns depth vs value data suitable for plotting.
    """
    collar = db.query(BoreholeCollar).filter(
        BoreholeCollar.collar_id == collar_id
    ).first()
    
    if not collar:
        raise HTTPException(404, "Borehole not found")
    
    intervals = db.query(BoreholeInterval).filter(
        BoreholeInterval.collar_id == collar_id
    ).order_by(BoreholeInterval.from_depth).all()
    
    data = []
    for interval in intervals:
        if interval.quality_vector and quality_field in interval.quality_vector:
            data.append({
                "from_depth": interval.from_depth,
                "to_depth": interval.to_depth,
                "mid_depth": (interval.from_depth + interval.to_depth) / 2,
                "value": interval.quality_vector[quality_field],
                "seam": interval.seam_name
            })
    
    return {
        "hole_id": collar.hole_id,
        "quality_field": quality_field,
        "data": data
    }


@router.delete("/{collar_id}")
async def delete_borehole(
    collar_id: str,
    db: Session = Depends(get_db)
):
    """Delete a borehole and all related data."""
    collar = db.query(BoreholeCollar).filter(
        BoreholeCollar.collar_id == collar_id
    ).first()
    
    if not collar:
        raise HTTPException(404, "Borehole not found")
    
    # Delete related trace records
    db.query(Borehole3DTrace).filter(
        Borehole3DTrace.collar_id == collar_id
    ).delete()
    
    # Cascade delete will handle surveys, intervals, assays
    db.delete(collar)
    db.commit()
    
    return {"message": f"Borehole {collar.hole_id} deleted"}


@router.get("/site/{site_id}/quality-summary")
async def get_quality_summary(
    site_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a summary of quality data across all boreholes for a site.
    
    Returns available quality fields and basic statistics.
    """
    # Get all intervals for the site
    collars = db.query(BoreholeCollar.collar_id).filter(
        BoreholeCollar.site_id == site_id
    ).all()
    collar_ids = [c.collar_id for c in collars]
    
    if not collar_ids:
        return {"quality_fields": [], "borehole_count": 0, "interval_count": 0}
    
    intervals = db.query(BoreholeInterval).filter(
        BoreholeInterval.collar_id.in_(collar_ids)
    ).all()
    
    # Collect all quality fields
    quality_stats: Dict[str, Dict[str, Any]] = {}
    
    for interval in intervals:
        if interval.quality_vector:
            for field, value in interval.quality_vector.items():
                if field not in quality_stats:
                    quality_stats[field] = {
                        "count": 0,
                        "min": float('inf'),
                        "max": float('-inf'),
                        "sum": 0
                    }
                
                stats = quality_stats[field]
                stats["count"] += 1
                stats["min"] = min(stats["min"], value)
                stats["max"] = max(stats["max"], value)
                stats["sum"] += value
    
    # Calculate averages
    quality_fields = []
    for field, stats in quality_stats.items():
        if stats["count"] > 0:
            quality_fields.append({
                "name": field,
                "count": stats["count"],
                "min": stats["min"],
                "max": stats["max"],
                "avg": stats["sum"] / stats["count"]
            })
    
    return {
        "borehole_count": len(collar_ids),
        "interval_count": len(intervals),
        "quality_fields": quality_fields
    }
