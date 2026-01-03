"""
Flow Optimizer Service - Section 3.10 of Enterprise Specification

Determines optimal routing of material through the flow network:
- Evaluates quality constraints and penalty costs per arc
- Routes parcels to destinations optimizing for objectives
- Generates decision explanations for transparency
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
import uuid
from datetime import datetime

from ..domain.models_flow import FlowNetwork, FlowNode, FlowArc, ArcQualityObjective
from ..domain.models_parcel import Parcel
from ..domain.models_schedule_results import FlowResult, DecisionExplanation
from .blending_service import BlendingService, blending_service


@dataclass
class RoutingDecision:
    """A decision about routing a parcel through the network."""
    parcel_id: str
    from_node_id: str
    to_node_id: str
    arc_id: str
    tonnes: float
    quality_vector: Dict[str, float]
    penalty_cost: float
    explanation: str


@dataclass
class PeriodFlowSummary:
    """Summary of all flows in a period."""
    period_id: str
    total_tonnes: float
    total_cost: float
    total_benefit: float
    total_penalty: float
    flow_results: List[FlowResult]
    explanations: List[DecisionExplanation]


class FlowOptimizer:
    """
    Determines optimal routing of material through the flow network.
    Evaluates quality constraints and penalty costs.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.blending = blending_service
    
    def get_network_for_site(self, site_id: str) -> Optional[FlowNetwork]:
        """Get the active flow network for a site."""
        return self.db.query(FlowNetwork)\
            .filter(FlowNetwork.site_id == site_id)\
            .filter(FlowNetwork.is_active == True)\
            .first()
    
    def get_outgoing_arcs(self, node_id: str) -> List[FlowArc]:
        """Get all enabled arcs leaving a node."""
        return self.db.query(FlowArc)\
            .filter(FlowArc.from_node_id == node_id)\
            .filter(FlowArc.is_enabled == True)\
            .all()
    
    def get_arc_objectives(self, arc_id: str) -> List[ArcQualityObjective]:
        """Get quality objectives for an arc."""
        return self.db.query(ArcQualityObjective)\
            .filter(ArcQualityObjective.arc_id == arc_id)\
            .all()
    
    def optimize_period_flows(
        self,
        period_id: str,
        parcels: List[Parcel],
        network: FlowNetwork,
        schedule_version_id: str
    ) -> PeriodFlowSummary:
        """
        Determines where each parcel should go in a given period.
        
        Args:
            period_id: The period being scheduled
            parcels: Available parcels to route
            network: The flow network to use
            schedule_version_id: Target schedule version
            
        Returns:
            PeriodFlowSummary with flows and explanations
        """
        flow_results = []
        explanations = []
        total_cost = 0.0
        total_benefit = 0.0
        total_penalty = 0.0
        total_tonnes = 0.0
        
        # Track node inventories for this period
        node_throughput = {}  # node_id -> tonnes processed
        
        for parcel in parcels:
            # Find the best route for this parcel
            decision = self._route_parcel(parcel, network, node_throughput)
            
            if decision:
                # Create FlowResult
                flow_result = FlowResult(
                    flow_result_id=str(uuid.uuid4()),
                    schedule_version_id=schedule_version_id,
                    period_id=period_id,
                    from_node_id=decision.from_node_id,
                    to_node_id=decision.to_node_id,
                    arc_id=decision.arc_id,
                    material_type_id=parcel.material_type_id,
                    tonnes=decision.tonnes,
                    quality_vector=decision.quality_vector,
                    cost=self._calculate_arc_cost(decision),
                    benefit=self._calculate_arc_benefit(decision),
                    penalty_cost=decision.penalty_cost
                )
                flow_results.append(flow_result)
                
                # Update tracking
                total_cost += flow_result.cost
                total_benefit += flow_result.benefit
                total_penalty += decision.penalty_cost
                total_tonnes += decision.tonnes
                
                # Update node throughput
                node_throughput[decision.to_node_id] = (
                    node_throughput.get(decision.to_node_id, 0) + decision.tonnes
                )
                
                # Generate explanation if significant penalty
                if decision.penalty_cost > 0:
                    explanation = DecisionExplanation(
                        explanation_id=str(uuid.uuid4()),
                        schedule_version_id=schedule_version_id,
                        period_id=period_id,
                        decision_type="Routing",
                        related_arc_id=decision.arc_id,
                        summary_text=decision.explanation,
                        binding_constraints=[],
                        penalty_breakdown=[{
                            "parcel_id": parcel.parcel_id,
                            "penalty": decision.penalty_cost
                        }],
                        total_penalty=decision.penalty_cost
                    )
                    explanations.append(explanation)
        
        return PeriodFlowSummary(
            period_id=period_id,
            total_tonnes=total_tonnes,
            total_cost=total_cost,
            total_benefit=total_benefit,
            total_penalty=total_penalty,
            flow_results=flow_results,
            explanations=explanations
        )
    
    def _route_parcel(
        self,
        parcel: Parcel,
        network: FlowNetwork,
        node_throughput: Dict[str, float]
    ) -> Optional[RoutingDecision]:
        """
        Find the best route for a single parcel.
        Uses greedy evaluation of available arcs.
        """
        # Find source node (parcel's origin)
        source_reference = parcel.source_reference or ""
        
        # Parse source reference to find from_node
        # Format: "area:{area_id}:slice:{index}" or "stockpile:{node_id}"
        from_node_id = None
        if source_reference.startswith("stockpile:"):
            from_node_id = source_reference.replace("stockpile:", "")
        else:
            # For mining sources, find the source node
            # Default to first source node in network
            source_nodes = self.db.query(FlowNode)\
                .filter(FlowNode.network_id == network.network_id)\
                .filter(FlowNode.node_type == "Source")\
                .all()
            if source_nodes:
                from_node_id = source_nodes[0].node_id
        
        if not from_node_id:
            return None
        
        # Get outgoing arcs
        arcs = self.get_outgoing_arcs(from_node_id)
        if not arcs:
            return None
        
        # Evaluate each arc
        best_arc = None
        best_penalty = float('inf')
        best_explanation = ""
        
        for arc in arcs:
            # Check material type eligibility
            if arc.allowed_material_types:
                if parcel.material_type_id not in arc.allowed_material_types:
                    continue
            
            # Check capacity
            current_throughput = node_throughput.get(arc.to_node_id, 0)
            if arc.capacity_tonnes_per_period:
                remaining_capacity = arc.capacity_tonnes_per_period - current_throughput
                if parcel.quantity_tonnes > remaining_capacity:
                    continue  # Doesn't fit
            
            # Evaluate quality penalty
            penalty, explanation = self.evaluate_route_penalty(parcel, arc)
            
            # Also consider arc priority (higher = preferred)
            adjusted_penalty = penalty - (arc.priority or 0) * 0.01
            
            if adjusted_penalty < best_penalty:
                best_penalty = adjusted_penalty
                best_arc = arc
                best_explanation = explanation
        
        if not best_arc:
            return None
        
        return RoutingDecision(
            parcel_id=parcel.parcel_id,
            from_node_id=from_node_id,
            to_node_id=best_arc.to_node_id,
            arc_id=best_arc.arc_id,
            tonnes=parcel.quantity_tonnes,
            quality_vector=parcel.quality_vector or {},
            penalty_cost=max(0, best_penalty),  # Don't allow negative penalty
            explanation=best_explanation
        )
    
    def evaluate_route_penalty(
        self,
        parcel: Parcel,
        arc: FlowArc,
        existing_blend: Dict[str, float] = None
    ) -> Tuple[float, str]:
        """
        Calculates penalty cost for routing parcel through arc.
        Considers quality objectives and capacity.
        
        Returns:
            Tuple of (penalty_cost, explanation_text)
        """
        # Get quality objectives for this arc
        objectives = self.get_arc_objectives(arc.arc_id)
        
        if not objectives:
            return 0.0, "No quality constraints on this route"
        
        # Get parcel quality
        parcel_quality = parcel.quality_vector or {}
        
        # If there's an existing blend at destination, consider it
        if existing_blend:
            # Simulate adding this parcel to the blend
            # For simplicity just use parcel quality for now
            test_quality = parcel_quality
        else:
            test_quality = parcel_quality
        
        # Check compliance
        obj_dicts = [
            {
                'quality_field_id': obj.quality_field_id,
                'objective_type': obj.objective_type,
                'target_value': obj.target_value,
                'min_value': obj.min_value,
                'max_value': obj.max_value,
                'penalty_weight': obj.penalty_weight,
                'hard_constraint': obj.hard_constraint,
                'tolerance': obj.tolerance
            }
            for obj in objectives
        ]
        
        result = self.blending.check_spec_compliance(test_quality, obj_dicts)
        
        if result.violations:
            explanation = f"Quality violations: {', '.join(result.violations[:3])}"
            if len(result.violations) > 3:
                explanation += f" (+{len(result.violations) - 3} more)"
        else:
            explanation = "Quality within spec"
        
        return result.total_penalty, explanation
    
    def _calculate_arc_cost(self, decision: RoutingDecision) -> float:
        """Calculate transport/processing cost for this route."""
        arc = self.db.query(FlowArc)\
            .filter(FlowArc.arc_id == decision.arc_id)\
            .first()
        
        if arc and arc.cost_per_tonne:
            return arc.cost_per_tonne * decision.tonnes
        return 0.0
    
    def _calculate_arc_benefit(self, decision: RoutingDecision) -> float:
        """Calculate value/benefit for this route."""
        arc = self.db.query(FlowArc)\
            .filter(FlowArc.arc_id == decision.arc_id)\
            .first()
        
        if arc and arc.benefit_per_tonne:
            return arc.benefit_per_tonne * decision.tonnes
        return 0.0
    
    def generate_explanations(
        self,
        flows: List[FlowResult],
        binding_constraints: List[str],
        schedule_version_id: str,
        period_id: str
    ) -> List[DecisionExplanation]:
        """
        Creates explanation artifacts for routing decisions.
        Groups and summarizes decisions for human readability.
        """
        explanations = []
        
        # Group flows by destination
        dest_flows = {}
        for flow in flows:
            dest = flow.to_node_id
            if dest not in dest_flows:
                dest_flows[dest] = []
            dest_flows[dest].append(flow)
        
        # Create summary explanation for each destination
        for dest_id, dest_flow_list in dest_flows.items():
            total_tonnes = sum(f.tonnes for f in dest_flow_list)
            total_penalty = sum(f.penalty_cost for f in dest_flow_list)
            
            # Get destination node name
            node = self.db.query(FlowNode)\
                .filter(FlowNode.node_id == dest_id)\
                .first()
            dest_name = node.name if node else dest_id[:8]
            
            summary = f"Routed {total_tonnes:.0f}t to {dest_name}"
            if total_penalty > 0:
                summary += f" with penalty ${total_penalty:.0f}"
            
            explanation = DecisionExplanation(
                explanation_id=str(uuid.uuid4()),
                schedule_version_id=schedule_version_id,
                period_id=period_id,
                decision_type="Routing",
                related_node_id=dest_id,
                summary_text=summary,
                binding_constraints=binding_constraints,
                penalty_breakdown=[{
                    "flow_id": f.flow_result_id,
                    "tonnes": f.tonnes,
                    "penalty": f.penalty_cost
                } for f in dest_flow_list],
                total_penalty=total_penalty
            )
            explanations.append(explanation)
        
        return explanations
