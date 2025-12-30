from sqlalchemy import Column, String, Float, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..database import Base

class ScheduleVersion(Base):
    __tablename__ = "schedule_versions"

    version_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String)
    status = Column(String, default="Draft") # Draft, Published, Archived
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="schedule_version")


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"))
    
    # Assignments
    resource_id = Column(String, ForeignKey("resources.resource_id"))
    activity_id = Column(String, ForeignKey("activities.activity_id"))
    
    # Time (Simplified for v1: Period based)
    period_id = Column(String) # For now just string ID, later FK to periods table
    
    # Work
    activity_area_id = Column(String, ForeignKey("activity_areas.area_id"), nullable=True)
    planned_quantity = Column(Float, default=0.0)
    
    # Metadata
    color_override = Column(String, nullable=True)

    schedule_version = relationship("ScheduleVersion", back_populates="tasks")
    resource = relationship("Resource")
    activity = relationship("Activity")
    activity_area = relationship("ActivityArea")
