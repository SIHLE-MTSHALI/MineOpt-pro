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
    """
    A spatial work package (polygon/solid) representing an area to be mined.
    Contains slices for staged extraction.
    """
    __tablename__ = "activity_areas"
    
    area_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    name = Column(String, nullable=False)
    activity_id = Column(String, ForeignKey("activities.activity_id"), nullable=True)
    
    # Geometry definition
    # Example: {"position": [x, y, z], "size": [w, h, d], "vertices": [...]}
    geometry = Column(JSON, nullable=True)
    
    # Bench/elevation metadata
    bench_level = Column(String, nullable=True)
    elevation_rl = Column(Float, nullable=True)  # Reduced Level
    
    # Mining direction (optional vector for sequencing)
    mining_direction_vector = Column(JSON, nullable=True)  # [dx, dy, dz]
    
    # Slice management
    slice_count = Column(Integer, default=1)
    # List of slice objects: [{index, status, quantity, quality_vector, material_type_id}]
    slice_states = Column(JSON, default=list)
    
    # Scheduling priority (higher = mined earlier)
    priority = Column(Integer, default=0)
    
    # Lock status (locked areas cannot be scheduled)
    is_locked = Column(Boolean, default=False)
    lock_reason = Column(String, nullable=True)
    
    # Destination preferences (optional routing hints)
    preferred_destination_node_id = Column(String, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    # Relationships
    activity = relationship("Activity")
    
    def __repr__(self):
        return f"<ActivityArea {self.name}>"

# 3.6 Resources
class Resource(Base):
    """
    Equipment, crews, or processors that perform work.
    """
    __tablename__ = "resources"
    
    resource_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    name = Column(String, nullable=False)
    
    # Resource classification
    # Excavator, TruckFleet, Dozer, Drill, Crusher, WashPlant, Conveyor, Loader
    resource_type = Column(String, nullable=False)
    
    # Capacity type determines how output is measured
    # Throughput: tonnes/hour
    # Volume: BCM/hour
    # TimeBased: hours available
    capacity_type = Column(String, default="Throughput")
    
    # Production rates
    base_rate = Column(Float, nullable=True)
    base_rate_units = Column(String, nullable=True)  # t/h, BCM/h, m/h
    
    # Rate reduction for blending control
    can_reduce_rate_for_blend = Column(Boolean, default=False)
    min_rate_factor = Column(Float, default=0.0)  # Minimum allowed rate as fraction
    max_rate_factor = Column(Float, default=1.0)  # Maximum rate factor (overclock)
    
    # Economic factors
    cost_per_hour = Column(Float, nullable=True)  # Operating cost $/hr
    cost_per_tonne = Column(Float, nullable=True)  # Variable cost $/t
    
    # Environmental factors
    emissions_factor = Column(Float, nullable=True)  # kg CO2/tonne or similar
    
    # Activity eligibility
    supported_activities = Column(JSON, nullable=True)  # List of activity IDs
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    site = relationship("Site", back_populates="resources")
    period_parameters = relationship("ResourcePeriodParameters", back_populates="resource")

    def __repr__(self):
        return f"<Resource {self.name} ({self.resource_type})>"

class ResourcePeriodParameters(Base):
    """
    Period-specific parameters for a resource.
    Allows modeling of varying availability, efficiency, and utilization.
    """
    __tablename__ = "resource_period_params"
    
    param_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(String, ForeignKey("resources.resource_id"), nullable=False)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=False)
    
    # Availability: fraction of period not down (maintenance, breakdown)
    availability_fraction = Column(Float, default=1.0)
    
    # Utilisation: fraction of available time actually used
    utilisation_fraction = Column(Float, default=1.0)
    
    # Efficiency: productivity multiplier (operator skill, conditions)
    efficiency_fraction = Column(Float, default=1.0)
    
    # Rate factor: planner override scaling output
    rate_factor = Column(Float, default=1.0)
    
    # Notes explaining parameter values
    notes = Column(String, nullable=True)
    
    # Relationships
    resource = relationship("Resource", back_populates="period_parameters")

    def __repr__(self):
        return f"<ResourcePeriodParams {self.resource_id[:8]}... avail={self.availability_fraction}>"
