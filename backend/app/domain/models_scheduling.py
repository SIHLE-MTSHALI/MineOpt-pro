from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
from datetime import datetime

class ScheduleVersion(Base):
    __tablename__ = "schedule_versions"
    version_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False)
    status = Column(String, default="Draft") # Draft, Published, Archived
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="schedule_version")

class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"))
    
    # Relationships to Enterprise Domain Models
    resource_id = Column(String, ForeignKey("resources.resource_id")) 
    activity_id = Column(String, ForeignKey("activities.activity_id"))
    period_id = Column(String, ForeignKey("periods.period_id"))
    activity_area_id = Column(String, ForeignKey("activity_areas.area_id")) # The Block
    
    # Quantities
    planned_quantity = Column(Float)
    
    # Metadata
    status = Column(String, default="Scheduled") # Scheduled, InProgress, Complete
    
    schedule_version = relationship("ScheduleVersion", back_populates="tasks")
    # We can add back_populates in other models if needed, but for now simple FKs suffice
    # resource = relationship("Resource")
    # activity = relationship("Activity")
    # period = relationship("Period")
