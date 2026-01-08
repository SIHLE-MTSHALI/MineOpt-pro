"""
Surface History Domain Models

Models for temporal surface tracking and comparison.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class SurfaceVersion(Base):
    """A historical version of a surface."""
    __tablename__ = "surface_versions"
    
    version_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    surface_id = Column(String(36), ForeignKey("surfaces.surface_id"), nullable=False)
    
    # Version metadata
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(100))
    version_date = Column(DateTime, nullable=False)
    
    # Source information
    source_type = Column(String(50))  # survey, design, as_built, drone
    survey_date = Column(DateTime)
    surveyor = Column(String(100))
    
    # Statistics at this version
    point_count = Column(Integer)
    triangle_count = Column(Integer)
    min_elevation = Column(Float)
    max_elevation = Column(Float)
    area_m2 = Column(Float)
    
    # Geometry storage
    # Could be path to file, or inline JSON for small surfaces
    geometry_storage = Column(String(50), default="file")  # file, inline
    geometry_path = Column(String(500))
    geometry_data = Column(JSON)  # For inline storage
    
    # Comparison with previous version
    volume_change_bcm = Column(Float)
    volume_cut_bcm = Column(Float)
    volume_fill_bcm = Column(Float)
    
    # Status
    is_current = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))


class SurfaceComparison(Base):
    """Comparison result between two surface versions."""
    __tablename__ = "surface_comparisons"
    
    comparison_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Surfaces being compared
    base_version_id = Column(String(36), ForeignKey("surface_versions.version_id"), nullable=False)
    compare_version_id = Column(String(36), ForeignKey("surface_versions.version_id"), nullable=False)
    
    # Comparison metadata
    comparison_name = Column(String(100))
    comparison_date = Column(DateTime, default=datetime.utcnow)
    
    # Volume results
    net_volume_bcm = Column(Float)  # Positive = cut, Negative = fill
    cut_volume_bcm = Column(Float)
    fill_volume_bcm = Column(Float)
    
    # Statistics
    max_cut_m = Column(Float)
    max_fill_m = Column(Float)
    average_difference_m = Column(Float)
    comparison_area_m2 = Column(Float)
    
    # Boundary for comparison (GeoJSON)
    boundary_geojson = Column(JSON)
    
    # Grid resolution used
    grid_spacing_m = Column(Float)
    
    # Result storage
    difference_grid_path = Column(String(500))  # Path to difference raster
    isopach_contours = Column(JSON)  # Contour data
    
    # Status
    status = Column(String(20), default="completed")  # pending, completed, failed
    error_message = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))


class ExcavationProgress(Base):
    """Cumulative excavation progress tracking."""
    __tablename__ = "excavation_progress"
    
    progress_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Period
    period_date = Column(DateTime, nullable=False)
    period_type = Column(String(20))  # daily, weekly, monthly
    
    # Design surface reference
    design_surface_id = Column(String(36), ForeignKey("surfaces.surface_id"))
    
    # Volumes
    period_cut_bcm = Column(Float)
    period_fill_bcm = Column(Float)
    cumulative_cut_bcm = Column(Float)
    cumulative_fill_bcm = Column(Float)
    
    # Progress
    design_volume_bcm = Column(Float)
    remaining_volume_bcm = Column(Float)
    percent_complete = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
