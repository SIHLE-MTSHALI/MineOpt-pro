from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime

# 3.7 Material Types
class MaterialType(Base):
    __tablename__ = "material_types"
    material_type_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False)
    category = Column(String) # ROM, Waste, Reject, Product
    default_density = Column(Float)
    moisture_basis_for_quantity = Column(String, default="as-mined")
    reporting_group = Column(String) # Coal, Waste
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="material_types")

# 3.8 Quality Fields
class QualityField(Base):
    __tablename__ = "quality_fields"
    quality_field_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False) # CV_ARB
    description = Column(String)
    units = Column(String) # MJ/kg
    basis = Column(String) # ARB, ADB, DAF
    aggregation_rule = Column(String, default="WeightedAverage")
    missing_data_policy = Column(String, default="Error")
    default_value = Column(Float)
    constraint_direction_default = Column(String) # Max, Min, Target
    penalty_function_type = Column(String, default="Linear")
    penalty_parameters = Column(JSON) # {slope: 10}
    
    site = relationship("Site", back_populates="quality_fields")

# 3.4 Activities
class Activity(Base):
    __tablename__ = "activities"
    activity_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False) # Coal Mining, Waste Mining
    display_color = Column(String)
    moves_material = Column(Boolean, default=True)
    required_haulage = Column(Boolean, default=True)
    quantity_field_type = Column(String, default="Tonnes")
    default_number_of_slices = Column(Integer, default=1)
    max_resources = Column(Integer)
    is_selectable_in_ui = Column(Boolean, default=True)
    precedence_rules = Column(JSON) # List of predecessor activity_ids
    
    site = relationship("Site", back_populates="activities")

# 3.5 Activity Areas (Spatial)
class ActivityArea(Base):
    __tablename__ = "activity_areas"
    area_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False)
    activity_id = Column(String, ForeignKey("activities.activity_id"))
    geometry = Column(JSON) # {"position": [x,y,z], "size": [w,h,d]}
    slice_count = Column(Integer, default=1)
    slice_states = Column(JSON) # List of slice objects {index, status, quantity, quality_vector}
    priority = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    
    activity = relationship("Activity")

# 3.6 Resources
class Resource(Base):
    __tablename__ = "resources"
    resource_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False)
    resource_type = Column(String) # Excavator, TruckFleet
    capacity_type = Column(String, default="Throughput")
    base_rate = Column(Float)
    base_rate_units = Column(String) # t/h
    can_reduce_rate_for_blend = Column(Boolean, default=False)
    min_rate_factor = Column(Float, default=0.0)
    supported_activities = Column(JSON) # List of activity IDs
    
    site = relationship("Site", back_populates="resources")

class ResourcePeriodParameters(Base):
    __tablename__ = "resource_period_params"
    param_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(String, ForeignKey("resources.resource_id"))
    period_id = Column(String) # FK to periods
    availability_fraction = Column(Float, default=1.0)
    utilisation_fraction = Column(Float, default=1.0)
    efficiency_fraction = Column(Float, default=1.0)
    rate_factor = Column(Float, default=1.0)
