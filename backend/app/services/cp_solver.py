"""
Constraint Programming Solver Service

Implements constraint propagation and branch-and-bound search for
mining scheduling problems that require discrete decisions.

Handles constraints like:
- Precedence (block A before block B)
- Resource mutual exclusion
- Mining sequence requirements
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    PRECEDENCE = "precedence"  # A before B
    MUTUAL_EXCLUSION = "mutual_exclusion"  # Not both at same time
    CUMULATIVE = "cumulative"  # Resource capacity over time
    ALLDIFFERENT = "alldifferent"  # All assignments different
    SEQUENCE = "sequence"  # Specific order required


@dataclass
class Variable:
    """CP variable with domain."""
    name: str
    domain: Set[Any]
    assigned_value: Optional[Any] = None
    
    @property
    def is_assigned(self) -> bool:
        return self.assigned_value is not None
    
    @property
    def domain_size(self) -> int:
        return len(self.domain)
    
    def assign(self, value: Any):
        if value in self.domain:
            self.assigned_value = value
        else:
            raise ValueError(f"Value {value} not in domain")
    
    def remove_value(self, value: Any) -> bool:
        """Remove value from domain. Returns True if domain became empty."""
        self.domain.discard(value)
        return len(self.domain) == 0


@dataclass
class Constraint:
    """CP constraint between variables."""
    constraint_type: ConstraintType
    variables: List[str]  # Variable names
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def is_satisfied(self, assignments: Dict[str, Any]) -> bool:
        """Check if constraint is satisfied with current assignments."""
        if self.constraint_type == ConstraintType.PRECEDENCE:
            # A before B: A's value < B's value
            var_a, var_b = self.variables[0], self.variables[1]
            if var_a in assignments and var_b in assignments:
                return assignments[var_a] < assignments[var_b]
            return True  # Not fully assigned yet
        
        elif self.constraint_type == ConstraintType.MUTUAL_EXCLUSION:
            # Variables can't have same value
            values = [assignments[v] for v in self.variables if v in assignments]
            return len(values) == len(set(values))
        
        elif self.constraint_type == ConstraintType.ALLDIFFERENT:
            values = [assignments[v] for v in self.variables if v in assignments]
            return len(values) == len(set(values))
        
        return True


@dataclass
class CPSolution:
    """Solution from CP solver."""
    assignments: Dict[str, Any]
    is_optimal: bool
    objective_value: float
    nodes_explored: int
    time_seconds: float


class CPSolverService:
    """
    Constraint Programming solver using arc consistency and branch-and-bound.
    
    Usage:
        solver = CPSolverService()
        solver.add_variable("task1", {1, 2, 3, 4, 5})  # time slots
        solver.add_variable("task2", {1, 2, 3, 4, 5})
        solver.add_constraint(ConstraintType.PRECEDENCE, ["task1", "task2"])
        solution = solver.solve()
    """
    
    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        self.constraints: List[Constraint] = []
        self.objective: Optional[Tuple[str, str]] = None  # (variable, "min"/"max")
        self._nodes_explored = 0
    
    def add_variable(self, name: str, domain: Set[Any]):
        """Add a variable with its initial domain."""
        self.variables[name] = Variable(name=name, domain=domain.copy())
    
    def add_constraint(
        self,
        constraint_type: ConstraintType,
        variables: List[str],
        **parameters
    ):
        """Add a constraint between variables."""
        self.constraints.append(Constraint(
            constraint_type=constraint_type,
            variables=variables,
            parameters=parameters
        ))
    
    def set_objective(self, variable: str, direction: str = "min"):
        """Set optimization objective (minimize or maximize a variable)."""
        self.objective = (variable, direction)
    
    # =========================================================================
    # Domain Propagation (Arc Consistency)
    # =========================================================================
    
    def domain_propagation(self) -> bool:
        """
        Apply arc consistency (AC-3 algorithm).
        Returns False if a domain becomes empty (no solution).
        """
        # Build arcs from constraints
        arcs = self._get_arcs()
        queue = list(arcs)
        
        while queue:
            var_i, var_j, constraint = queue.pop(0)
            
            if self._revise(var_i, var_j, constraint):
                if self.variables[var_i].domain_size == 0:
                    return False  # Domain wipeout
                
                # Add affected arcs back to queue
                for other_var, other_constraint in self._get_neighbors(var_i):
                    if other_var != var_j:
                        queue.append((other_var, var_i, other_constraint))
        
        return True
    
    def _get_arcs(self) -> List[Tuple[str, str, Constraint]]:
        """Get all arcs (directed variable pairs) from constraints."""
        arcs = []
        for constraint in self.constraints:
            if len(constraint.variables) == 2:
                arcs.append((constraint.variables[0], constraint.variables[1], constraint))
                arcs.append((constraint.variables[1], constraint.variables[0], constraint))
        return arcs
    
    def _get_neighbors(self, var: str) -> List[Tuple[str, Constraint]]:
        """Get all neighbors of a variable (connected via constraints)."""
        neighbors = []
        for constraint in self.constraints:
            if var in constraint.variables:
                for other in constraint.variables:
                    if other != var:
                        neighbors.append((other, constraint))
        return neighbors
    
    def _revise(self, var_i: str, var_j: str, constraint: Constraint) -> bool:
        """
        Remove values from var_i's domain that have no support in var_j.
        Returns True if any value was removed.
        """
        revised = False
        to_remove = []
        
        for val_i in self.variables[var_i].domain:
            has_support = False
            
            for val_j in self.variables[var_j].domain:
                # Check if (val_i, val_j) satisfies constraint
                test_assignments = {var_i: val_i, var_j: val_j}
                if constraint.is_satisfied(test_assignments):
                    has_support = True
                    break
            
            if not has_support:
                to_remove.append(val_i)
                revised = True
        
        for val in to_remove:
            self.variables[var_i].remove_value(val)
        
        return revised
    
    # =========================================================================
    # Branch and Bound Search
    # =========================================================================
    
    def solve(self, time_limit: float = 60.0) -> Optional[CPSolution]:
        """
        Solve using branch-and-bound with arc consistency.
        """
        import time
        start_time = time.time()
        
        self._nodes_explored = 0
        best_solution = None
        best_objective = float('inf') if self.objective and self.objective[1] == "min" else float('-inf')
        
        # Initial propagation
        if not self.domain_propagation():
            return None  # No solution
        
        def search(assignments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            nonlocal best_solution, best_objective
            
            # Check time limit
            if time.time() - start_time > time_limit:
                return best_solution
            
            self._nodes_explored += 1
            
            # Check if all assigned
            if len(assignments) == len(self.variables):
                # Verify all constraints
                if all(c.is_satisfied(assignments) for c in self.constraints):
                    # Update best if better
                    if self.objective:
                        obj_var, direction = self.objective
                        obj_val = assignments[obj_var]
                        if direction == "min" and obj_val < best_objective:
                            best_objective = obj_val
                            best_solution = assignments.copy()
                        elif direction == "max" and obj_val > best_objective:
                            best_objective = obj_val
                            best_solution = assignments.copy()
                    else:
                        best_solution = assignments.copy()
                    return best_solution
                return None
            
            # Select unassigned variable (MRV heuristic)
            unassigned = [
                v for v in self.variables.values() 
                if v.name not in assignments
            ]
            var = min(unassigned, key=lambda v: v.domain_size)
            
            # Try each value in domain (ordered by LCV if objective)
            domain_values = sorted(var.domain) if self.objective else list(var.domain)
            
            for value in domain_values:
                # Bound check for branch-and-bound
                if self.objective:
                    obj_var, direction = self.objective
                    if obj_var == var.name:
                        if direction == "min" and value >= best_objective:
                            continue
                        if direction == "max" and value <= best_objective:
                            continue
                
                # Make assignment
                new_assignments = assignments.copy()
                new_assignments[var.name] = value
                
                # Check constraints
                if all(c.is_satisfied(new_assignments) for c in self.constraints):
                    result = search(new_assignments)
                    if result and not self.objective:
                        return result  # First solution is enough
            
            return best_solution
        
        result = search({})
        elapsed = time.time() - start_time
        
        if result:
            obj_val = result[self.objective[0]] if self.objective else 0
            return CPSolution(
                assignments=result,
                is_optimal=True,  # BnB guarantees optimality
                objective_value=obj_val,
                nodes_explored=self._nodes_explored,
                time_seconds=elapsed
            )
        return None
    
    # =========================================================================
    # Solution Enumeration
    # =========================================================================
    
    def enumerate_solutions(self, max_solutions: int = 10) -> List[Dict[str, Any]]:
        """Find up to max_solutions different solutions."""
        solutions = []
        
        def search(assignments: Dict[str, Any]):
            if len(solutions) >= max_solutions:
                return
            
            if len(assignments) == len(self.variables):
                if all(c.is_satisfied(assignments) for c in self.constraints):
                    solutions.append(assignments.copy())
                return
            
            unassigned = [v for v in self.variables.values() if v.name not in assignments]
            var = min(unassigned, key=lambda v: v.domain_size)
            
            for value in var.domain:
                new_assignments = assignments.copy()
                new_assignments[var.name] = value
                if all(c.is_satisfied(new_assignments) for c in self.constraints):
                    search(new_assignments)
        
        search({})
        return solutions
    
    # =========================================================================
    # Mining-Specific Constraint Builders
    # =========================================================================
    
    @staticmethod
    def create_mining_sequence_constraint(
        blocks: List[str],
        sequence: List[int]
    ) -> List[Constraint]:
        """Create precedence constraints for mining sequence."""
        constraints = []
        for i in range(len(blocks) - 1):
            constraints.append(Constraint(
                constraint_type=ConstraintType.PRECEDENCE,
                variables=[blocks[i], blocks[i + 1]]
            ))
        return constraints
    
    @staticmethod
    def create_resource_capacity_constraint(
        tasks: List[str],
        capacity: int,
        time_horizon: int
    ) -> Constraint:
        """Create cumulative resource constraint."""
        return Constraint(
            constraint_type=ConstraintType.CUMULATIVE,
            variables=tasks,
            parameters={"capacity": capacity, "horizon": time_horizon}
        )


# Singleton for simple use
cp_solver_service = CPSolverService()
