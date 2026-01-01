from sqlalchemy import Column, String, Float, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..database import Base

class FlowNetwork(Base):
    __tablename__ = "flow_networks"

    network_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="flow_networks")
    nodes = relationship("FlowNode", back_populates="network")
    arcs = relationship("FlowArc", back_populates="network")


class FlowNode(Base):
    __tablename__ = "flow_nodes"

    node_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network_id = Column(String, ForeignKey("flow_networks.network_id"))
    node_type = Column(String) # Source, Stockpile, WashPlant, Dump, ProductSink
    name = Column(String)
    capacity_tonnes = Column(Float, nullable=True)
    inventory_tracking_enabled = Column(Boolean, default=False)
    
    # Inventory State
    current_tonnage = Column(Float, default=0.0)
    current_grade = Column(Float, default=0.0) # Weighted Average
    
    # 3D Context
    location_geometry = Column(JSON, nullable=True)

    network = relationship("FlowNetwork", back_populates="nodes")
    # Arcs defined roughly via adjacency list or FlowArc object
    arcs_outgoing = relationship("FlowArc", foreign_keys="FlowArc.from_node_id", back_populates="from_node")
    arcs_incoming = relationship("FlowArc", foreign_keys="FlowArc.to_node_id", back_populates="to_node")


class FlowArc(Base):
    __tablename__ = "flow_arcs"

    arc_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network_id = Column(String, ForeignKey("flow_networks.network_id"))
    from_node_id = Column(String, ForeignKey("flow_nodes.node_id"))
    to_node_id = Column(String, ForeignKey("flow_nodes.node_id"))
    
    allowed_material_type_ids = Column(JSON, default=[]) # List of material IDs
    capacity_tonnes_per_hour = Column(Float, nullable=True)
    cost_per_tonne = Column(Float, default=0.0)
    
    network = relationship("FlowNetwork", back_populates="arcs")
    from_node = relationship("FlowNode", foreign_keys=[from_node_id], back_populates="arcs_outgoing")
    to_node = relationship("FlowNode", foreign_keys=[to_node_id], back_populates="arcs_incoming")
    
    quality_objectives = relationship("ArcQualityObjective", back_populates="arc")


class ArcQualityObjective(Base):
    __tablename__ = "arc_quality_objectives"

    objective_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    arc_id = Column(String, ForeignKey("flow_arcs.arc_id"))
    quality_field_id = Column(String) # References QualityField.id but strict FK might be cyclic/complex, keeping loose for now
    
    objective_type = Column(String) # Target, Min, Max
    target_value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    penalty_weight = Column(Float, default=1.0)
    hard_constraint = Column(Boolean, default=False)

    arc = relationship("FlowArc", back_populates="quality_objectives")
