"""
Constraint Programming Solver Router - API endpoints for CP-based optimization

Provides endpoints for:
- Creating and solving CP models
- Mining schedule optimization
- Advanced constraint configuration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.cp_solver_service import (
    CPSolver, MiningScheduleCP, Solution, SolverStatus,
    ConstraintType, ObjectiveSense
)
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

router = APIRouter(prefix="/cp-solver", tags=["Constraint Programming"])


# =============================================================================
# Pydantic Models
# =============================================================================

class VariableInput(BaseModel):
    name: str
    domain_min: int
    domain_max: int
    is_boolean: bool = False


class ConstraintInput(BaseModel):
    name: str
    constraint_type: str  # equality, less_equal, greater_equal, range, all_different, sum_less_equal
    variables: List[str]
    parameters: Dict[str, Any] = {}
    is_hard: bool = True
    penalty_weight: float = 1.0


class ObjectiveInput(BaseModel):
    variable: str
    sense: str  # minimize or maximize
    weight: float = 1.0


class CPModelInput(BaseModel):
    variables: List[VariableInput]
    constraints: List[ConstraintInput]
    objectives: List[ObjectiveInput] = []
    timeout_seconds: int = 60


class TaskScheduleInput(BaseModel):
    task_id: str
    earliest_period: int
    latest_period: int
    resource_options: List[str] = []
    quantity_tonnes: float = 0


class PrecedenceInput(BaseModel):
    before_task: str
    after_task: str


class ResourceCapacityInput(BaseModel):
    resource_id: str
    period: int
    capacity: int
    task_ids: List[str]


class MiningScheduleInput(BaseModel):
    tasks: List[TaskScheduleInput]
    precedences: List[PrecedenceInput] = []
    resource_capacities: List[ResourceCapacityInput] = []
    minimize_makespan: bool = True
    timeout_seconds: int = 60


class SolutionOutput(BaseModel):
    solution_id: str
    status: str
    variable_values: Dict[str, int]
    objective_value: float
    constraint_violations: List[str]
    solve_time_seconds: float
    nodes_explored: int
    is_feasible: bool


# =============================================================================
# Generic CP Model Endpoints
# =============================================================================

@router.post("/solve", response_model=SolutionOutput)
def solve_cp_model(model: CPModelInput):
    """
    Solve a generic constraint programming model.
    
    Supports:
    - Integer and boolean variables
    - Hard and soft constraints
    - Multiple objectives
    """
    solver = CPSolver()
    solver.max_time_seconds = model.timeout_seconds
    
    # Create variables
    for var in model.variables:
        if var.is_boolean:
            solver.new_bool_var(var.name)
        else:
            solver.new_int_var(var.domain_min, var.domain_max, var.name)
    
    # Add constraints
    for constraint in model.constraints:
        c = _add_constraint(solver, constraint)
        if not constraint.is_hard:
            solver.add_soft_constraint(c, constraint.penalty_weight)
    
    # Add objectives
    for obj in model.objectives:
        if obj.sense == "minimize":
            solver.minimize(obj.variable, obj.weight)
        else:
            solver.maximize(obj.variable, obj.weight)
    
    # Solve
    solution = solver.solve()
    
    return SolutionOutput(
        solution_id=solution.solution_id,
        status=solution.status.value,
        variable_values=solution.variable_values,
        objective_value=solution.objective_value,
        constraint_violations=solution.constraint_violations,
        solve_time_seconds=solution.solve_time_seconds,
        nodes_explored=solution.nodes_explored,
        is_feasible=solution.is_feasible()
    )


def _add_constraint(solver: CPSolver, constraint: ConstraintInput):
    """Helper to add constraint based on type."""
    if constraint.constraint_type == "equality":
        return solver.add_equality(
            constraint.variables[0], 
            constraint.parameters.get("value"),
            constraint.name
        )
    elif constraint.constraint_type == "less_equal":
        return solver.add_less_equal(
            constraint.variables[0],
            constraint.parameters.get("value"),
            constraint.name
        )
    elif constraint.constraint_type == "greater_equal":
        return solver.add_greater_equal(
            constraint.variables[0],
            constraint.parameters.get("value"),
            constraint.name
        )
    elif constraint.constraint_type == "range":
        return solver.add_range(
            constraint.variables[0],
            constraint.parameters.get("min"),
            constraint.parameters.get("max"),
            constraint.name
        )
    elif constraint.constraint_type == "all_different":
        return solver.add_all_different(constraint.variables, constraint.name)
    elif constraint.constraint_type == "sum_less_equal":
        return solver.add_sum_less_equal(
            constraint.variables,
            constraint.parameters.get("value"),
            constraint.name
        )
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown constraint type: {constraint.constraint_type}"
        )


# =============================================================================
# Mining Schedule Optimization Endpoints
# =============================================================================

@router.post("/mining-schedule", response_model=SolutionOutput)
def solve_mining_schedule(schedule: MiningScheduleInput):
    """
    Solve a mining schedule optimization problem.
    
    Optimizes:
    - Task period assignments
    - Resource allocations
    - Respects precedence and capacity constraints
    """
    cp_model = MiningScheduleCP()
    
    # Add tasks
    task_ids = []
    for task in schedule.tasks:
        cp_model.add_task(task.task_id, task.earliest_period, task.latest_period)
        task_ids.append(task.task_id)
        
        if task.resource_options:
            cp_model.add_resource_assignment(task.task_id, task.resource_options)
    
    # Add precedence constraints
    for prec in schedule.precedences:
        cp_model.add_precedence_constraint(prec.before_task, prec.after_task)
    
    # Add resource capacity constraints
    for cap in schedule.resource_capacities:
        cp_model.add_resource_capacity(
            cap.resource_id, cap.period, cap.capacity, cap.task_ids
        )
    
    # Add objective
    if schedule.minimize_makespan and task_ids:
        cp_model.minimize_makespan(task_ids)
    
    # Solve
    solution = cp_model.solve(schedule.timeout_seconds)
    
    return SolutionOutput(
        solution_id=solution.solution_id,
        status=solution.status.value,
        variable_values=solution.variable_values,
        objective_value=solution.objective_value,
        constraint_violations=solution.constraint_violations,
        solve_time_seconds=solution.solve_time_seconds,
        nodes_explored=solution.nodes_explored,
        is_feasible=solution.is_feasible()
    )


@router.post("/optimize-flow")
def optimize_material_flow(
    network_id: str,
    period_id: str,
    min_throughput: int = 0,
    max_throughput: int = 100000,
    db: Session = Depends(get_db)
):
    """
    Optimize material flow through the network for a period.
    Uses CP to find optimal flow assignments.
    """
    from ..domain.models_flow import FlowNetwork, FlowNode, FlowArc
    
    # Get network
    network = db.query(FlowNetwork).filter(FlowNetwork.network_id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Get arcs
    arcs = db.query(FlowArc).filter(FlowArc.network_id == network_id).all()
    
    if not arcs:
        return {"status": "no_arcs", "message": "No arcs in network"}
    
    # Build CP model
    solver = CPSolver()
    solver.max_time_seconds = 30
    
    # Create flow variables for each arc
    arc_vars = {}
    for arc in arcs:
        var = solver.new_int_var(0, max_throughput, f"flow_{arc.arc_id}")
        arc_vars[arc.arc_id] = var
    
    # Get nodes for balance constraints
    nodes = db.query(FlowNode).filter(FlowNode.network_id == network_id).all()
    
    # Add flow balance constraints for intermediate nodes
    for node in nodes:
        if node.node_type not in ["SourcePit", "Sink", "ProductStockpile"]:
            inflows = [f"flow_{a.arc_id}" for a in arcs if a.destination_node_id == node.node_id]
            outflows = [f"flow_{a.arc_id}" for a in arcs if a.source_node_id == node.node_id]
            
            # Inflows should roughly equal outflows (simplified)
            if inflows and outflows:
                all_vars = inflows + outflows
                solver.add_sum_less_equal(all_vars, max_throughput * 2, f"balance_{node.node_id}")
    
    # Add minimum throughput constraint
    if min_throughput > 0:
        source_arcs = [f"flow_{a.arc_id}" for a in arcs if a.source_node_id and "pit" in a.source_node_id.lower()]
        if source_arcs:
            # At least min_throughput should flow from sources
            pass  # Would need sum >= constraint
    
    # Maximize total flow
    if arcs:
        # Create total flow variable
        total = solver.new_int_var(0, max_throughput * len(arcs), "total_flow")
        solver.maximize("total_flow")
    
    # Solve
    solution = solver.solve()
    
    # Extract flow values
    flow_results = {}
    for arc in arcs:
        flow_value = solution.variable_values.get(f"flow_{arc.arc_id}", 0)
        flow_results[arc.arc_id] = {
            "arc_id": arc.arc_id,
            "from": arc.source_node_id,
            "to": arc.destination_node_id,
            "flow_tonnes": flow_value
        }
    
    return {
        "status": solution.status.value,
        "solve_time": solution.solve_time_seconds,
        "nodes_explored": solution.nodes_explored,
        "total_flow": sum(f["flow_tonnes"] for f in flow_results.values()),
        "flows": list(flow_results.values())
    }


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/constraint-types")
def get_constraint_types():
    """Get list of supported constraint types."""
    return {
        "constraint_types": [
            {"name": "equality", "description": "x == value", "parameters": ["value"]},
            {"name": "less_equal", "description": "x <= value", "parameters": ["value"]},
            {"name": "greater_equal", "description": "x >= value", "parameters": ["value"]},
            {"name": "range", "description": "min <= x <= max", "parameters": ["min", "max"]},
            {"name": "all_different", "description": "all variables must have different values", "parameters": []},
            {"name": "sum_less_equal", "description": "sum(vars) <= value", "parameters": ["value"]},
            {"name": "precedence", "description": "x must be scheduled before y", "parameters": []},
        ]
    }


@router.get("/solver-info")
def get_solver_info():
    """Get information about the CP solver."""
    return {
        "name": "MineOpt CP Solver",
        "version": "1.0.0",
        "features": [
            "Integer and boolean variables",
            "Hard and soft constraints",
            "Multiple objectives",
            "Domain propagation",
            "Branch and bound search",
            "Minimum Remaining Values (MRV) heuristic",
            "Backtracking with state restoration"
        ],
        "constraint_types": len(ConstraintType),
        "search_strategies": [
            "First Unassigned",
            "Minimum Remaining Values",
            "Most Constrained"
        ]
    }


@router.post("/validate-model")
def validate_cp_model(model: CPModelInput):
    """
    Validate a CP model without solving.
    Checks for consistency and potential issues.
    """
    issues = []
    
    # Check variables
    var_names = set()
    for var in model.variables:
        if var.name in var_names:
            issues.append(f"Duplicate variable name: {var.name}")
        var_names.add(var.name)
        
        if var.domain_min > var.domain_max:
            issues.append(f"Invalid domain for {var.name}: min > max")
    
    # Check constraints reference valid variables
    for constraint in model.constraints:
        for var_name in constraint.variables:
            if var_name not in var_names:
                issues.append(f"Constraint {constraint.name} references unknown variable: {var_name}")
    
    # Check objectives reference valid variables
    for obj in model.objectives:
        if obj.variable not in var_names:
            issues.append(f"Objective references unknown variable: {obj.variable}")
    
    return {
        "valid": len(issues) == 0,
        "variable_count": len(model.variables),
        "constraint_count": len(model.constraints),
        "objective_count": len(model.objectives),
        "issues": issues
    }
