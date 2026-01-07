"""
Fleet Management Domain Models

Models for equipment tracking, GPS, and geofencing.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.database import Base


class EquipmentType(str, enum.Enum):
    """Types of mining equipment."""
    HAUL_TRUCK = "haul_truck"
    EXCAVATOR = "excavator"
    FRONT_END_LOADER = "front_end_loader"
    DOZER = "dozer"
    GRADER = "grader"
    DRILL_RIG = "drill_rig"
    WATER_CART = "water_cart"
    FUEL_TRUCK = "fuel_truck"
    LIGHT_VEHICLE = "light_vehicle"
    OTHER = "other"


class EquipmentStatus(str, enum.Enum):
    """Operating status of equipment."""
    OPERATING = "operating"
    STANDBY = "standby"
    MAINTENANCE = "maintenance"
    BREAKDOWN = "breakdown"
    REFUELING = "refueling"
    SHIFT_CHANGE = "shift_change"
    OFF_SITE = "off_site"


class Equipment(Base):
    """Mining equipment entity."""
    __tablename__ = "equipment"
    
    equipment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    fleet_number = Column(String(50), nullable=False)
    name = Column(String(100))
    equipment_type = Column(Enum(EquipmentType), nullable=False)
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    year = Column(Integer)
    
    # Capacity
    payload_tonnes = Column(Float)  # For haul trucks
    bucket_capacity_bcm = Column(Float)  # For excavators/loaders
    
    # Status
    status = Column(Enum(EquipmentStatus), default=EquipmentStatus.STANDBY)
    current_operator_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    
    # Engine hours / odometer
    engine_hours = Column(Float, default=0)
    odometer_km = Column(Float, default=0)
    
    # Last known position
    last_latitude = Column(Float)
    last_longitude = Column(Float)
    last_heading = Column(Float)
    last_speed_kmh = Column(Float)
    last_position_time = Column(DateTime)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    gps_readings = relationship("GPSReading", back_populates="equipment", cascade="all, delete-orphan")
    haul_cycles = relationship("HaulCycle", back_populates="equipment", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="equipment", cascade="all, delete-orphan")


class GPSReading(Base):
    """GPS position reading for equipment tracking."""
    __tablename__ = "gps_readings"
    
    reading_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)
    
    # Position
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)
    
    # Motion
    heading = Column(Float)  # Degrees from north
    speed_kmh = Column(Float)
    
    # Quality
    hdop = Column(Float)  # Horizontal dilution of precision
    num_satellites = Column(Integer)
    fix_quality = Column(String(20))  # GPS, DGPS, RTK, etc.
    
    # Status at time of reading
    engine_on = Column(Boolean)
    status = Column(Enum(EquipmentStatus))
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    equipment = relationship("Equipment", back_populates="gps_readings")


class Geofence(Base):
    """Geofenced area for equipment tracking and restrictions."""
    __tablename__ = "geofences"
    
    geofence_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String(100), nullable=False)
    description = Column(Text)
    zone_type = Column(String(50))  # loading, dumping, haul_road, restricted, speed_limit
    
    # Geometry (stored as GeoJSON polygon)
    boundary_geojson = Column(JSON, nullable=False)
    
    # Rules
    speed_limit_kmh = Column(Float)  # If speed limit zone
    is_restricted = Column(Boolean, default=False)  # Entry prohibited without authorization
    alert_on_entry = Column(Boolean, default=False)
    alert_on_exit = Column(Boolean, default=False)
    
    # Schedule - when the geofence is active
    active_start_time = Column(String(10))  # "HH:MM" format
    active_end_time = Column(String(10))
    active_days = Column(JSON)  # ["Mon", "Tue", ...]
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    violations = relationship("GeofenceViolation", back_populates="geofence", cascade="all, delete-orphan")


class GeofenceViolation(Base):
    """Record of geofence rule violations."""
    __tablename__ = "geofence_violations"
    
    violation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    geofence_id = Column(String(36), ForeignKey("geofences.geofence_id"), nullable=False)
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)
    
    # Violation details
    violation_type = Column(String(50))  # unauthorized_entry, speeding, unauthorized_exit
    latitude = Column(Float)
    longitude = Column(Float)
    speed_kmh = Column(Float)  # For speeding violations
    speed_limit_kmh = Column(Float)
    
    # Timestamps
    violation_time = Column(DateTime, nullable=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(36), ForeignKey("users.user_id"))
    
    # Relationship
    geofence = relationship("Geofence", back_populates="violations")


class HaulCycle(Base):
    """Detected haul cycle from GPS data."""
    __tablename__ = "haul_cycles"
    
    cycle_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Source and destination
    source_location_id = Column(String(36))  # Loading location (dig block, stockpile)
    source_name = Column(String(100))
    destination_location_id = Column(String(36))  # Dump location
    destination_name = Column(String(100))
    
    # Cycle phases (all times in seconds)
    queue_at_loader_sec = Column(Float, default=0)
    loading_sec = Column(Float, default=0)
    travel_loaded_sec = Column(Float, default=0)
    queue_at_dump_sec = Column(Float, default=0)
    dumping_sec = Column(Float, default=0)
    travel_empty_sec = Column(Float, default=0)
    total_cycle_sec = Column(Float, default=0)
    
    # Distances
    travel_loaded_km = Column(Float)
    travel_empty_km = Column(Float)
    total_distance_km = Column(Float)
    
    # Load info
    payload_tonnes = Column(Float)
    material_type = Column(String(50))  # ore, waste, topsoil
    
    # Timestamps
    cycle_start = Column(DateTime, nullable=False, index=True)
    cycle_end = Column(DateTime, nullable=False)
    
    # Status
    is_complete = Column(Boolean, default=True)
    is_valid = Column(Boolean, default=True)  # False if cycle seems anomalous
    
    # Relationship
    equipment = relationship("Equipment", back_populates="haul_cycles")


class MaintenanceRecord(Base):
    """Equipment maintenance and work order records."""
    __tablename__ = "maintenance_records"
    
    record_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)
    
    # Work order info
    work_order_number = Column(String(50))
    maintenance_type = Column(String(50))  # preventive, corrective, inspection
    priority = Column(String(20))  # low, medium, high, critical
    
    # Description
    title = Column(String(200), nullable=False)
    description = Column(Text)
    failure_code = Column(String(50))
    
    # Scheduling
    scheduled_date = Column(DateTime)
    due_engine_hours = Column(Float)  # Due at this engine hour reading
    
    # Execution
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    performed_by = Column(String(100))  # Technician name/ID
    
    # Engine hours at time of maintenance
    engine_hours_at_service = Column(Float)
    
    # Parts and costs
    parts_used = Column(JSON)  # List of {part_number, description, quantity, cost}
    labor_hours = Column(Float)
    total_cost = Column(Float)
    
    # Status
    status = Column(String(20), default="scheduled")  # scheduled, in_progress, completed, cancelled
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    equipment = relationship("Equipment", back_populates="maintenance_records")


class ComponentLife(Base):
    """Track component lifecycle for equipment."""
    __tablename__ = "component_life"
    
    component_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)
    
    # Component identification
    component_type = Column(String(50), nullable=False)  # engine, transmission, tires, undercarriage
    component_name = Column(String(100))
    serial_number = Column(String(100))
    
    # Installation
    installed_at = Column(DateTime)
    installed_engine_hours = Column(Float)
    
    # Expected life
    expected_life_hours = Column(Float)
    expected_life_km = Column(Float)
    
    # Current status
    current_hours = Column(Float, default=0)
    current_km = Column(Float, default=0)
    remaining_life_percent = Column(Float, default=100)
    
    # Replacement
    replaced_at = Column(DateTime)
    replacement_reason = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
