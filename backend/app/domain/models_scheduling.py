"""
Scheduling Entities - Section 3.15 of Enterprise Specification

ScheduleVersion: A frozen instance of a mining plan with full metadata.
Task: Individual work assignments linking resources, activities, and locations.

Enhanced with:
- Schedule horizon and versioning support
- Flow routing fields (from_node, to_node)
- Fine-grained datetime resolution
- Task type classification
- KPI tagging for reporting
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
from datetime import datetime


class ScheduleVersion(Base):
    """
    A frozen instance of a mining schedule.
    Once published, schedule versions are immutable.
    """
    __tablename__ = "schedule_versions"
    
    version_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Status lifecycle: Draft -> Published -> Archived
    status = Column(String, default="Draft")
    
    # Schedule type
    schedule_type = Column(String, default="Authoritative")  # Authoritative, Preview, WhatIf
    
    # Horizon definition
    horizon_start_period_id = Column(String, ForeignKey("periods.period_id"), nullable=True)
    horizon_end_period_id = Column(String, ForeignKey("periods.period_id"), nullable=True)
    
    # Version lineage (for forking and iteration)
    parent_schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=True)
    
    # Change tracking
    change_reason = Column(Text, nullable=True)  # Why this version was created
    
    # Run information
    run_request_id = Column(String, nullable=True)  # ScheduleRunRequest that created this
    run_diagnostics_summary = Column(JSON, nullable=True)
    # Example: {"infeasibilities": 0, "warnings": 3, "binding_constraints": ["Plant capacity"]}
    
    # Model references for reproducibility
    site_model_version_reference = Column(String, nullable=True)
    state_snapshot_reference = Column(String, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    published_by = Column(String, nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="schedule_version")
    site = relationship("Site")
    parent_version = relationship("ScheduleVersion", remote_side=[version_id])

    def __repr__(self):
        return f"<ScheduleVersion {self.name} ({self.status})>"


class Task(Base):
    """
    A single work assignment in the schedule.
    Represents an activity performed by a resource at a location during a period.
    """
    __tablename__ = "tasks"
    
    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=False)
    
    # Core relationships
    resource_id = Column(String, ForeignKey("resources.resource_id"), nullable=True)
    activity_id = Column(String, ForeignKey("activities.activity_id"), nullable=True)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=True)
    activity_area_id = Column(String, ForeignKey("activity_areas.area_id"), nullable=True)
    
    # Material flow routing (where material goes from/to)
    from_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=True)
    to_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=True)
    
    # Fine-grained timing (within a period)
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)
    
    # Quantities
    planned_quantity = Column(Float, default=0.0)
    actual_quantity = Column(Float, nullable=True)  # For reconciliation
    
    # Material type for this task
    material_type_id = Column(String, ForeignKey("material_types.material_type_id"), nullable=True)
    
    # Task classification
    # Mining: Extracting material from ground
    # Haulage: Transporting material (implicit in routing)
    # Processing: Plant operations
    # Rehandle: Moving material between stockpiles
    # Delay: Planned or unplanned downtime
    # OptimiserDelay: Rate reduction inserted by optimizer
    # Maintenance: Scheduled maintenance
    task_type = Column(String, default="Mining")
    
    # Delay information (if task_type is Delay/OptimiserDelay)
    delay_reason_code = Column(String, nullable=True)
    delay_reason_description = Column(String, nullable=True)
    
    # Status tracking
    status = Column(String, default="Scheduled")  # Scheduled, InProgress, Complete, Cancelled
    
    # Rate factor applied (if production was reduced)
    rate_factor_applied = Column(Float, default=1.0)
    
    # KPI tags for reporting grouping
    # Example: {"product": "Prime", "shift_type": "Day", "priority": "high"}
    kpi_tags = Column(JSON, nullable=True)
    
    # Quality information (expected or actual)
    expected_quality_vector = Column(JSON, nullable=True)
    actual_quality_vector = Column(JSON, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    schedule_version = relationship("ScheduleVersion", back_populates="tasks")
    resource = relationship("Resource")
    activity = relationship("Activity")
    from_node = relationship("FlowNode", foreign_keys=[from_node_id])
    to_node = relationship("FlowNode", foreign_keys=[to_node_id])
    material_type = relationship("MaterialType")

    def __repr__(self):
        return f"<Task {self.task_type} {self.planned_quantity}t>"

    @property
    def is_delay(self) -> bool:
        """Check if this is a delay task."""
        return self.task_type in ["Delay", "OptimiserDelay", "Maintenance"]
    
    @property
    def duration_hours(self) -> float:
        """Calculate task duration in hours if datetime set."""
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return delta.total_seconds() / 3600
        return 0.0
