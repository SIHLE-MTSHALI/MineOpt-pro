"""
Surface History Service

Temporal surface management, versioning, and comparison.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import math
import logging

from app.domain.models_surface_history import (
    SurfaceVersion, SurfaceComparison, ExcavationProgress
)


class SurfaceHistoryService:
    """Service for managing surface history and comparisons."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # SURFACE VERSIONING
    # =========================================================================
    
    def create_version(
        self,
        surface_id: str,
        version_date: datetime,
        version_name: Optional[str] = None,
        source_type: str = "survey",
        surveyor: Optional[str] = None,
        geometry_path: Optional[str] = None,
        geometry_data: Optional[dict] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> SurfaceVersion:
        """Create a new surface version."""
        # Get next version number
        max_version = self.db.query(func.max(SurfaceVersion.version_number)).filter(
            SurfaceVersion.surface_id == surface_id
        ).scalar() or 0
        
        version = SurfaceVersion(
            surface_id=surface_id,
            version_number=max_version + 1,
            version_name=version_name or f"Version {max_version + 1}",
            version_date=version_date,
            source_type=source_type,
            survey_date=version_date,
            surveyor=surveyor,
            geometry_storage="file" if geometry_path else "inline",
            geometry_path=geometry_path,
            geometry_data=geometry_data,
            notes=notes,
            created_by=created_by
        )
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def get_version(self, version_id: str) -> Optional[SurfaceVersion]:
        """Get version by ID."""
        return self.db.query(SurfaceVersion).filter(
            SurfaceVersion.version_id == version_id
        ).first()
    
    def list_versions(
        self,
        surface_id: str,
        limit: int = 50
    ) -> List[SurfaceVersion]:
        """List all versions of a surface."""
        return self.db.query(SurfaceVersion).filter(
            SurfaceVersion.surface_id == surface_id
        ).order_by(SurfaceVersion.version_date.desc()).limit(limit).all()
    
    def set_current_version(
        self,
        version_id: str
    ) -> SurfaceVersion:
        """Set a version as the current active version."""
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        # Clear current flag from other versions
        self.db.query(SurfaceVersion).filter(
            SurfaceVersion.surface_id == version.surface_id,
            SurfaceVersion.is_current == True
        ).update({'is_current': False})
        
        version.is_current = True
        self.db.commit()
        
        return version
    
    def approve_version(
        self,
        version_id: str,
        approved_by: str
    ) -> SurfaceVersion:
        """Approve a surface version."""
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        version.is_approved = True
        version.approved_by = approved_by
        version.approved_at = datetime.utcnow()
        
        self.db.commit()
        return version
    
    def update_version_stats(
        self,
        version_id: str,
        point_count: int,
        triangle_count: int,
        min_elevation: float,
        max_elevation: float,
        area_m2: float
    ) -> SurfaceVersion:
        """Update statistics for a surface version."""
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        version.point_count = point_count
        version.triangle_count = triangle_count
        version.min_elevation = min_elevation
        version.max_elevation = max_elevation
        version.area_m2 = area_m2
        
        self.db.commit()
        return version
    
    # =========================================================================
    # SURFACE COMPARISON
    # =========================================================================
    
    def compare_surfaces(
        self,
        base_version_id: str,
        compare_version_id: str,
        comparison_name: Optional[str] = None,
        grid_spacing_m: float = 5.0,
        boundary_geojson: Optional[dict] = None,
        created_by: Optional[str] = None
    ) -> SurfaceComparison:
        """Compare two surface versions and calculate volumes."""
        base = self.get_version(base_version_id)
        compare = self.get_version(compare_version_id)
        
        if not base or not compare:
            raise ValueError("One or both versions not found")
        
        # Calculate volume differences
        # In production, this would use actual surface geometry
        # Here we simulate based on metadata
        
        cut_volume = 0.0
        fill_volume = 0.0
        
        if base.min_elevation and compare.min_elevation:
            avg_diff = (compare.min_elevation - base.min_elevation + 
                       compare.max_elevation - base.max_elevation) / 2
            
            area = base.area_m2 or 10000  # Default area if not set
            
            if avg_diff > 0:
                fill_volume = abs(avg_diff) * area
            else:
                cut_volume = abs(avg_diff) * area
        
        comparison = SurfaceComparison(
            base_version_id=base_version_id,
            compare_version_id=compare_version_id,
            comparison_name=comparison_name or f"{base.version_name} vs {compare.version_name}",
            net_volume_bcm=cut_volume - fill_volume,
            cut_volume_bcm=cut_volume,
            fill_volume_bcm=fill_volume,
            max_cut_m=abs(base.min_elevation - compare.min_elevation) if base.min_elevation and compare.min_elevation else 0,
            max_fill_m=abs(base.max_elevation - compare.max_elevation) if base.max_elevation and compare.max_elevation else 0,
            average_difference_m=(cut_volume - fill_volume) / (base.area_m2 or 1),
            comparison_area_m2=base.area_m2,
            boundary_geojson=boundary_geojson,
            grid_spacing_m=grid_spacing_m,
            created_by=created_by
        )
        
        self.db.add(comparison)
        self.db.commit()
        self.db.refresh(comparison)
        
        return comparison
    
    def get_comparison(self, comparison_id: str) -> Optional[SurfaceComparison]:
        """Get comparison by ID."""
        return self.db.query(SurfaceComparison).filter(
            SurfaceComparison.comparison_id == comparison_id
        ).first()
    
    def list_comparisons(
        self,
        surface_id: str,
        limit: int = 20
    ) -> List[SurfaceComparison]:
        """List comparisons involving a surface."""
        version_ids = [v.version_id for v in self.list_versions(surface_id)]
        
        return self.db.query(SurfaceComparison).filter(
            (SurfaceComparison.base_version_id.in_(version_ids)) |
            (SurfaceComparison.compare_version_id.in_(version_ids))
        ).order_by(SurfaceComparison.comparison_date.desc()).limit(limit).all()
    
    # =========================================================================
    # EXCAVATION PROGRESS
    # =========================================================================
    
    def record_progress(
        self,
        site_id: str,
        period_date: datetime,
        period_cut_bcm: float,
        period_fill_bcm: float,
        design_volume_bcm: Optional[float] = None,
        design_surface_id: Optional[str] = None,
        period_type: str = "daily"
    ) -> ExcavationProgress:
        """Record excavation progress for a period."""
        # Get cumulative totals
        prev_progress = self.db.query(ExcavationProgress).filter(
            ExcavationProgress.site_id == site_id,
            ExcavationProgress.period_date < period_date
        ).order_by(ExcavationProgress.period_date.desc()).first()
        
        cumulative_cut = (prev_progress.cumulative_cut_bcm or 0) + period_cut_bcm if prev_progress else period_cut_bcm
        cumulative_fill = (prev_progress.cumulative_fill_bcm or 0) + period_fill_bcm if prev_progress else period_fill_bcm
        
        remaining = design_volume_bcm - cumulative_cut if design_volume_bcm else None
        percent = (cumulative_cut / design_volume_bcm * 100) if design_volume_bcm else None
        
        progress = ExcavationProgress(
            site_id=site_id,
            period_date=period_date,
            period_type=period_type,
            design_surface_id=design_surface_id,
            period_cut_bcm=period_cut_bcm,
            period_fill_bcm=period_fill_bcm,
            cumulative_cut_bcm=cumulative_cut,
            cumulative_fill_bcm=cumulative_fill,
            design_volume_bcm=design_volume_bcm,
            remaining_volume_bcm=remaining,
            percent_complete=percent
        )
        
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        
        return progress
    
    def get_progress_history(
        self,
        site_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ExcavationProgress]:
        """Get excavation progress history."""
        query = self.db.query(ExcavationProgress).filter(
            ExcavationProgress.site_id == site_id
        )
        
        if start_date:
            query = query.filter(ExcavationProgress.period_date >= start_date)
        if end_date:
            query = query.filter(ExcavationProgress.period_date <= end_date)
        
        return query.order_by(ExcavationProgress.period_date).all()
    
    def get_progress_summary(self, site_id: str) -> Dict[str, Any]:
        """Get excavation progress summary."""
        latest = self.db.query(ExcavationProgress).filter(
            ExcavationProgress.site_id == site_id
        ).order_by(ExcavationProgress.period_date.desc()).first()
        
        if not latest:
            return {
                'total_cut_bcm': 0,
                'total_fill_bcm': 0,
                'percent_complete': 0,
                'remaining_bcm': None
            }
        
        return {
            'total_cut_bcm': latest.cumulative_cut_bcm or 0,
            'total_fill_bcm': latest.cumulative_fill_bcm or 0,
            'percent_complete': latest.percent_complete or 0,
            'remaining_bcm': latest.remaining_volume_bcm,
            'design_volume_bcm': latest.design_volume_bcm,
            'last_update': latest.period_date.isoformat() if latest.period_date else None
        }


def get_surface_history_service(db: Session) -> SurfaceHistoryService:
    return SurfaceHistoryService(db)
