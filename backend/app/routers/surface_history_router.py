"""
Surface History REST API Router

Endpoints for surface versioning, comparison, and progress tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.services.surface_history_service import (
    SurfaceHistoryService, get_surface_history_service
)


router = APIRouter(prefix="/surfaces", tags=["Surface History"])


# Schemas
class VersionCreate(BaseModel):
    surface_id: str
    version_date: datetime
    version_name: Optional[str] = None
    source_type: str = "survey"
    surveyor: Optional[str] = None
    geometry_path: Optional[str] = None
    notes: Optional[str] = None


class VersionResponse(BaseModel):
    version_id: str
    surface_id: str
    version_number: int
    version_name: Optional[str]
    version_date: datetime
    source_type: Optional[str]
    is_current: bool
    is_approved: bool
    point_count: Optional[int]
    triangle_count: Optional[int]
    volume_change_bcm: Optional[float]
    
    class Config:
        from_attributes = True


class VersionStatsUpdate(BaseModel):
    point_count: int
    triangle_count: int
    min_elevation: float
    max_elevation: float
    area_m2: float


class CompareRequest(BaseModel):
    base_version_id: str
    compare_version_id: str
    comparison_name: Optional[str] = None
    grid_spacing_m: float = 5.0
    boundary_geojson: Optional[dict] = None


class ComparisonResponse(BaseModel):
    comparison_id: str
    comparison_name: Optional[str]
    net_volume_bcm: Optional[float]
    cut_volume_bcm: Optional[float]
    fill_volume_bcm: Optional[float]
    max_cut_m: Optional[float]
    max_fill_m: Optional[float]
    comparison_date: datetime
    
    class Config:
        from_attributes = True


class ProgressRecord(BaseModel):
    site_id: str
    period_date: datetime
    period_cut_bcm: float
    period_fill_bcm: float
    design_volume_bcm: Optional[float] = None
    design_surface_id: Optional[str] = None
    period_type: str = "daily"


class ProgressResponse(BaseModel):
    progress_id: str
    period_date: datetime
    period_cut_bcm: Optional[float]
    period_fill_bcm: Optional[float]
    cumulative_cut_bcm: Optional[float]
    percent_complete: Optional[float]
    
    class Config:
        from_attributes = True


# Version Endpoints
@router.post("/versions", response_model=VersionResponse)
def create_version(data: VersionCreate, db: Session = Depends(get_db)):
    """Create a new surface version."""
    service = get_surface_history_service(db)
    version = service.create_version(
        surface_id=data.surface_id,
        version_date=data.version_date,
        version_name=data.version_name,
        source_type=data.source_type,
        surveyor=data.surveyor,
        geometry_path=data.geometry_path,
        notes=data.notes
    )
    return VersionResponse(
        version_id=version.version_id,
        surface_id=version.surface_id,
        version_number=version.version_number,
        version_name=version.version_name,
        version_date=version.version_date,
        source_type=version.source_type,
        is_current=version.is_current,
        is_approved=version.is_approved,
        point_count=version.point_count,
        triangle_count=version.triangle_count,
        volume_change_bcm=version.volume_change_bcm
    )


@router.get("/{surface_id}/history", response_model=List[VersionResponse])
def list_surface_versions(
    surface_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all versions of a surface."""
    service = get_surface_history_service(db)
    versions = service.list_versions(surface_id, limit)
    return [
        VersionResponse(
            version_id=v.version_id,
            surface_id=v.surface_id,
            version_number=v.version_number,
            version_name=v.version_name,
            version_date=v.version_date,
            source_type=v.source_type,
            is_current=v.is_current,
            is_approved=v.is_approved,
            point_count=v.point_count,
            triangle_count=v.triangle_count,
            volume_change_bcm=v.volume_change_bcm
        )
        for v in versions
    ]


@router.get("/versions/{version_id}", response_model=VersionResponse)
def get_version(version_id: str, db: Session = Depends(get_db)):
    """Get a specific surface version."""
    service = get_surface_history_service(db)
    version = service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return VersionResponse(
        version_id=version.version_id,
        surface_id=version.surface_id,
        version_number=version.version_number,
        version_name=version.version_name,
        version_date=version.version_date,
        source_type=version.source_type,
        is_current=version.is_current,
        is_approved=version.is_approved,
        point_count=version.point_count,
        triangle_count=version.triangle_count,
        volume_change_bcm=version.volume_change_bcm
    )


@router.post("/versions/{version_id}/set-current")
def set_current_version(version_id: str, db: Session = Depends(get_db)):
    """Set a version as the current active version."""
    service = get_surface_history_service(db)
    try:
        service.set_current_version(version_id)
        return {"message": "Version set as current", "version_id": version_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/versions/{version_id}/approve")
def approve_version(
    version_id: str,
    approved_by: str = Query(...),
    db: Session = Depends(get_db)
):
    """Approve a surface version."""
    service = get_surface_history_service(db)
    try:
        service.approve_version(version_id, approved_by)
        return {"message": "Version approved", "version_id": version_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/versions/{version_id}/stats")
def update_version_stats(
    version_id: str,
    data: VersionStatsUpdate,
    db: Session = Depends(get_db)
):
    """Update statistics for a surface version."""
    service = get_surface_history_service(db)
    try:
        service.update_version_stats(
            version_id,
            data.point_count,
            data.triangle_count,
            data.min_elevation,
            data.max_elevation,
            data.area_m2
        )
        return {"message": "Stats updated", "version_id": version_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Comparison Endpoints
@router.post("/compare", response_model=ComparisonResponse)
def compare_surfaces(data: CompareRequest, db: Session = Depends(get_db)):
    """Compare two surface versions."""
    service = get_surface_history_service(db)
    try:
        comparison = service.compare_surfaces(
            base_version_id=data.base_version_id,
            compare_version_id=data.compare_version_id,
            comparison_name=data.comparison_name,
            grid_spacing_m=data.grid_spacing_m,
            boundary_geojson=data.boundary_geojson
        )
        return ComparisonResponse(
            comparison_id=comparison.comparison_id,
            comparison_name=comparison.comparison_name,
            net_volume_bcm=comparison.net_volume_bcm,
            cut_volume_bcm=comparison.cut_volume_bcm,
            fill_volume_bcm=comparison.fill_volume_bcm,
            max_cut_m=comparison.max_cut_m,
            max_fill_m=comparison.max_fill_m,
            comparison_date=comparison.comparison_date
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse)
def get_comparison(comparison_id: str, db: Session = Depends(get_db)):
    """Get a comparison result."""
    service = get_surface_history_service(db)
    comparison = service.get_comparison(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return ComparisonResponse(
        comparison_id=comparison.comparison_id,
        comparison_name=comparison.comparison_name,
        net_volume_bcm=comparison.net_volume_bcm,
        cut_volume_bcm=comparison.cut_volume_bcm,
        fill_volume_bcm=comparison.fill_volume_bcm,
        max_cut_m=comparison.max_cut_m,
        max_fill_m=comparison.max_fill_m,
        comparison_date=comparison.comparison_date
    )


@router.get("/{surface_id}/comparisons", response_model=List[ComparisonResponse])
def list_comparisons(
    surface_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List comparisons for a surface."""
    service = get_surface_history_service(db)
    comparisons = service.list_comparisons(surface_id, limit)
    return [
        ComparisonResponse(
            comparison_id=c.comparison_id,
            comparison_name=c.comparison_name,
            net_volume_bcm=c.net_volume_bcm,
            cut_volume_bcm=c.cut_volume_bcm,
            fill_volume_bcm=c.fill_volume_bcm,
            max_cut_m=c.max_cut_m,
            max_fill_m=c.max_fill_m,
            comparison_date=c.comparison_date
        )
        for c in comparisons
    ]


# Progress Endpoints
@router.post("/progress", response_model=ProgressResponse)
def record_progress(data: ProgressRecord, db: Session = Depends(get_db)):
    """Record excavation progress."""
    service = get_surface_history_service(db)
    progress = service.record_progress(
        site_id=data.site_id,
        period_date=data.period_date,
        period_cut_bcm=data.period_cut_bcm,
        period_fill_bcm=data.period_fill_bcm,
        design_volume_bcm=data.design_volume_bcm,
        design_surface_id=data.design_surface_id,
        period_type=data.period_type
    )
    return ProgressResponse(
        progress_id=progress.progress_id,
        period_date=progress.period_date,
        period_cut_bcm=progress.period_cut_bcm,
        period_fill_bcm=progress.period_fill_bcm,
        cumulative_cut_bcm=progress.cumulative_cut_bcm,
        percent_complete=progress.percent_complete
    )


@router.get("/sites/{site_id}/progress", response_model=List[ProgressResponse])
def get_progress_history(
    site_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get excavation progress history."""
    service = get_surface_history_service(db)
    progress_list = service.get_progress_history(site_id, start_date, end_date)
    return [
        ProgressResponse(
            progress_id=p.progress_id,
            period_date=p.period_date,
            period_cut_bcm=p.period_cut_bcm,
            period_fill_bcm=p.period_fill_bcm,
            cumulative_cut_bcm=p.cumulative_cut_bcm,
            percent_complete=p.percent_complete
        )
        for p in progress_list
    ]


@router.get("/sites/{site_id}/progress/summary")
def get_progress_summary(site_id: str, db: Session = Depends(get_db)):
    """Get excavation progress summary."""
    service = get_surface_history_service(db)
    return service.get_progress_summary(site_id)
