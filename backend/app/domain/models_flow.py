from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from ..database import Base
import uuid

# 3.10 Flow Network
class FlowNetwork(Base):
    __tablename__ = "flow_networks"
    network_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False)
    
    nodes = relationship("FlowNode", back_populates="network")
    arcs = relationship("FlowArc", back_populates="network")

class FlowNode(Base):
    __tablename__ = "flow_nodes"
    node_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network_id = Column(String, ForeignKey("flow_networks.network_id"))
    node_type = Column(String, nullable=False) # Source, Stockpile, WashPlant, Dump
    name = Column(String, nullable=False)
    location_geometry = Column(JSON)
    capacity_tonnes = Column(Float)
    inventory_tracking_enabled = Column(Boolean, default=False)
    
    # Polymorphic configs (One-to-One ideally, here simplified as optional columns or separate tables)
    # We will use separate tables for config to keep it clean
    
    network = relationship("FlowNetwork", back_populates="nodes")
    stockpile_config = relationship("StockpileConfig", uselist=False, back_populates="node")
    wash_plant_config = relationship("WashPlantConfig", uselist=False, back_populates="node")

class FlowArc(Base):
    __tablename__ = "flow_arcs"
    arc_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network_id = Column(String, ForeignKey("flow_networks.network_id"))
    from_node_id = Column(String, ForeignKey("flow_nodes.node_id"))
    to_node_id = Column(String, ForeignKey("flow_nodes.node_id"))
    allowed_material_types = Column(JSON) # List of material_type_ids
    capacity_tonnes_per_period = Column(Float)
    transport_time_model_id = Column(String)
    
    network = relationship("FlowNetwork", back_populates="arcs")

# 3.11 Stockpile Config
class StockpileConfig(Base):
    __tablename__ = "stockpile_configs"
    config_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("flow_nodes.node_id"))
    inventory_method = Column(String, default="WeightedAverage")
    reclaim_method = Column(String, default="FIFO")
    max_capacity_tonnes = Column(Float)
    current_inventory_tonnes = Column(Float, default=0.0)
    current_grade_vector = Column(JSON, default={}) # {CV: 20, Ash: 15}
    
    node = relationship("FlowNode", back_populates="stockpile_config")

# 3.13 Wash Plant Config
class WashPlantConfig(Base):
    __tablename__ = "wash_plant_configs"
    config_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("flow_nodes.node_id"))
    feed_capacity_tph = Column(Float)
    cutpoint_selection_mode = Column(String, default="TargetQuality")
    wash_table_id = Column(String)
    yield_adjustment_factor = Column(Float, default=1.0)
    
    node = relationship("FlowNode", back_populates="wash_plant_config")
