"""
Borehole Domain Models - Phase 2 Borehole Data Workflows

SQLAlchemy models for borehole data management:
- BoreholeCollar: Surface location and orientation
- BoreholeSurvey: Downhole deviation measurements
- BoreholeInterval: Depth intervals for lithology/quality
- BoreholeAssay: Quality measurements by interval

These models support importing data from Surpac, Vulcan, Minex, GeoBank,
and generic CSV formats.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
from datetime import datetime


class BoreholeCollar(Base):
    """
    Borehole collar - the surface location and metadata of a drillhole.
    
    This is the primary entry point for borehole data, with surveys,
    intervals, and assays linked through the collar_id.
    """
    __tablename__ = "borehole_collars"
    
    collar_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    hole_id = Column(String, nullable=False, index=True)  # User-facing ID (e.g., "BH001")
    hole_name = Column(String, nullable=True)
    
    # Location (coordinates)
    easting = Column(Float, nullable=False)   # X coordinate
    northing = Column(Float, nullable=False)  # Y coordinate
    elevation = Column(Float, nullable=False)  # Collar RL (surface elevation)
    
    # Orientation (for angled holes)
    azimuth = Column(Float, default=0.0)  # Compass direction (0-360°)
    dip = Column(Float, default=-90.0)    # Angle from horizontal (-90 = vertical down)
    
    # Depth
    total_depth = Column(Float, nullable=True)  # End-of-hole (EOH) depth
    planned_depth = Column(Float, nullable=True)
    
    # Status and type
    status = Column(String, default="Active")  # Active, Completed, Abandoned
    hole_type = Column(String, default="Exploration")  # Exploration, Grade Control, Geotechnical
    
    # Drilling information
    drill_date = Column(DateTime, nullable=True)
    drill_company = Column(String, nullable=True)
    drill_method = Column(String, nullable=True)  # RC, Diamond, Rotary
    
    # Coordinate system reference
    coordinate_system = Column(String, nullable=True)  # e.g., "MGA94 Zone 56"
    
    # Source tracking
    source_file = Column(String, nullable=True)
    source_format = Column(String, nullable=True)  # Vulcan, Minex, Surpac, CSV
    import_date = Column(DateTime, default=datetime.utcnow)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("Site")
    surveys = relationship("BoreholeSurvey", back_populates="collar", cascade="all, delete-orphan")
    intervals = relationship("BoreholeInterval", back_populates="collar", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BoreholeCollar {self.hole_id}>"
    
    @property
    def x(self) -> float:
        """Alias for easting."""
        return self.easting
    
    @property
    def y(self) -> float:
        """Alias for northing."""
        return self.northing
    
    @property
    def z(self) -> float:
        """Alias for elevation."""
        return self.elevation


class BoreholeSurvey(Base):
    """
    Borehole survey - downhole deviation measurements.
    
    Surveys define the 3D path of the borehole by recording azimuth
    and dip at specified depths. Used to calculate the true position
    of intervals below ground.
    """
    __tablename__ = "borehole_surveys"
    
    survey_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collar_id = Column(String, ForeignKey("borehole_collars.collar_id"), nullable=False)
    
    # Measurement depth (measured depth, not vertical depth)
    depth = Column(Float, nullable=False)
    
    # Orientation at this depth
    azimuth = Column(Float, nullable=False)  # Compass direction (0-360°)
    dip = Column(Float, nullable=False)      # Angle from horizontal
    
    # Survey method
    survey_method = Column(String, nullable=True)  # Gyro, EMS, Magnetic, Assumed
    
    # Quality indicators
    is_reliable = Column(Boolean, default=True)
    quality_code = Column(String, nullable=True)
    
    # Calculated coordinates (3D position at this depth)
    calc_easting = Column(Float, nullable=True)
    calc_northing = Column(Float, nullable=True)
    calc_elevation = Column(Float, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    collar = relationship("BoreholeCollar", back_populates="surveys")
    
    def __repr__(self):
        return f"<BoreholeSurvey {self.collar_id[:8]}... @ {self.depth}m>"


class BoreholeInterval(Base):
    """
    Borehole interval - a depth range for lithology, assay, or other data.
    
    Intervals define the from/to depths for geological observations
    and quality measurements. Can represent coal seams, waste zones,
    or sample intervals.
    """
    __tablename__ = "borehole_intervals"
    
    interval_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collar_id = Column(String, ForeignKey("borehole_collars.collar_id"), nullable=False)
    
    # Depth range (measured depths)
    from_depth = Column(Float, nullable=False)
    to_depth = Column(Float, nullable=False)
    
    # Calculated thickness
    @property
    def thickness(self) -> float:
        return self.to_depth - self.from_depth
    
    # Interval type
    interval_type = Column(String, default="Assay")  # Assay, Lithology, Composite
    
    # Lithology/Geology
    lithology_code = Column(String, nullable=True)  # Coal, Waste, Sandstone, etc.
    lithology_description = Column(String, nullable=True)
    
    # Seam identification (for coal)
    seam_name = Column(String, nullable=True)  # Upper, Lower, Main, A-Seam
    seam_code = Column(String, nullable=True)
    
    # Material type linkage
    material_type_id = Column(String, ForeignKey("material_types.material_type_id"), nullable=True)
    
    # Sample info
    sample_id = Column(String, nullable=True)
    sample_type = Column(String, nullable=True)  # Core, Chip, Composite
    
    # Recovery (for core drilling)
    core_recovery = Column(Float, nullable=True)  # Percentage 0-100
    
    # Quality data (stored as JSON for flexibility)
    quality_vector = Column(JSON, nullable=True)
    # Example: {"CV_ARB": 24.5, "Ash_ADB": 12.0, "TS_ARB": 0.45}
    
    # Washability reference (if available)
    washability_id = Column(String, nullable=True)
    
    # Calculated 3D coordinates (midpoint of interval)
    calc_easting = Column(Float, nullable=True)
    calc_northing = Column(Float, nullable=True)
    calc_elevation = Column(Float, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    collar = relationship("BoreholeCollar", back_populates="intervals")
    material_type = relationship("MaterialType")
    assays = relationship("BoreholeAssay", back_populates="interval", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BoreholeInterval {self.from_depth}-{self.to_depth}m>"
    
    def get_quality(self, field_name: str, default: float = 0.0) -> float:
        """Get a quality value from the vector."""
        if self.quality_vector:
            return self.quality_vector.get(field_name, default)
        return default


class BoreholeAssay(Base):
    """
    Borehole assay - individual quality measurements.
    
    Stores individual quality field values for an interval.
    This normalized structure allows for flexible quality fields
    while the interval's quality_vector stores the denormalized view.
    """
    __tablename__ = "borehole_assays"
    
    assay_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interval_id = Column(String, ForeignKey("borehole_intervals.interval_id"), nullable=False)
    
    # Quality field reference
    quality_field_id = Column(String, ForeignKey("quality_fields.quality_field_id"), nullable=True)
    quality_field_name = Column(String, nullable=False)  # e.g., "CV_ARB", "Ash_ADB"
    
    # The measured value
    value = Column(Float, nullable=False)
    
    # Units (denormalized for convenience)
    units = Column(String, nullable=True)  # MJ/kg, %, ppm
    
    # Analysis metadata
    analysis_date = Column(DateTime, nullable=True)
    lab_code = Column(String, nullable=True)
    analysis_method = Column(String, nullable=True)
    
    # Quality status
    is_valid = Column(Boolean, default=True)
    qc_flag = Column(String, nullable=True)  # OK, Suspect, Reanalysis
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interval = relationship("BoreholeInterval", back_populates="assays")
    quality_field = relationship("QualityField")
    
    def __repr__(self):
        return f"<BoreholeAssay {self.quality_field_name}={self.value}>"


class Borehole3DTrace(Base):
    """
    Pre-calculated 3D trace points for a borehole.
    
    Stores the calculated XYZ coordinates along the borehole path,
    derived from collar location and survey data. Used for visualization
    and spatial queries.
    """
    __tablename__ = "borehole_3d_traces"
    
    trace_point_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collar_id = Column(String, ForeignKey("borehole_collars.collar_id"), nullable=False)
    
    # Sequence along trace
    sequence = Column(Integer, nullable=False)
    
    # Depth (measured depth from collar)
    depth = Column(Float, nullable=False)
    
    # Calculated 3D coordinates
    easting = Column(Float, nullable=False)
    northing = Column(Float, nullable=False)
    elevation = Column(Float, nullable=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    collar = relationship("BoreholeCollar")
    
    def __repr__(self):
        return f"<Borehole3DTrace {self.depth}m @ ({self.easting:.1f}, {self.northing:.1f}, {self.elevation:.1f})>"
    
    @property
    def x(self) -> float:
        return self.easting
    
    @property
    def y(self) -> float:
        return self.northing
    
    @property
    def z(self) -> float:
        return self.elevation
