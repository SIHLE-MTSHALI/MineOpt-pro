from sqlalchemy import Column, String, Float, ForeignKey, Boolean, JSON, Integer
from sqlalchemy.orm import relationship
import uuid
from ..database import Base

class Resource(Base):
    __tablename__ = "resources"

    resource_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String)
    resource_type = Column(String) # Excavator, Truck, Drill
    
    capacity_type = Column(String) # Throughput, Volume
    base_rate = Column(Float)
    base_rate_units = Column(String) # t/h
    
    can_reduce_rate_for_blend = Column(Boolean, default=False)
    minimum_rate_factor = Column(Float, default=0.0)
    
    site = relationship("Site", back_populates="resources")


class Activity(Base):
    __tablename__ = "activities"
    
    activity_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String)
    display_color = Column(String)
    
    moves_material = Column(Boolean, default=True)
    requires_haulage = Column(Boolean, default=True)
    precedence_rules = Column(JSON, default=[])

    site = relationship("Site", back_populates="activities")
    activity_areas = relationship("ActivityArea", back_populates="activity")


class ActivityArea(Base):
    __tablename__ = "activity_areas"

    area_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    activity_id = Column(String, ForeignKey("activities.activity_id"))
    name = Column(String)
    
    geometry = Column(JSON) # GeoJSON or custom vertex list
    priority = Column(Integer, default=50)
    is_locked = Column(Boolean, default=False)
    
    # Slices are complex, for v1 store as JSON list of objects
    # Or separate table if querying slices heavily. Spec says "slice_states (array of slice objects)"
    slice_states = Column(JSON, default=[]) 

    activity = relationship("Activity", back_populates="activity_areas")
