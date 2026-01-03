"""
Flow Network Entities - Section 3.10-3.14 of Enterprise Specification

Defines the material flow network structure:
- FlowNetwork: Container for nodes and arcs
- FlowNode: Locations where material can exist or be processed
- FlowArc: Connections between nodes with constraints
- ArcQualityObjective: Quality targets/limits per arc
- TransportTimeModel: Haulage time modeling

Also includes configuration entities for stockpiles and wash plants.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Float, JSON, Text
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime


# =============================================================================
# 3.10 Flow Network
# =============================================================================

class FlowNetwork(Base):
    """
    Container for a material flow network.
    A site may have multiple networks (e.g., main pit, secondary pit).
    """
    __tablename__ = "flow_networks"
    
    network_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Network status
    is_active = Column(Boolean, default=True)
    
    # Validation status
    is_validated = Column(Boolean, default=False)
    validation_errors = Column(JSON, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("Site")
    nodes = relationship("FlowNode", back_populates="network", cascade="all, delete-orphan")
    arcs = relationship("FlowArc", back_populates="network", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FlowNetwork {self.name}>"


class FlowNode(Base):
    """
    A node in the material flow network.
    Represents a location where material can exist, be stored, or be processed.
    """
    __tablename__ = "flow_nodes"
    
    node_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network_id = Column(String, ForeignKey("flow_networks.network_id"), nullable=False)
    
    # Node classification
    # Source: Mining faces, external inputs
    # Stockpile: Standard inventory stockpile
    # StagedStockpile: Multi-pile managed stockpile
    # Crusher: Primary crusher
    # WashPlant: Coal handling and preparation plant
    # Dump: Waste dump, rejects dump
    # ProductSink: Product stockpile or loadout
    # Loadout: Train loadout, truck dispatch point
    # Conveyor: Conveyor transfer point
    node_type = Column(String, nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Spatial location (for 3D rendering)
    # Example: {"position": [x, y, z], "dimensions": [w, h, d]}
    location_geometry = Column(JSON, nullable=True)
    
    # Capacity limit (tonnes)
    capacity_tonnes = Column(Float, nullable=True)
    
    # Link to operating resource (e.g., excavator for source, plant for processing)
    operating_resource_id = Column(String, ForeignKey("resources.resource_id"), nullable=True)
    
    # Enable detailed inventory tracking
    inventory_tracking_enabled = Column(Boolean, default=False)
    
    # Display properties
    display_color = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    network = relationship("FlowNetwork", back_populates="nodes")
    stockpile_config = relationship("StockpileConfig", uselist=False, back_populates="node", cascade="all, delete-orphan")
    wash_plant_config = relationship("WashPlantConfig", uselist=False, back_populates="node", cascade="all, delete-orphan")
    # Note: staged_stockpile_config relationship is defined in models_staged_stockpile.py
    # Access via StagedStockpileConfig.query.filter_by(node_id=...) if needed
    operating_resource = relationship("Resource")

    def __repr__(self):
        return f"<FlowNode {self.node_type}: {self.name}>"


class FlowArc(Base):
    """
    A directed connection between two nodes in the flow network.
    Defines allowed materials, capacity, costs, and quality objectives.
    """
    __tablename__ = "flow_arcs"
    
    arc_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network_id = Column(String, ForeignKey("flow_networks.network_id"), nullable=False)
    
    # Connection
    from_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False)
    to_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False)
    
    # Material eligibility
    # List of material_type_ids allowed on this arc, or null for all
    allowed_material_types = Column(JSON, nullable=True)
    
    # Capacity constraint (tonnes per period)
    capacity_tonnes_per_period = Column(Float, nullable=True)
    
    # Economic factors
    cost_per_tonne = Column(Float, default=0.0)  # Haulage cost, processing cost
    benefit_per_tonne = Column(Float, default=0.0)  # Revenue, value added
    
    # Transport modeling
    transport_time_model_id = Column(String, ForeignKey("transport_time_models.model_id"), nullable=True)
    
    # Arc status
    is_enabled = Column(Boolean, default=True)
    
    # Priority for routing decisions (higher = preferred)
    priority = Column(Integer, default=0)
    
    # Notes
    notes = Column(String, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    network = relationship("FlowNetwork", back_populates="arcs")
    from_node = relationship("FlowNode", foreign_keys=[from_node_id])
    to_node = relationship("FlowNode", foreign_keys=[to_node_id])
    quality_objectives = relationship("ArcQualityObjective", back_populates="arc", cascade="all, delete-orphan")
    transport_time_model = relationship("TransportTimeModel")

    def __repr__(self):
        return f"<FlowArc {self.from_node_id[:8]}... -> {self.to_node_id[:8]}...>"


class ArcQualityObjective(Base):
    """
    Quality target or constraint for material flowing through an arc.
    Enables product spec enforcement at routing decision points.
    """
    __tablename__ = "arc_quality_objectives"
    
    objective_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    arc_id = Column(String, ForeignKey("flow_arcs.arc_id"), nullable=False)
    quality_field_id = Column(String, ForeignKey("quality_fields.quality_field_id"), nullable=False)
    
    # Objective type
    # Target: Aim for this value (penalize deviation)
    # Min: Must be >= this value
    # Max: Must be <= this value
    # Range: Must be between min and max
    objective_type = Column(String, nullable=False)
    
    # Values (used based on objective_type)
    target_value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Penalty configuration
    penalty_weight = Column(Float, default=1.0)  # Multiplier for penalty
    
    # Override penalty function (if different from field default)
    # Example: {"type": "Quadratic", "parameters": {"coefficient": 2.0}}
    penalty_function_override = Column(JSON, nullable=True)
    
    # Hard constraint = infeasible if violated, Soft = apply penalty
    hard_constraint = Column(Boolean, default=False)
    
    # Tolerance for near-miss (within tolerance = no penalty)
    tolerance = Column(Float, default=0.0)
    
    # Notes
    notes = Column(String, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    arc = relationship("FlowArc", back_populates="quality_objectives")
    quality_field = relationship("QualityField")

    def __repr__(self):
        return f"<ArcQualityObjective {self.objective_type} for {self.quality_field_id[:8]}...>"


# =============================================================================
# 3.14 Transport Time Model
# =============================================================================

class TransportTimeModel(Base):
    """
    Models haulage/transport time between nodes.
    Used for cycle time calculation and equipment sizing.
    """
    __tablename__ = "transport_time_models"
    
    model_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String, nullable=False)
    
    # Model type
    # ConstantTime: Fixed time regardless of distance
    # DistanceSpeed: Time = distance / speed
    # CycleTimeByRoute: Lookup table by route
    model_type = Column(String, nullable=False)
    
    # Parameters (interpretation depends on model_type)
    # ConstantTime: {"time_minutes": 15}
    # DistanceSpeed: {"distance_m": 2000, "speed_loaded_kmh": 20, "speed_empty_kmh": 30}
    # CycleTimeByRoute: {"lookup": {"route_a": 12, "route_b": 18}}
    parameters = Column(JSON, nullable=False, default=dict)
    
    # Fixed time components
    load_time_minutes = Column(Float, default=3.0)
    dump_time_minutes = Column(Float, default=2.0)
    queue_time_minutes = Column(Float, default=1.0)
    
    # Route geometry reference (for visualization)
    route_geometry_reference = Column(JSON, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<TransportTimeModel {self.name} ({self.model_type})>"

    def calculate_cycle_time(self, distance_m: float = None) -> float:
        """
        Calculate total cycle time in minutes.
        """
        fixed_time = self.load_time_minutes + self.dump_time_minutes + self.queue_time_minutes
        
        if self.model_type == "ConstantTime":
            travel_time = self.parameters.get("time_minutes", 10)
        elif self.model_type == "DistanceSpeed":
            dist = distance_m or self.parameters.get("distance_m", 1000)
            speed_loaded = self.parameters.get("speed_loaded_kmh", 20)
            speed_empty = self.parameters.get("speed_empty_kmh", 30)
            # Convert to minutes
            time_loaded = (dist / 1000) / speed_loaded * 60
            time_empty = (dist / 1000) / speed_empty * 60
            travel_time = time_loaded + time_empty
        else:
            travel_time = 10  # Default
            
        return fixed_time + travel_time


# =============================================================================
# 3.11 Stockpile Config
# =============================================================================

class StockpileConfig(Base):
    """
    Configuration for a standard (non-staged) stockpile node.
    Tracks inventory and quality using weighted average method.
    """
    __tablename__ = "stockpile_configs"
    
    config_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False, unique=True)
    
    # Inventory tracking method
    # WeightedAverage: Track total tonnage and blended quality
    # ParcelTracked: Track individual parcels (detailed but complex)
    inventory_method = Column(String, default="WeightedAverage")
    
    # Reclaim method (for blending decisions)
    # FIFO: First in, first out
    # LIFO: Last in, first out
    # BlendedProportional: Proportional from all layers
    reclaim_method = Column(String, default="FIFO")
    
    # Capacity constraints
    max_capacity_tonnes = Column(Float, nullable=True)
    min_capacity_tonnes = Column(Float, default=0.0)  # Safety stock
    
    # Current state
    current_inventory_tonnes = Column(Float, default=0.0)
    current_grade_vector = Column(JSON, default=dict)
    
    # Parcel list (if ParcelTracked method)
    parcel_ids = Column(JSON, nullable=True)
    
    # Survey update policy
    # Replace: Survey overwrites calculated balance
    # ReconcileDelta: Survey adjusts by difference
    survey_update_policy = Column(String, default="Replace")
    
    # Last survey timestamp
    last_survey_at = Column(DateTime, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    node = relationship("FlowNode", back_populates="stockpile_config")

    def __repr__(self):
        return f"<StockpileConfig {self.current_inventory_tonnes}t>"


# =============================================================================
# 3.13 Wash Plant Config
# =============================================================================

class WashPlantConfig(Base):
    """
    Configuration for a coal handling and preparation plant (CHPP) node.
    """
    __tablename__ = "wash_plant_configs"
    
    config_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False, unique=True)
    
    # Capacity
    feed_capacity_tph = Column(Float, nullable=True)  # Tonnes per hour
    operating_hours_per_period = Column(Float, nullable=True)
    
    # Cutpoint selection mode
    # FixedRD: Use fixed relative density cutpoint
    # TargetQuality: Determine RD to achieve target quality
    # OptimiserSelected: Let optimizer choose optimal cutpoint
    cutpoint_selection_mode = Column(String, default="TargetQuality")
    
    # Fixed cutpoint (if mode is FixedRD)
    default_rd_cutpoint = Column(Float, nullable=True)
    
    # Target matching mode (if mode is TargetQuality)
    # Nearest: Use nearest wash table row
    # Interpolated: Interpolate between rows
    target_matching_mode = Column(String, default="Interpolated")
    
    # Reference to wash table
    wash_table_id = Column(String, ForeignKey("wash_tables.wash_table_id"), nullable=True)
    
    # Yield adjustment (plant efficiency factor)
    yield_adjustment_factor = Column(Float, default=1.0)
    
    # Quality adjustment model (optional correction factors)
    quality_adjustment_model = Column(JSON, nullable=True)
    
    # Product stream definitions
    # Example: [{"name": "Prime", "target_ash": 10.0}, {"name": "Secondary", "target_ash": 14.0}]
    product_stream_definitions = Column(JSON, nullable=True)
    
    # Reject stream configuration
    reject_destination_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=True)
    
    # Multi-stage configuration
    multistage_enabled = Column(Boolean, default=False)
    second_stage_wash_table_id = Column(String, nullable=True)
    second_stage_rules = Column(JSON, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    node = relationship("FlowNode", back_populates="wash_plant_config")
    wash_table = relationship("WashTable", foreign_keys=[wash_table_id])

    def __repr__(self):
        return f"<WashPlantConfig {self.feed_capacity_tph}tph>"

