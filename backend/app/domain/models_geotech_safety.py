"""
Geotechnical, Environmental & Safety Domain Models

Models for slope monitoring, water management, air quality, rehabilitation, and safety.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.database import Base


# =============================================================================
# GEOTECHNICAL MODELS
# =============================================================================

class GeotechDomain(Base):
    """Geotechnical design domain."""
    __tablename__ = "geotech_domains"
    
    domain_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    rock_type = Column(String(100))
    
    # Boundary (GeoJSON)
    boundary_geojson = Column(JSON)
    
    # Design parameters
    inter_ramp_angle = Column(Float)  # Overall slope angle
    batter_angle = Column(Float)  # Face angle
    batter_height = Column(Float)  # Bench height
    berm_width = Column(Float)  # Catch berm width
    
    # Stability factors
    factor_of_safety = Column(Float)
    failure_mechanism = Column(String(50))  # planar, wedge, circular, toppling
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SlopeMonitoringPrism(Base):
    """Slope monitoring prism location."""
    __tablename__ = "slope_prisms"
    
    prism_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    domain_id = Column(String(36), ForeignKey("geotech_domains.domain_id"))
    
    # Identification
    prism_name = Column(String(50), nullable=False)
    location = Column(String(100))
    
    # Initial position
    initial_x = Column(Float, nullable=False)
    initial_y = Column(Float, nullable=False)
    initial_z = Column(Float, nullable=False)
    installed_at = Column(DateTime)
    
    # Current position
    current_x = Column(Float)
    current_y = Column(Float)
    current_z = Column(Float)
    
    # Cumulative displacement
    total_displacement_mm = Column(Float, default=0)
    displacement_rate_mm_day = Column(Float, default=0)
    
    # Alert thresholds
    warning_threshold_mm = Column(Float, default=50)
    critical_threshold_mm = Column(Float, default=100)
    alert_status = Column(String(20), default="normal")  # normal, warning, critical
    
    # Status
    is_active = Column(Boolean, default=True)
    last_reading_at = Column(DateTime)
    
    # Relationships
    readings = relationship("PrismReading", back_populates="prism", cascade="all, delete-orphan")


class PrismReading(Base):
    """Individual prism monitoring reading."""
    __tablename__ = "prism_readings"
    
    reading_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prism_id = Column(String(36), ForeignKey("slope_prisms.prism_id"), nullable=False)
    
    # Position
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    
    # Displacement from initial
    delta_x = Column(Float)
    delta_y = Column(Float)
    delta_z = Column(Float)
    total_displacement_mm = Column(Float)
    
    # Displacement rate
    displacement_rate_mm_day = Column(Float)
    
    # Quality
    accuracy_mm = Column(Float)
    
    # Timestamp
    measured_at = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    prism = relationship("SlopeMonitoringPrism", back_populates="readings")


class MonitoringBore(Base):
    """Groundwater monitoring bore."""
    __tablename__ = "monitoring_bores"
    
    bore_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    bore_name = Column(String(50), nullable=False)
    bore_type = Column(String(50))  # monitoring, dewatering, observation
    
    # Location
    easting = Column(Float, nullable=False)
    northing = Column(Float, nullable=False)
    collar_rl = Column(Float)
    
    # Construction
    drilled_date = Column(DateTime)
    total_depth_m = Column(Float)
    casing_diameter_mm = Column(Float)
    screen_from_m = Column(Float)
    screen_to_m = Column(Float)
    
    # Current status
    current_water_level_m = Column(Float)  # Depth below collar
    current_water_rl = Column(Float)  # Reduced level
    
    # Design water level
    target_water_level_m = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_reading_at = Column(DateTime)
    
    # Relationships
    readings = relationship("WaterLevelReading", back_populates="bore", cascade="all, delete-orphan")


class WaterLevelReading(Base):
    """Groundwater level reading."""
    __tablename__ = "water_level_readings"
    
    reading_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bore_id = Column(String(36), ForeignKey("monitoring_bores.bore_id"), nullable=False)
    
    # Measurement
    water_level_m = Column(Float, nullable=False)  # Depth below collar
    water_rl = Column(Float)  # Reduced level
    
    # Timestamp
    measured_at = Column(DateTime, nullable=False)
    measured_by = Column(String(100))
    
    # Relationship
    bore = relationship("MonitoringBore", back_populates="readings")


# =============================================================================
# ENVIRONMENTAL MODELS
# =============================================================================

class DustMonitor(Base):
    """Dust monitoring station."""
    __tablename__ = "dust_monitors"
    
    monitor_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    monitor_type = Column(String(50))  # continuous, hvas, deposited
    
    # Position
    easting = Column(Float)
    northing = Column(Float)
    
    # Thresholds
    pm10_threshold_ug_m3 = Column(Float, default=50)
    pm25_threshold_ug_m3 = Column(Float, default=25)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_reading_at = Column(DateTime)
    
    # Relationships
    readings = relationship("DustReading", back_populates="monitor", cascade="all, delete-orphan")


class DustReading(Base):
    """Dust concentration reading."""
    __tablename__ = "dust_readings"
    
    reading_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    monitor_id = Column(String(36), ForeignKey("dust_monitors.monitor_id"), nullable=False)
    
    # Measurements
    pm10_ug_m3 = Column(Float)
    pm25_ug_m3 = Column(Float)
    tsp_ug_m3 = Column(Float)  # Total suspended particulates
    
    # Exceedance flags
    pm10_exceeded = Column(Boolean, default=False)
    pm25_exceeded = Column(Boolean, default=False)
    
    # Weather at time of reading
    wind_speed_kmh = Column(Float)
    wind_direction = Column(String(10))
    temperature_c = Column(Float)
    humidity_percent = Column(Float)
    
    # Timestamp
    measured_at = Column(DateTime, nullable=False, index=True)
    
    # Relationship
    monitor = relationship("DustMonitor", back_populates="readings")


class RehabilitationArea(Base):
    """Rehabilitation area tracking."""
    __tablename__ = "rehabilitation_areas"
    
    area_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String(100), nullable=False)
    area_type = Column(String(50))  # dump, void, infrastructure
    
    # Geometry
    boundary_geojson = Column(JSON)
    area_hectares = Column(Float)
    
    # Status
    status = Column(String(50))  # active, shaping, topsoil, seeded, established
    
    # Key dates
    mining_completed_at = Column(DateTime)
    shaping_completed_at = Column(DateTime)
    topsoil_placed_at = Column(DateTime)
    seeded_at = Column(DateTime)
    
    # Vegetation
    seed_mix = Column(String(200))
    target_species = Column(JSON)
    
    # Current condition
    vegetation_coverage_percent = Column(Float)
    health_score = Column(Float)  # 0-100
    last_inspection_at = Column(DateTime)
    
    # Closure liability
    estimated_closure_cost = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# SAFETY MODELS
# =============================================================================

class HazardZone(Base):
    """Hazard or exclusion zone."""
    __tablename__ = "hazard_zones"
    
    zone_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String(100), nullable=False)
    hazard_type = Column(String(50))  # blast, unstable, highwall, electrical, water
    severity = Column(String(20))  # low, medium, high, critical
    
    # Geometry
    boundary_geojson = Column(JSON, nullable=False)
    buffer_m = Column(Float, default=0)
    
    # Rules
    is_exclusion = Column(Boolean, default=True)
    requires_authorization = Column(Boolean, default=False)
    authorized_roles = Column(JSON)  # List of roles that can enter
    
    # Schedule
    active_from = Column(DateTime)
    active_to = Column(DateTime)
    active_schedule = Column(JSON)  # Recurring schedule
    
    # Current status
    is_active = Column(Boolean, default=True)
    
    # Notifications
    notify_on_entry = Column(Boolean, default=True)
    notification_message = Column(Text)
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class HazardZoneEntry(Base):
    """Record of entry into hazard zone."""
    __tablename__ = "hazard_zone_entries"
    
    entry_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String(36), ForeignKey("hazard_zones.zone_id"), nullable=False)
    
    # Who/what entered
    equipment_id = Column(String(36))
    equipment_fleet_number = Column(String(50))
    person_id = Column(String(36))
    person_name = Column(String(100))
    
    # Entry details
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    
    # Authorization
    was_authorized = Column(Boolean)
    authorization_id = Column(String(36))
    
    # Location
    entry_latitude = Column(Float)
    entry_longitude = Column(Float)
    
    # Acknowledgment
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    
    # Notes
    notes = Column(Text)


class FatigueEvent(Base):
    """Fatigue detection event."""
    __tablename__ = "fatigue_events"
    
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Operator
    operator_id = Column(String(36), ForeignKey("users.user_id"))
    operator_name = Column(String(100))
    
    # Equipment
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"))
    equipment_fleet_number = Column(String(50))
    
    # Event details
    event_type = Column(String(50))  # microsleep, distraction, yawn, head_drop
    severity = Column(String(20))  # low, medium, high, critical
    confidence_percent = Column(Float)
    
    # Source
    detection_system = Column(String(100))  # DSS, Seeing Machines, SmartCap
    
    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Timing
    occurred_at = Column(DateTime, nullable=False)
    shift_hours_at_event = Column(Float)
    
    # Response
    response_action = Column(String(100))
    responded_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class OperatorFatigueScore(Base):
    """Aggregated operator fatigue risk score."""
    __tablename__ = "operator_fatigue_scores"
    
    score_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operator_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Calculated score
    fatigue_risk_score = Column(Float)  # 0-100
    alertness_level = Column(String(20))  # alert, moderate, fatigued, critical
    
    # Factors
    hours_worked_24h = Column(Float)
    hours_worked_7d = Column(Float)
    events_24h = Column(Integer)
    events_7d = Column(Integer)
    
    # Recommendation
    recommended_action = Column(String(200))
    mandatory_rest = Column(Boolean, default=False)
    
    # Period
    calculated_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
