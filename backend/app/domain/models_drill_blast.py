"""
Drill & Blast Domain Models

Models for drill patterns, blast events, and fragmentation.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.database import Base


class DrillHoleStatus(str, enum.Enum):
    """Status of a drill hole."""
    PLANNED = "planned"
    DRILLED = "drilled"
    LOADED = "loaded"
    DETONATED = "detonated"
    CANCELLED = "cancelled"


class ExplosiveType(str, enum.Enum):
    """Types of explosives."""
    ANFO = "anfo"
    EMULSION = "emulsion"
    HEAVY_ANFO = "heavy_anfo"
    WATERGEL = "watergel"
    DYNAMITE = "dynamite"
    ELECTRONIC = "electronic"


class BlastPattern(Base):
    """Drill and blast pattern definition."""
    __tablename__ = "blast_patterns"
    
    pattern_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Location
    bench_id = Column(String(36))
    bench_name = Column(String(100))
    block_name = Column(String(100))
    
    # Pattern geometry
    pattern_type = Column(String(50), default="rectangular")  # rectangular, staggered, radial
    burden = Column(Float, nullable=False)  # Distance to free face (m)
    spacing = Column(Float, nullable=False)  # Distance between holes in row (m)
    num_rows = Column(Integer, nullable=False)
    num_holes_per_row = Column(Integer, nullable=False)
    
    # Hole specifications
    hole_diameter_mm = Column(Float, default=165)
    hole_depth_m = Column(Float, nullable=False)
    subdrill_m = Column(Float, default=0.5)  # Extra depth below bench floor
    
    # Stemming
    stemming_height_m = Column(Float, default=3.0)
    stemming_material = Column(String(50), default="drill_cuttings")
    
    # Explosive
    explosive_type = Column(Enum(ExplosiveType), default=ExplosiveType.ANFO)
    powder_factor_kg_bcm = Column(Float)  # Calculated
    
    # Pattern orientation
    orientation_degrees = Column(Float, default=0)  # Pattern rotation
    origin_x = Column(Float)  # Pattern origin easting
    origin_y = Column(Float)  # Pattern origin northing
    origin_z = Column(Float)  # Pattern origin elevation (bench level)
    
    # Status
    status = Column(String(50), default="draft")  # draft, approved, drilled, loaded, fired
    
    # Metadata
    designed_by = Column(String(100))
    designed_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    holes = relationship("DrillHole", back_populates="pattern", cascade="all, delete-orphan")
    blast_event = relationship("BlastEvent", back_populates="pattern", uselist=False)


class DrillHole(Base):
    """Individual drill hole within a pattern."""
    __tablename__ = "drill_holes"
    
    hole_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pattern_id = Column(String(36), ForeignKey("blast_patterns.pattern_id"), nullable=False)
    
    # Identification
    hole_number = Column(Integer, nullable=False)
    row_number = Column(Integer)
    hole_in_row = Column(Integer)
    
    # Design position
    design_x = Column(Float, nullable=False)
    design_y = Column(Float, nullable=False)
    design_z = Column(Float)  # Collar elevation
    
    # Design parameters
    design_depth_m = Column(Float, nullable=False)
    design_angle_degrees = Column(Float, default=90)  # 90 = vertical
    design_azimuth_degrees = Column(Float, default=0)
    design_diameter_mm = Column(Float)
    
    # Actual drilled (from survey)
    actual_x = Column(Float)
    actual_y = Column(Float)
    actual_z = Column(Float)
    actual_depth_m = Column(Float)
    actual_angle_degrees = Column(Float)
    actual_azimuth_degrees = Column(Float)
    
    # Drilling info
    drilled_at = Column(DateTime)
    drilled_by = Column(String(100))
    drill_rig_id = Column(String(36))
    penetration_rate_m_hr = Column(Float)
    
    # Loading
    charge_weight_kg = Column(Float)
    explosive_type = Column(Enum(ExplosiveType))
    primer_type = Column(String(50))
    detonator_type = Column(String(50))
    detonator_delay_ms = Column(Integer)  # Delay in milliseconds
    
    deck_charge = Column(Boolean, default=False)
    deck_configuration = Column(JSON)  # List of deck details if applicable
    
    stemming_height_m = Column(Float)
    loaded_at = Column(DateTime)
    loaded_by = Column(String(100))
    
    # Status
    status = Column(Enum(DrillHoleStatus), default=DrillHoleStatus.PLANNED)
    
    # QA/QC
    water_present = Column(Boolean, default=False)
    cavity_detected = Column(Boolean, default=False)
    notes = Column(Text)
    
    # Relationship
    pattern = relationship("BlastPattern", back_populates="holes")


class BlastEvent(Base):
    """Blast execution event."""
    __tablename__ = "blast_events"
    
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pattern_id = Column(String(36), ForeignKey("blast_patterns.pattern_id"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Event identification
    blast_number = Column(String(50))
    blast_date = Column(DateTime, nullable=False)
    
    # Timing
    scheduled_time = Column(DateTime)
    actual_fire_time = Column(DateTime)
    all_clear_time = Column(DateTime)
    
    # Summary
    total_holes = Column(Integer)
    total_explosive_kg = Column(Float)
    total_volume_bcm = Column(Float)
    powder_factor_kg_bcm = Column(Float)
    
    # Initiation
    initiation_system = Column(String(50))  # nonel, electronic, detonating_cord
    total_delay_ms = Column(Integer)  # Total firing sequence duration
    
    # Weather conditions
    wind_speed_kmh = Column(Float)
    wind_direction = Column(String(10))
    temperature_c = Column(Float)
    humidity_percent = Column(Float)
    
    # Monitoring results
    max_ppv_mm_s = Column(Float)  # Peak particle velocity
    max_overpressure_db = Column(Float)  # Air overpressure
    monitoring_locations = Column(JSON)  # List of monitoring points with readings
    
    # Fragmentation assessment
    avg_fragment_size_cm = Column(Float)
    oversize_percent = Column(Float)  # Percent > target size
    fines_percent = Column(Float)  # Percent < minimum size
    fragmentation_rating = Column(String(20))  # good, acceptable, poor
    
    # Muckpile
    muckpile_height_m = Column(Float)
    throw_distance_m = Column(Float)
    
    # Issues
    misfires = Column(Integer, default=0)
    flyrock_incident = Column(Boolean, default=False)
    flyrock_details = Column(Text)
    
    # Responsible persons
    shotfirer_id = Column(String(36))
    shotfirer_name = Column(String(100))
    supervisor_id = Column(String(36))
    supervisor_name = Column(String(100))
    
    # Status
    status = Column(String(50), default="planned")  # planned, in_progress, completed, incident
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    pattern = relationship("BlastPattern", back_populates="blast_event")


class FragmentationModel(Base):
    """Fragmentation prediction model parameters."""
    __tablename__ = "fragmentation_models"
    
    model_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Model identification
    name = Column(String(100), nullable=False)
    rock_type = Column(String(100))
    description = Column(Text)
    
    # Kuz-Ram model parameters
    rock_factor_a = Column(Float, default=8)  # Rock factor A (4-16)
    uniformity_index_n = Column(Float, default=1.0)  # Uniformity index
    
    # Rock properties
    rock_density_kg_m3 = Column(Float, default=2700)
    ucs_mpa = Column(Float)  # Uniaxial compressive strength
    rqi = Column(Float)  # Rock Quality Index
    
    # Explosive properties
    relative_weight_strength = Column(Float, default=100)  # ANFO = 100
    
    # Calibration
    calibrated_from_blasts = Column(Integer, default=0)
    last_calibrated = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
