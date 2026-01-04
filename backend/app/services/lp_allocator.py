"""
LP Material Allocator - Section 5.5 of Enterprise Specification

Implements Linear Programming solver for optimal material routing:
- Minimizes total cost (transport + quality penalties)
- Respects capacity constraints (arcs, nodes)
- Respects blending constraints for quality targets
- Produces optimal allocation decisions

Uses scipy.optimize.linprog for solving.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
import numpy as np
from scipy.optimize import linprog, OptimizeResult
import uuid
from datetime import datetime

from ..domain.models_flow import FlowNetwork, FlowNode, FlowArc, ArcQualityObjective
from ..domain.models_parcel import Parcel
from ..domain.models_schedule_results import FlowResult, DecisionExplanation


@dataclass
class AllocationVariable:
    """Represents a decision variable: how much of parcel i goes to arc j."""
    var_index: int
    parcel_id: str
    parcel_index: int
    arc_id: str
    arc_index: int
    from_node_id: str
    to_node_id: str


@dataclass
class LPProblem:
    """Formulated LP problem ready for solving."""
    c: np.ndarray  # Objective coefficients (minimize)
    A_ub: np.ndarray  # Inequality constraint matrix
    b_ub: np.ndarray  # Inequality constraint bounds
    A_eq: np.ndarray  # Equality constraint matrix
    b_eq: np.ndarray  # Equality constraint bounds
    bounds: List[Tuple[float, float]]  # Variable bounds
    variables: List[AllocationVariable]
    parcels: List[Parcel]
    arcs: List[FlowArc]
    constraint_names: List[str]


@dataclass
class AllocationResult:
    """Result of LP material allocation."""
    success: bool
    allocations: List[Dict]  # List of {parcel_id, arc_id, tonnes}
    total_cost: float
    total_penalty: float
    binding_constraints: List[str]
    solver_message: str
    iterations: int
    flow_results: List[FlowResult] = field(default_factory=list)
    explanations: List[DecisionExplanation] = field(default_factory=list)


class LPMaterialAllocator:
    """
    Linear Programming based material allocator.
    
    Solves the allocation problem:
    
    Minimize:
        sum_i,j (cost_ij + penalty_ij) * x_ij
        
    Subject to:
        sum_j x_ij = parcel_i.quantity  for all parcels i (all material allocated)
        sum_i x_ij <= capacity_j        for all arcs j (capacity constraints)
        x_ij >= 0                       for all i,j (non-negativity)
        
    Quality constraints are handled via penalty costs in the objective.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._arc_cache = {}
        self._objective_cache = {}
    
    def get_network_for_site(self, site_id: str) -> Optional[FlowNetwork]:
        """Get the active flow network for a site."""
        return self.db.query(FlowNetwork)\
            .filter(FlowNetwork.site_id == site_id)\
            .filter(FlowNetwork.is_active == True)\
            .first()
    
    def get_available_arcs(self, network: FlowNetwork, source_node_ids: Set[str]) -> List[FlowArc]:
        """Get all enabled arcs from given source nodes."""
        arcs = self.db.query(FlowArc)\
            .filter(FlowArc.network_id == network.network_id)\
            .filter(FlowArc.from_node_id.in_(source_node_ids))\
            .filter(FlowArc.is_enabled == True)\
            .all()
        return arcs
    
    def get_arc_objectives(self, arc_id: str) -> List[ArcQualityObjective]:
        """Get quality objectives for an arc with caching."""
        if arc_id not in self._objective_cache:
            objectives = self.db.query(ArcQualityObjective)\
                .filter(ArcQualityObjective.arc_id == arc_id)\
                .all()
            self._objective_cache[arc_id] = objectives
        return self._objective_cache[arc_id]
    
    def solve_allocation(
        self,
        parcels: List[Parcel],
        network: FlowNetwork,
        period_id: str,
        schedule_version_id: str,
        existing_node_loads: Dict[str, float] = None
    ) -> AllocationResult:
        """
        Solve the material allocation problem using LP.
        
        Args:
            parcels: Available parcels to route
            network: The flow network
            period_id: Current period
            schedule_version_id: Target schedule version
            existing_node_loads: Pre-existing loads on nodes (from earlier in period)
            
        Returns:
            AllocationResult with optimal allocations
        """
        if not parcels:
            return AllocationResult(
                success=True,
                allocations=[],
                total_cost=0.0,
                total_penalty=0.0,
                binding_constraints=[],
                solver_message="No parcels to allocate",
                iterations=0
            )
        
        existing_node_loads = existing_node_loads or {}
        
        # Clear caches
        self._objective_cache = {}
        
        # Build the LP problem
        problem = self._build_lp_problem(parcels, network, existing_node_loads)
        
        if problem is None or len(problem.variables) == 0:
            return AllocationResult(
                success=False,
                allocations=[],
                total_cost=0.0,
                total_penalty=0.0,
                binding_constraints=[],
                solver_message="No feasible routes available",
                iterations=0
            )
        
        # Solve using scipy linprog
        result = self._solve_lp(problem)
        
        # Convert solution to allocations
        allocation_result = self._extract_solution(
            result, problem, period_id, schedule_version_id
        )
        
        return allocation_result
    
    def _build_lp_problem(
        self,
        parcels: List[Parcel],
        network: FlowNetwork,
        existing_node_loads: Dict[str, float]
    ) -> Optional[LPProblem]:
        """
        Build the LP problem formulation.
        
        Decision variables: x_ij = tonnes of parcel i routed through arc j
        """
        # Determine source nodes for parcels
        source_node_ids = set()
        parcel_sources = {}
        
        for parcel in parcels:
            source_ref = parcel.source_reference or ""
            if source_ref.startswith("stockpile:"):
                node_id = source_ref.replace("stockpile:", "")
                source_node_ids.add(node_id)
                parcel_sources[parcel.parcel_id] = node_id
            else:
                # Mining source - find first Source node
                source_nodes = self.db.query(FlowNode)\
                    .filter(FlowNode.network_id == network.network_id)\
                    .filter(FlowNode.node_type == "Source")\
                    .all()
                if source_nodes:
                    source_node_ids.add(source_nodes[0].node_id)
                    parcel_sources[parcel.parcel_id] = source_nodes[0].node_id
        
        if not source_node_ids:
            return None
        
        # Get available arcs from source nodes
        arcs = self.get_available_arcs(network, source_node_ids)
        if not arcs:
            return None
        
        # Build variable list: for each parcel, for each feasible arc
        variables = []
        var_index = 0
        
        for i, parcel in enumerate(parcels):
            parcel_source = parcel_sources.get(parcel.parcel_id)
            
            for j, arc in enumerate(arcs):
                # Check if arc is from this parcel's source
                if arc.from_node_id != parcel_source:
                    continue
                
                # Check material type eligibility
                if arc.allowed_material_types:
                    allowed = arc.allowed_material_types
                    if isinstance(allowed, str):
                        # Handle JSON string
                        import json
                        try:
                            allowed = json.loads(allowed)
                        except:
                            allowed = [allowed]
                    if parcel.material_type_id not in allowed:
                        continue
                
                variables.append(AllocationVariable(
                    var_index=var_index,
                    parcel_id=parcel.parcel_id,
                    parcel_index=i,
                    arc_id=arc.arc_id,
                    arc_index=j,
                    from_node_id=arc.from_node_id,
                    to_node_id=arc.to_node_id
                ))
                var_index += 1
        
        if not variables:
            return None
        
        n_vars = len(variables)
        n_parcels = len(parcels)
        n_arcs = len(arcs)
        
        # Build objective: minimize cost + penalty
        c = np.zeros(n_vars)
        
        for var in variables:
            parcel = parcels[var.parcel_index]
            arc = arcs[var.arc_index]
            
            # Transport/processing cost
            cost = arc.cost_per_tonne or 0.0
            
            # Quality penalty
            penalty = self._calculate_quality_penalty(parcel, arc)
            
            # Negative benefit (since we minimize)
            benefit = arc.benefit_per_tonne or 0.0
            
            c[var.var_index] = cost + penalty - benefit
        
        # Build equality constraints: all parcel material must be allocated
        # sum_j x_ij = parcel_i.quantity for all i
        A_eq = np.zeros((n_parcels, n_vars))
        b_eq = np.zeros(n_parcels)
        
        for var in variables:
            A_eq[var.parcel_index, var.var_index] = 1.0
        
        for i, parcel in enumerate(parcels):
            b_eq[i] = parcel.quantity_tonnes
        
        # Build inequality constraints: arc capacities and node capacities
        constraint_rows = []
        constraint_bounds = []
        constraint_names = []
        
        # Arc capacity constraints: sum_i x_ij <= capacity_j
        for j, arc in enumerate(arcs):
            if arc.capacity_tonnes_per_period and arc.capacity_tonnes_per_period > 0:
                row = np.zeros(n_vars)
                for var in variables:
                    if var.arc_index == j:
                        row[var.var_index] = 1.0
                constraint_rows.append(row)
                constraint_bounds.append(arc.capacity_tonnes_per_period)
                constraint_names.append(f"arc_capacity:{arc.arc_id[:8]}")
        
        # Node capacity constraints (for stockpiles/destinations)
        node_capacities = {}
        for node in self.db.query(FlowNode)\
            .filter(FlowNode.network_id == network.network_id).all():
            if node.capacity_tonnes and node.capacity_tonnes > 0:
                existing_load = existing_node_loads.get(node.node_id, 0)
                remaining = node.capacity_tonnes - existing_load
                if remaining > 0:
                    node_capacities[node.node_id] = remaining
        
        for node_id, remaining_capacity in node_capacities.items():
            row = np.zeros(n_vars)
            has_flow = False
            for var in variables:
                if var.to_node_id == node_id:
                    row[var.var_index] = 1.0
                    has_flow = True
            if has_flow:
                constraint_rows.append(row)
                constraint_bounds.append(remaining_capacity)
                constraint_names.append(f"node_capacity:{node_id[:8]}")
        
        # Build matrices
        if constraint_rows:
            A_ub = np.array(constraint_rows)
            b_ub = np.array(constraint_bounds)
        else:
            A_ub = np.zeros((0, n_vars))
            b_ub = np.zeros(0)
        
        # Variable bounds: 0 <= x_ij <= parcel_quantity
        bounds = []
        for var in variables:
            parcel = parcels[var.parcel_index]
            bounds.append((0, parcel.quantity_tonnes))
        
        return LPProblem(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            variables=variables,
            parcels=parcels,
            arcs=arcs,
            constraint_names=constraint_names
        )
    
    def _calculate_quality_penalty(self, parcel: Parcel, arc: FlowArc) -> float:
        """
        Calculate quality penalty cost for routing parcel through arc.
        
        Uses the arc's quality objectives to compute expected penalty.
        """
        objectives = self.get_arc_objectives(arc.arc_id)
        if not objectives:
            return 0.0
        
        parcel_quality = parcel.quality_vector or {}
        total_penalty = 0.0
        
        for obj in objectives:
            # Get the quality field name from the objective
            field_id = obj.quality_field_id
            
            # Try to find the value in parcel quality
            value = None
            for key, val in parcel_quality.items():
                if key == field_id or field_id in key:
                    value = val
                    break
            
            if value is None:
                continue
            
            # Calculate deviation based on objective type
            deviation = 0.0
            obj_type = obj.objective_type or "Target"
            
            if obj_type == "Min" and obj.min_value is not None:
                if value < obj.min_value:
                    deviation = obj.min_value - value
            elif obj_type == "Max" and obj.max_value is not None:
                if value > obj.max_value:
                    deviation = value - obj.max_value
            elif obj_type == "Target" and obj.target_value is not None:
                deviation = abs(value - obj.target_value)
            elif obj_type == "Range":
                if obj.min_value is not None and value < obj.min_value:
                    deviation = obj.min_value - value
                elif obj.max_value is not None and value > obj.max_value:
                    deviation = value - obj.max_value
            
            # Apply penalty weight
            weight = obj.penalty_weight or 1.0
            total_penalty += deviation * weight
        
        return total_penalty
    
    def _solve_lp(self, problem: LPProblem) -> OptimizeResult:
        """Solve the LP using scipy.optimize.linprog."""
        try:
            # Use the highs method (most robust)
            result = linprog(
                c=problem.c,
                A_ub=problem.A_ub if problem.A_ub.size > 0 else None,
                b_ub=problem.b_ub if problem.b_ub.size > 0 else None,
                A_eq=problem.A_eq if problem.A_eq.size > 0 else None,
                b_eq=problem.b_eq if problem.b_eq.size > 0 else None,
                bounds=problem.bounds,
                method='highs'
            )
            return result
        except Exception as e:
            # Return a failed result
            class FailedResult:
                success = False
                message = str(e)
                x = np.zeros(len(problem.variables))
                fun = 0.0
                nit = 0
                slack = np.zeros(0)
            return FailedResult()
    
    def _extract_solution(
        self,
        result: OptimizeResult,
        problem: LPProblem,
        period_id: str,
        schedule_version_id: str
    ) -> AllocationResult:
        """Extract allocation decisions from LP solution."""
        if not result.success:
            return AllocationResult(
                success=False,
                allocations=[],
                total_cost=0.0,
                total_penalty=0.0,
                binding_constraints=[],
                solver_message=getattr(result, 'message', 'Optimization failed'),
                iterations=getattr(result, 'nit', 0)
            )
        
        allocations = []
        flow_results = []
        total_cost = 0.0
        total_penalty = 0.0
        
        for var in problem.variables:
            tonnes = result.x[var.var_index]
            if tonnes > 0.01:  # Tolerance for numerical precision
                parcel = problem.parcels[var.parcel_index]
                arc = problem.arcs[var.arc_index]
                
                cost = (arc.cost_per_tonne or 0.0) * tonnes
                benefit = (arc.benefit_per_tonne or 0.0) * tonnes
                penalty = self._calculate_quality_penalty(parcel, arc) * tonnes / parcel.quantity_tonnes
                
                allocations.append({
                    'parcel_id': var.parcel_id,
                    'arc_id': var.arc_id,
                    'from_node_id': var.from_node_id,
                    'to_node_id': var.to_node_id,
                    'tonnes': tonnes,
                    'quality_vector': parcel.quality_vector,
                    'cost': cost,
                    'benefit': benefit,
                    'penalty': penalty
                })
                
                # Create FlowResult
                flow_result = FlowResult(
                    flow_result_id=str(uuid.uuid4()),
                    schedule_version_id=schedule_version_id,
                    period_id=period_id,
                    from_node_id=var.from_node_id,
                    to_node_id=var.to_node_id,
                    arc_id=var.arc_id,
                    material_type_id=parcel.material_type_id,
                    tonnes=tonnes,
                    quality_vector=parcel.quality_vector,
                    cost=cost,
                    benefit=benefit,
                    penalty_cost=penalty
                )
                flow_results.append(flow_result)
                
                total_cost += cost
                total_penalty += penalty
        
        # Identify binding constraints
        binding_constraints = []
        if hasattr(result, 'slack') and result.slack is not None:
            for i, slack in enumerate(result.slack):
                if abs(slack) < 0.01 and i < len(problem.constraint_names):
                    binding_constraints.append(problem.constraint_names[i])
        
        # Generate explanations
        explanations = self._generate_explanations(
            allocations, binding_constraints, period_id, schedule_version_id
        )
        
        return AllocationResult(
            success=True,
            allocations=allocations,
            total_cost=total_cost,
            total_penalty=total_penalty,
            binding_constraints=binding_constraints,
            solver_message="Optimal solution found",
            iterations=getattr(result, 'nit', 0),
            flow_results=flow_results,
            explanations=explanations
        )
    
    def _generate_explanations(
        self,
        allocations: List[Dict],
        binding_constraints: List[str],
        period_id: str,
        schedule_version_id: str
    ) -> List[DecisionExplanation]:
        """Generate decision explanations for the allocation."""
        explanations = []
        
        # Group by destination
        dest_allocations = {}
        for alloc in allocations:
            dest = alloc['to_node_id']
            if dest not in dest_allocations:
                dest_allocations[dest] = []
            dest_allocations[dest].append(alloc)
        
        for dest_id, allocs in dest_allocations.items():
            total_tonnes = sum(a['tonnes'] for a in allocs)
            total_penalty = sum(a['penalty'] for a in allocs)
            
            # Get node name
            node = self.db.query(FlowNode)\
                .filter(FlowNode.node_id == dest_id)\
                .first()
            dest_name = node.name if node else dest_id[:8]
            
            summary = f"LP allocated {total_tonnes:.0f}t to {dest_name}"
            if total_penalty > 0:
                summary += f" (penalty: ${total_penalty:.0f})"
            
            # Note any binding constraints affecting this destination
            relevant_constraints = [c for c in binding_constraints if dest_id[:8] in c]
            if relevant_constraints:
                summary += f" [Constrained by: {', '.join(relevant_constraints)}]"
            
            explanation = DecisionExplanation(
                explanation_id=str(uuid.uuid4()),
                schedule_version_id=schedule_version_id,
                period_id=period_id,
                decision_type="LP_Routing",
                related_node_id=dest_id,
                summary_text=summary,
                binding_constraints=relevant_constraints,
                penalty_breakdown=[{
                    'parcel_id': a['parcel_id'],
                    'tonnes': a['tonnes'],
                    'penalty': a['penalty']
                } for a in allocs],
                total_penalty=total_penalty
            )
            explanations.append(explanation)
        
        return explanations


# Create singleton instance
def create_lp_allocator(db: Session) -> LPMaterialAllocator:
    """Factory function to create LP allocator with database session."""
    return LPMaterialAllocator(db)
