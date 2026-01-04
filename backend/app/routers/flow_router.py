"""
Flow Network Router - API endpoints for flow network CRUD

Provides endpoints for:
- Flow network management (create, read, update, delete)
- Flow node operations (add, update, delete, position)
- Flow arc operations (add, update, delete)
- Quality objective configuration on arcs
- Network validation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain.models_flow import FlowNetwork, FlowNode, FlowArc, ArcQualityObjective
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uuid

router = APIRouter(prefix="/flow", tags=["Flow Network"])


# =============================================================================
# Pydantic Models
# =============================================================================

class FlowNodeCreate(BaseModel):
    """Create a new flow node."""
    name: str
    node_type: str  # SourcePit, Stockpile, StagedStockpile, WashPlant, Destination, Dump
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    capacity: Optional[float] = None
    feed_capacity_tph: Optional[float] = None


class FlowNodeUpdate(BaseModel):
    """Update a flow node."""
    name: Optional[str] = None
    node_type: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    capacity: Optional[float] = None
    feed_capacity_tph: Optional[float] = None


class FlowArcCreate(BaseModel):
    """Create a new flow arc."""
    from_node_id: str
    to_node_id: str
    max_throughput_tph: Optional[float] = None
    priority: Optional[int] = 0
    allowed_material_types: Optional[List[str]] = None
    cost_per_tonne: Optional[float] = 0.0


class FlowArcUpdate(BaseModel):
    """Update a flow arc."""
    max_throughput_tph: Optional[float] = None
    priority: Optional[int] = None
    allowed_material_types: Optional[List[str]] = None
    cost_per_tonne: Optional[float] = None


class QualityObjectiveCreate(BaseModel):
    """Create a quality objective for an arc."""
    quality_field_id: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    target_value: Optional[float] = None
    softness: Optional[str] = "Medium"  # Hard, Medium, Soft
    penalty_weight: Optional[float] = 1.0


class NetworkLayout(BaseModel):
    """Full network layout for save/load."""
    nodes: List[Dict[str, Any]]
    arcs: List[Dict[str, Any]]


# =============================================================================
# Network Endpoints
# =============================================================================

@router.get("/networks/{site_id}")
def get_networks_for_site(site_id: str, db: Session = Depends(get_db)):
    """Get all flow networks for a site."""
    networks = db.query(FlowNetwork).filter(FlowNetwork.site_id == site_id).all()
    return [{
        "network_id": n.network_id,
        "site_id": n.site_id,
        "name": n.name,
        "description": n.description,
        "is_active": n.is_active
    } for n in networks]


@router.post("/networks")
def create_network(site_id: str, name: str, description: str = None, db: Session = Depends(get_db)):
    """Create a new flow network."""
    network = FlowNetwork(
        network_id=str(uuid.uuid4()),
        site_id=site_id,
        name=name,
        description=description,
        is_active=True
    )
    db.add(network)
    db.commit()
    db.refresh(network)
    return network


@router.get("/networks/{network_id}/full")
def get_network_full(network_id: str, db: Session = Depends(get_db)):
    """Get complete network with all nodes, arcs, and quality objectives."""
    network = db.query(FlowNetwork).filter(FlowNetwork.network_id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    nodes = db.query(FlowNode).filter(FlowNode.network_id == network_id).all()
    arcs = db.query(FlowArc).filter(FlowArc.network_id == network_id).all()
    
    # Get quality objectives for each arc
    arc_data = []
    for arc in arcs:
        objectives = db.query(ArcQualityObjective).filter(
            ArcQualityObjective.arc_id == arc.arc_id
        ).all()
        
        arc_data.append({
            "arc_id": arc.arc_id,
            "from_node_id": arc.from_node_id,
            "to_node_id": arc.to_node_id,
            "max_throughput_tph": arc.max_throughput_tph,
            "priority": arc.priority,
            "allowed_material_types": arc.allowed_material_types,
            "cost_per_tonne": arc.cost_per_tonne,
            "quality_objectives": [{
                "objective_id": obj.objective_id,
                "quality_field_id": obj.quality_field_id,
                "min_value": obj.min_value,
                "max_value": obj.max_value,
                "target_value": obj.target_value,
                "softness": obj.softness,
                "penalty_weight": obj.penalty_weight
            } for obj in objectives]
        })
    
    return {
        "network_id": network.network_id,
        "name": network.name,
        "description": network.description,
        "is_active": network.is_active,
        "nodes": [{
            "node_id": n.node_id,
            "name": n.name,
            "node_type": n.node_type,
            "position_x": n.position_x,
            "position_y": n.position_y,
            "capacity": n.capacity,
            "feed_capacity_tph": n.feed_capacity_tph,
            "current_inventory": n.current_inventory
        } for n in nodes],
        "arcs": arc_data
    }


@router.delete("/networks/{network_id}")
def delete_network(network_id: str, db: Session = Depends(get_db)):
    """Delete a flow network (cascades to nodes and arcs)."""
    network = db.query(FlowNetwork).filter(FlowNetwork.network_id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Delete quality objectives first
    arcs = db.query(FlowArc).filter(FlowArc.network_id == network_id).all()
    for arc in arcs:
        db.query(ArcQualityObjective).filter(
            ArcQualityObjective.arc_id == arc.arc_id
        ).delete()
    
    # Delete arcs and nodes
    db.query(FlowArc).filter(FlowArc.network_id == network_id).delete()
    db.query(FlowNode).filter(FlowNode.network_id == network_id).delete()
    
    db.delete(network)
    db.commit()
    return {"message": "Network deleted"}


# =============================================================================
# Node Endpoints
# =============================================================================

@router.post("/networks/{network_id}/nodes")
def add_node(network_id: str, node: FlowNodeCreate, db: Session = Depends(get_db)):
    """Add a new node to the network."""
    network = db.query(FlowNetwork).filter(FlowNetwork.network_id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    new_node = FlowNode(
        node_id=str(uuid.uuid4()),
        network_id=network_id,
        name=node.name,
        node_type=node.node_type,
        position_x=node.position_x or 100,
        position_y=node.position_y or 100,
        capacity=node.capacity,
        feed_capacity_tph=node.feed_capacity_tph
    )
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return new_node


@router.put("/nodes/{node_id}")
def update_node(node_id: str, updates: FlowNodeUpdate, db: Session = Depends(get_db)):
    """Update a node's properties."""
    node = db.query(FlowNode).filter(FlowNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    if updates.name is not None:
        node.name = updates.name
    if updates.node_type is not None:
        node.node_type = updates.node_type
    if updates.position_x is not None:
        node.position_x = updates.position_x
    if updates.position_y is not None:
        node.position_y = updates.position_y
    if updates.capacity is not None:
        node.capacity = updates.capacity
    if updates.feed_capacity_tph is not None:
        node.feed_capacity_tph = updates.feed_capacity_tph
    
    db.commit()
    db.refresh(node)
    return node


@router.put("/nodes/{node_id}/position")
def update_node_position(node_id: str, x: float, y: float, db: Session = Depends(get_db)):
    """Update just the node position (for drag operations)."""
    node = db.query(FlowNode).filter(FlowNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node.position_x = x
    node.position_y = y
    db.commit()
    return {"node_id": node_id, "x": x, "y": y}


@router.delete("/nodes/{node_id}")
def delete_node(node_id: str, db: Session = Depends(get_db)):
    """Delete a node (also removes connected arcs)."""
    node = db.query(FlowNode).filter(FlowNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Delete connected arcs and their quality objectives
    connected_arcs = db.query(FlowArc).filter(
        (FlowArc.from_node_id == node_id) | (FlowArc.to_node_id == node_id)
    ).all()
    
    for arc in connected_arcs:
        db.query(ArcQualityObjective).filter(
            ArcQualityObjective.arc_id == arc.arc_id
        ).delete()
    
    db.query(FlowArc).filter(
        (FlowArc.from_node_id == node_id) | (FlowArc.to_node_id == node_id)
    ).delete()
    
    db.delete(node)
    db.commit()
    return {"message": "Node deleted", "arcs_removed": len(connected_arcs)}


# =============================================================================
# Arc Endpoints
# =============================================================================

@router.post("/networks/{network_id}/arcs")
def add_arc(network_id: str, arc: FlowArcCreate, db: Session = Depends(get_db)):
    """Add a new arc to the network."""
    network = db.query(FlowNetwork).filter(FlowNetwork.network_id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Verify both nodes exist
    from_node = db.query(FlowNode).filter(FlowNode.node_id == arc.from_node_id).first()
    to_node = db.query(FlowNode).filter(FlowNode.node_id == arc.to_node_id).first()
    if not from_node or not to_node:
        raise HTTPException(status_code=400, detail="Invalid node references")
    
    # Check for duplicate arc
    existing = db.query(FlowArc).filter(
        FlowArc.from_node_id == arc.from_node_id,
        FlowArc.to_node_id == arc.to_node_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Arc already exists between these nodes")
    
    new_arc = FlowArc(
        arc_id=str(uuid.uuid4()),
        network_id=network_id,
        from_node_id=arc.from_node_id,
        to_node_id=arc.to_node_id,
        max_throughput_tph=arc.max_throughput_tph or 500,
        priority=arc.priority or 0,
        allowed_material_types=arc.allowed_material_types,
        cost_per_tonne=arc.cost_per_tonne or 0
    )
    db.add(new_arc)
    db.commit()
    db.refresh(new_arc)
    return new_arc


@router.put("/arcs/{arc_id}")
def update_arc(arc_id: str, updates: FlowArcUpdate, db: Session = Depends(get_db)):
    """Update an arc's properties."""
    arc = db.query(FlowArc).filter(FlowArc.arc_id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")
    
    if updates.max_throughput_tph is not None:
        arc.max_throughput_tph = updates.max_throughput_tph
    if updates.priority is not None:
        arc.priority = updates.priority
    if updates.allowed_material_types is not None:
        arc.allowed_material_types = updates.allowed_material_types
    if updates.cost_per_tonne is not None:
        arc.cost_per_tonne = updates.cost_per_tonne
    
    db.commit()
    db.refresh(arc)
    return arc


@router.delete("/arcs/{arc_id}")
def delete_arc(arc_id: str, db: Session = Depends(get_db)):
    """Delete an arc."""
    arc = db.query(FlowArc).filter(FlowArc.arc_id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")
    
    # Delete quality objectives first
    db.query(ArcQualityObjective).filter(
        ArcQualityObjective.arc_id == arc_id
    ).delete()
    
    db.delete(arc)
    db.commit()
    return {"message": "Arc deleted"}


# =============================================================================
# Quality Objective Endpoints
# =============================================================================

@router.get("/arcs/{arc_id}/objectives")
def get_arc_objectives(arc_id: str, db: Session = Depends(get_db)):
    """Get quality objectives for an arc."""
    objectives = db.query(ArcQualityObjective).filter(
        ArcQualityObjective.arc_id == arc_id
    ).all()
    return objectives


@router.post("/arcs/{arc_id}/objectives")
def add_arc_objective(arc_id: str, objective: QualityObjectiveCreate, db: Session = Depends(get_db)):
    """Add a quality objective to an arc."""
    arc = db.query(FlowArc).filter(FlowArc.arc_id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")
    
    new_obj = ArcQualityObjective(
        objective_id=str(uuid.uuid4()),
        arc_id=arc_id,
        quality_field_id=objective.quality_field_id,
        min_value=objective.min_value,
        max_value=objective.max_value,
        target_value=objective.target_value,
        softness=objective.softness,
        penalty_weight=objective.penalty_weight
    )
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


@router.delete("/objectives/{objective_id}")
def delete_objective(objective_id: str, db: Session = Depends(get_db)):
    """Delete a quality objective."""
    obj = db.query(ArcQualityObjective).filter(
        ArcQualityObjective.objective_id == objective_id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")
    
    db.delete(obj)
    db.commit()
    return {"message": "Objective deleted"}


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/networks/{network_id}/layout")
def save_network_layout(network_id: str, layout: NetworkLayout, db: Session = Depends(get_db)):
    """
    Save complete network layout (bulk create/update).
    This is used by the frontend editor to save the entire graph at once.
    """
    network = db.query(FlowNetwork).filter(FlowNetwork.network_id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Track existing entities for updates vs creates
    existing_nodes = {n.node_id: n for n in db.query(FlowNode).filter(
        FlowNode.network_id == network_id
    ).all()}
    
    existing_arcs = {a.arc_id: a for a in db.query(FlowArc).filter(
        FlowArc.network_id == network_id
    ).all()}
    
    node_id_map = {}  # frontend ID -> backend ID
    
    # Process nodes
    for node_data in layout.nodes:
        frontend_id = node_data.get('id') or node_data.get('node_id')
        
        if frontend_id in existing_nodes:
            # Update existing
            node = existing_nodes[frontend_id]
            node.name = node_data.get('name', node.name)
            node.node_type = node_data.get('type') or node_data.get('node_type', node.node_type)
            node.position_x = node_data.get('x') or node_data.get('position_x', node.position_x)
            node.position_y = node_data.get('y') or node_data.get('position_y', node.position_y)
            node.capacity = node_data.get('capacity', node.capacity)
            node.feed_capacity_tph = node_data.get('feedCapacity') or node_data.get('feed_capacity_tph', node.feed_capacity_tph)
            node_id_map[frontend_id] = frontend_id
        else:
            # Create new
            new_id = str(uuid.uuid4())
            new_node = FlowNode(
                node_id=new_id,
                network_id=network_id,
                name=node_data.get('name', 'Unnamed'),
                node_type=node_data.get('type') or node_data.get('node_type', 'Stockpile'),
                position_x=node_data.get('x') or node_data.get('position_x', 100),
                position_y=node_data.get('y') or node_data.get('position_y', 100),
                capacity=node_data.get('capacity'),
                feed_capacity_tph=node_data.get('feedCapacity') or node_data.get('feed_capacity_tph')
            )
            db.add(new_node)
            node_id_map[frontend_id] = new_id
    
    # Process arcs
    for arc_data in layout.arcs:
        frontend_id = arc_data.get('id') or arc_data.get('arc_id')
        from_id = arc_data.get('from') or arc_data.get('from_node_id')
        to_id = arc_data.get('to') or arc_data.get('to_node_id')
        
        # Map frontend IDs to backend IDs if needed
        backend_from = node_id_map.get(from_id, from_id)
        backend_to = node_id_map.get(to_id, to_id)
        
        if frontend_id in existing_arcs:
            # Update existing
            arc = existing_arcs[frontend_id]
            arc.from_node_id = backend_from
            arc.to_node_id = backend_to
            arc.max_throughput_tph = arc_data.get('maxThroughput') or arc_data.get('max_throughput_tph', arc.max_throughput_tph)
            arc.priority = arc_data.get('priority', arc.priority)
            arc.allowed_material_types = arc_data.get('materialFilter') or arc_data.get('allowed_material_types')
        else:
            # Create new
            new_arc = FlowArc(
                arc_id=str(uuid.uuid4()),
                network_id=network_id,
                from_node_id=backend_from,
                to_node_id=backend_to,
                max_throughput_tph=arc_data.get('maxThroughput') or arc_data.get('max_throughput_tph', 500),
                priority=arc_data.get('priority', 0),
                allowed_material_types=arc_data.get('materialFilter') or arc_data.get('allowed_material_types')
            )
            db.add(new_arc)
    
    db.commit()
    
    return {"message": "Layout saved", "nodes": len(layout.nodes), "arcs": len(layout.arcs)}


# =============================================================================
# Validation
# =============================================================================

@router.get("/networks/{network_id}/validate")
def validate_network(network_id: str, db: Session = Depends(get_db)):
    """
    Validate the network configuration.
    Returns warnings about potential issues.
    """
    warnings = []
    
    nodes = db.query(FlowNode).filter(FlowNode.network_id == network_id).all()
    arcs = db.query(FlowArc).filter(FlowArc.network_id == network_id).all()
    
    node_ids = {n.node_id for n in nodes}
    from_ids = {a.from_node_id for a in arcs}
    to_ids = {a.to_node_id for a in arcs}
    connected_ids = from_ids | to_ids
    
    # Check for disconnected nodes
    for node in nodes:
        if node.node_id not in connected_ids:
            warnings.append({
                "type": "disconnected_node",
                "severity": "warning",
                "node_id": node.node_id,
                "message": f"Node '{node.name}' is not connected to any arcs"
            })
    
    # Check for missing capacity
    for node in nodes:
        if node.node_type in ['Stockpile', 'StagedStockpile'] and not node.capacity:
            warnings.append({
                "type": "missing_capacity",
                "severity": "info",
                "node_id": node.node_id,
                "message": f"Stockpile '{node.name}' has no capacity defined"
            })
    
    # Check for arcs without capacity
    for arc in arcs:
        if not arc.max_throughput_tph:
            from_node = next((n for n in nodes if n.node_id == arc.from_node_id), None)
            to_node = next((n for n in nodes if n.node_id == arc.to_node_id), None)
            warnings.append({
                "type": "missing_arc_capacity",
                "severity": "info",
                "arc_id": arc.arc_id,
                "message": f"Arc from '{from_node.name if from_node else '?'}' to '{to_node.name if to_node else '?'}' has no capacity limit"
            })
    
    # Check for source pits without outgoing arcs
    for node in nodes:
        if node.node_type == 'SourcePit' and node.node_id not in from_ids:
            warnings.append({
                "type": "dead_end_source",
                "severity": "error",
                "node_id": node.node_id,
                "message": f"Source pit '{node.name}' has no outgoing arcs"
            })
    
    # Check for destinations without incoming arcs
    for node in nodes:
        if node.node_type == 'Destination' and node.node_id not in to_ids:
            warnings.append({
                "type": "unreachable_destination",
                "severity": "error",
                "node_id": node.node_id,
                "message": f"Destination '{node.name}' has no incoming arcs"
            })
    
    return {
        "valid": len([w for w in warnings if w["severity"] == "error"]) == 0,
        "warning_count": len(warnings),
        "warnings": warnings
    }
