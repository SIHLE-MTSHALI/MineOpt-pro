"""
Material Tracking and Shift Operations Domain Models

Models for load tickets, material movements, shifts, and handovers.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.database import Base


class MaterialType(str, enum.Enum):
    """Types of material."""
    ORE_HIGH_GRADE = "ore_high_grade"
    ORE_LOW_GRADE = "ore_low_grade"
    MARGINAL = "marginal"
    WASTE = "waste"
    TOPSOIL = "topsoil"
    OVERBURDEN = "overburden"
    REHANDLE = "rehandle"


class LoadTicket(Base):
    """Record of a single haul truck load."""
    __tablename__ = "load_tickets"
    
    ticket_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    shift_id = Column(String(36), ForeignKey("shifts.shift_id"))
    
    # Equipment
    truck_id = Column(String(36), ForeignKey("equipment.equipment_id"))
    truck_fleet_number = Column(String(50))
    loader_id = Column(String(36), ForeignKey("equipment.equipment_id"))
    loader_fleet_number = Column(String(50))
    
    # Origin
    origin_type = Column(String(50))  # dig_block, stockpile, rehandle
    origin_id = Column(String(36))
    origin_name = Column(String(100))
    origin_bench = Column(String(50))
    
    # Destination
    destination_type = Column(String(50))  # dump, stockpile, crusher, plant
    destination_id = Column(String(36))
    destination_name = Column(String(100))
    
    # Material
    material_type = Column(Enum(MaterialType), nullable=False)
    tonnes = Column(Float)  # Estimated or weighed
    bcm = Column(Float)
    
    # Grade (if ore)
    grade_percent = Column(Float)
    grade_ppm = Column(Float)
    grade_source = Column(String(50))  # estimated, assay, grade_control
    
    # Weighbridge
    tare_weight_kg = Column(Float)
    gross_weight_kg = Column(Float)
    net_weight_kg = Column(Float)
    weighed = Column(Boolean, default=False)
    
    # Timing
    loaded_at = Column(DateTime, nullable=False)
    dumped_at = Column(DateTime)
    
    # Operator
    operator_id = Column(String(36))
    operator_name = Column(String(100))
    
    # Status
    is_valid = Column(Boolean, default=True)
    void_reason = Column(String(200))
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class MaterialMovementSummary(Base):
    """Aggregated material movement for reconciliation."""
    __tablename__ = "material_movement_summaries"
    
    summary_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Period
    period_type = Column(String(20))  # shift, day, week, month
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Source
    source_type = Column(String(50))
    source_id = Column(String(36))
    source_name = Column(String(100))
    
    # Destination
    destination_type = Column(String(50))
    destination_id = Column(String(36))
    destination_name = Column(String(100))
    
    # Material
    material_type = Column(Enum(MaterialType))
    
    # Quantities
    load_count = Column(Integer, default=0)
    total_tonnes = Column(Float, default=0)
    total_bcm = Column(Float, default=0)
    avg_grade = Column(Float)
    contained_metal = Column(Float)
    
    # Plan vs actual
    planned_tonnes = Column(Float)
    variance_tonnes = Column(Float)
    variance_percent = Column(Float)
    
    # Calculated
    created_at = Column(DateTime, default=datetime.utcnow)


class Shift(Base):
    """Work shift definition."""
    __tablename__ = "shifts"
    
    shift_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Shift identification
    shift_name = Column(String(50))  # Day, Night, A, B, C
    shift_date = Column(DateTime, nullable=False)
    shift_number = Column(Integer)  # 1, 2, 3 for the day
    
    # Timing
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Personnel
    supervisor_id = Column(String(36), ForeignKey("users.user_id"))
    supervisor_name = Column(String(100))
    crew_count = Column(Integer)
    
    # Status
    status = Column(String(20), default="scheduled")  # scheduled, active, completed
    
    # Relationships
    handovers = relationship("ShiftHandover", back_populates="shift", cascade="all, delete-orphan")
    incidents = relationship("ShiftIncident", back_populates="shift", cascade="all, delete-orphan")


class ShiftHandover(Base):
    """Shift handover notes."""
    __tablename__ = "shift_handovers"
    
    handover_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shift_id = Column(String(36), ForeignKey("shifts.shift_id"), nullable=False)
    
    # Handover type
    handover_type = Column(String(20))  # outgoing, incoming
    
    # Personnel
    outgoing_supervisor_id = Column(String(36))
    outgoing_supervisor_name = Column(String(100))
    incoming_supervisor_id = Column(String(36))
    incoming_supervisor_name = Column(String(100))
    
    # Production summary
    ore_tonnes = Column(Float, default=0)
    waste_tonnes = Column(Float, default=0)
    total_loads = Column(Integer, default=0)
    
    # Equipment status
    equipment_status = Column(JSON)  # List of equipment with status
    equipment_down = Column(Integer, default=0)
    
    # Key issues
    safety_notes = Column(Text)
    production_notes = Column(Text)
    equipment_notes = Column(Text)
    general_notes = Column(Text)
    
    # Outstanding tasks
    tasks_incomplete = Column(JSON)  # List of tasks for next shift
    tasks_priority = Column(JSON)  # Priority items
    
    # Acknowledgment
    handover_time = Column(DateTime)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))
    
    # Relationship
    shift = relationship("Shift", back_populates="handovers")


class ShiftIncident(Base):
    """Safety or operational incident during shift."""
    __tablename__ = "shift_incidents"
    
    incident_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shift_id = Column(String(36), ForeignKey("shifts.shift_id"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Classification
    incident_type = Column(String(50))  # safety, environmental, equipment, operational
    severity = Column(String(20))  # near_miss, minor, moderate, serious, critical
    category = Column(String(100))  # slip_trip_fall, collision, spill, etc.
    
    # Details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    location = Column(String(200))
    location_x = Column(Float)
    location_y = Column(Float)
    
    # Time
    occurred_at = Column(DateTime, nullable=False)
    reported_at = Column(DateTime, default=datetime.utcnow)
    
    # Personnel involved
    reported_by_id = Column(String(36))
    reported_by_name = Column(String(100))
    persons_involved = Column(JSON)  # List of {name, role, injury}
    
    # Equipment
    equipment_id = Column(String(36))
    equipment_fleet_number = Column(String(50))
    equipment_damage = Column(Text)
    
    # Response
    immediate_actions = Column(Text)
    root_cause = Column(Text)
    corrective_actions = Column(JSON)  # List of actions with status
    
    # Investigation
    investigation_required = Column(Boolean, default=False)
    investigation_status = Column(String(50))
    investigation_notes = Column(Text)
    
    # Closure
    status = Column(String(20), default="open")  # open, investigating, closed
    closed_at = Column(DateTime)
    closed_by = Column(String(100))
    
    # Relationship
    shift = relationship("Shift", back_populates="incidents")


class ReconciliationPeriod(Base):
    """Material reconciliation for a period."""
    __tablename__ = "reconciliation_periods"
    
    reconciliation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String(36), ForeignKey("sites.site_id"), nullable=False)
    
    # Period
    period_type = Column(String(20))  # month, quarter, year
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_name = Column(String(50))  # e.g., "January 2024"
    
    # Planned (from mine plan)
    planned_ore_tonnes = Column(Float)
    planned_ore_grade = Column(Float)
    planned_waste_tonnes = Column(Float)
    planned_strip_ratio = Column(Float)
    
    # Delivered (from load tickets)
    delivered_ore_tonnes = Column(Float)
    delivered_ore_grade = Column(Float)
    delivered_waste_tonnes = Column(Float)
    delivered_strip_ratio = Column(Float)
    
    # Processed (from plant)
    processed_tonnes = Column(Float)
    processed_grade = Column(Float)
    recovered_metal = Column(Float)
    recovery_percent = Column(Float)
    
    # Variances
    ore_variance_tonnes = Column(Float)
    ore_variance_percent = Column(Float)
    grade_variance = Column(Float)
    grade_variance_percent = Column(Float)
    
    # Dilution and ore loss
    dilution_percent = Column(Float)
    ore_loss_percent = Column(Float)
    
    # Status
    status = Column(String(20), default="draft")  # draft, reviewed, approved
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
