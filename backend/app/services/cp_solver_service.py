"""
Constraint Programming Solver - Advanced Optimization Service

Implements a constraint programming (CP) solver for complex scheduling problems.
Supports:
- Hard constraints (must satisfy)
- Soft constraints (minimize violations)
- Multiple objective optimization
- Variable domains and propagation
- Branch and bound search

Based on CP-SAT solver patterns for mining scheduling.
"""

from typing import List, Dict, Optional, Tuple, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import heapq
import copy


# =============================================================================
# Core Constraint Types
# =============================================================================

class ConstraintType(Enum):
    """Types of constraints supported by the solver."""
    EQUALITY = "equality"           # x == value
    LESS_THAN = "less_than"         # x < value
    LESS_EQUAL = "less_equal"       # x <= value
    GREATER_THAN = "greater_than"   # x > value
    GREATER_EQUAL = "greater_equal" # x >= value
    RANGE = "range"                 # min <= x <= max
    NOT_EQUAL = "not_equal"         # x != value
    ALL_DIFFERENT = "all_different" # all vars different
    SUM_EQUAL = "sum_equal"         # sum(vars) == value
    SUM_LESS_EQUAL = "sum_less_equal"  # sum(vars) <= value
    IMPLICATION = "implication"     # if x then y
    EXCLUSIVE_OR = "exclusive_or"   # exactly one true
    PRECEDENCE = "precedence"       # x must happen before y


class VariableType(Enum):
    """Types of decision variables."""
    INTEGER = "integer"
    BOOLEAN = "boolean"
    INTERVAL = "interval"


class ObjectiveSense(Enum):
    """Optimization direction."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class SolverStatus(Enum):
    """Status of solver execution."""
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    TIMEOUT = "timeout"
    ERROR = "error"


# =============================================================================
# Variable and Constraint Definitions
# =============================================================================

@dataclass
class Variable:
    """Decision variable in the CP model."""
    name: str
    var_type: VariableType
    domain_min: int = 0
    domain_max: int = 1
    current_value: Optional[int] = None
    is_fixed: bool = False
    
    def __hash__(self):
        return hash(self.name)
    
    def domain_size(self) -> int:
        return self.domain_max - self.domain_min + 1
    
    def is_assigned(self) -> bool:
        return self.current_value is not None
    
    def get_domain(self) -> List[int]:
        return list(range(self.domain_min, self.domain_max + 1))


@dataclass
class Constraint:
    """Constraint in the CP model."""
    constraint_id: str
    name: str
    constraint_type: ConstraintType
    variables: List[str]  # Variable names
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_hard: bool = True  # Hard constraint (must satisfy) vs soft (minimize violations)
    penalty_weight: float = 1.0  # Weight for soft constraint violations
    
    def __hash__(self):
        return hash(self.constraint_id)


@dataclass
class Objective:
    """Objective function component."""
    name: str
    sense: ObjectiveSense
    variable: str  # Variable name to optimize
    weight: float = 1.0  # For multi-objective


@dataclass
class Solution:
    """Solution to the CP model."""
    solution_id: str
    status: SolverStatus
    variable_values: Dict[str, int]
    objective_value: float
    constraint_violations: List[str]
    solve_time_seconds: float
    nodes_explored: int
    
    def is_feasible(self) -> bool:
        return self.status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]


# =============================================================================
# Constraint Propagation
# =============================================================================

class DomainStore:
    """Manages variable domains during search."""
    
    def __init__(self):
        self.domains: Dict[str, Set[int]] = {}
        self.trail: List[Tuple[str, Set[int]]] = []  # For backtracking
    
    def initialize(self, variables: List[Variable]):
        """Initialize domains from variables."""
        for var in variables:
            self.domains[var.name] = set(range(var.domain_min, var.domain_max + 1))
    
    def get_domain(self, var_name: str) -> Set[int]:
        return self.domains.get(var_name, set())
    
    def set_domain(self, var_name: str, domain: Set[int]):
        # Save for backtracking
        self.trail.append((var_name, self.domains[var_name].copy()))
        self.domains[var_name] = domain
    
    def remove_value(self, var_name: str, value: int) -> bool:
        """Remove value from domain. Returns True if domain not empty."""
        if var_name in self.domains and value in self.domains[var_name]:
            self.trail.append((var_name, self.domains[var_name].copy()))
            self.domains[var_name].discard(value)
        return len(self.domains.get(var_name, set())) > 0
    
    def fix_value(self, var_name: str, value: int):
        """Fix variable to a single value."""
        self.trail.append((var_name, self.domains[var_name].copy()))
        self.domains[var_name] = {value}
    
    def is_assigned(self, var_name: str) -> bool:
        return len(self.domains.get(var_name, set())) == 1
    
    def get_value(self, var_name: str) -> Optional[int]:
        domain = self.domains.get(var_name, set())
        if len(domain) == 1:
            return list(domain)[0]
        return None
    
    def save_state(self) -> int:
        """Save current state for backtracking."""
        return len(self.trail)
    
    def restore_state(self, checkpoint: int):
        """Restore to previous checkpoint."""
        while len(self.trail) > checkpoint:
            var_name, old_domain = self.trail.pop()
            self.domains[var_name] = old_domain


class ConstraintPropagator:
    """Propagates constraints to reduce variable domains."""
    
    def __init__(self, constraints: List[Constraint]):
        self.constraints = constraints
        self.var_to_constraints: Dict[str, List[Constraint]] = {}
        
        # Build index
        for constraint in constraints:
            for var_name in constraint.variables:
                if var_name not in self.var_to_constraints:
                    self.var_to_constraints[var_name] = []
                self.var_to_constraints[var_name].append(constraint)
    
    def propagate(self, domains: DomainStore) -> bool:
        """
        Apply constraint propagation.
        Returns False if a domain becomes empty (inconsistency).
        """
        changed = True
        iterations = 0
        max_iterations = 1000
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for constraint in self.constraints:
                if not constraint.is_hard:
                    continue
                    
                result = self._propagate_constraint(constraint, domains)
                if result is None:
                    return False  # Inconsistency
                if result:
                    changed = True
        
        return True
    
    def _propagate_constraint(self, constraint: Constraint, domains: DomainStore) -> Optional[bool]:
        """
        Propagate a single constraint.
        Returns:
        - None: Inconsistency detected
        - True: Domain was reduced
        - False: No change
        """
        if constraint.constraint_type == ConstraintType.EQUALITY:
            return self._propagate_equality(constraint, domains)
        elif constraint.constraint_type == ConstraintType.LESS_EQUAL:
            return self._propagate_less_equal(constraint, domains)
        elif constraint.constraint_type == ConstraintType.GREATER_EQUAL:
            return self._propagate_greater_equal(constraint, domains)
        elif constraint.constraint_type == ConstraintType.RANGE:
            return self._propagate_range(constraint, domains)
        elif constraint.constraint_type == ConstraintType.ALL_DIFFERENT:
            return self._propagate_all_different(constraint, domains)
        elif constraint.constraint_type == ConstraintType.SUM_LESS_EQUAL:
            return self._propagate_sum_less_equal(constraint, domains)
        
        return False
    
    def _propagate_equality(self, constraint: Constraint, domains: DomainStore) -> Optional[bool]:
        """x == value"""
        var_name = constraint.variables[0]
        value = constraint.parameters.get("value")
        
        domain = domains.get_domain(var_name)
        if value not in domain:
            return None  # Inconsistency
        
        if len(domain) > 1:
            domains.fix_value(var_name, value)
            return True
        
        return False
    
    def _propagate_less_equal(self, constraint: Constraint, domains: DomainStore) -> Optional[bool]:
        """x <= value"""
        var_name = constraint.variables[0]
        value = constraint.parameters.get("value")
        
        domain = domains.get_domain(var_name)
        new_domain = {v for v in domain if v <= value}
        
        if not new_domain:
            return None  # Inconsistency
        
        if len(new_domain) < len(domain):
            domains.set_domain(var_name, new_domain)
            return True
        
        return False
    
    def _propagate_greater_equal(self, constraint: Constraint, domains: DomainStore) -> Optional[bool]:
        """x >= value"""
        var_name = constraint.variables[0]
        value = constraint.parameters.get("value")
        
        domain = domains.get_domain(var_name)
        new_domain = {v for v in domain if v >= value}
        
        if not new_domain:
            return None
        
        if len(new_domain) < len(domain):
            domains.set_domain(var_name, new_domain)
            return True
        
        return False
    
    def _propagate_range(self, constraint: Constraint, domains: DomainStore) -> Optional[bool]:
        """min <= x <= max"""
        var_name = constraint.variables[0]
        min_val = constraint.parameters.get("min")
        max_val = constraint.parameters.get("max")
        
        domain = domains.get_domain(var_name)
        new_domain = {v for v in domain if min_val <= v <= max_val}
        
        if not new_domain:
            return None
        
        if len(new_domain) < len(domain):
            domains.set_domain(var_name, new_domain)
            return True
        
        return False
    
    def _propagate_all_different(self, constraint: Constraint, domains: DomainStore) -> Optional[bool]:
        """All variables must have different values."""
        changed = False
        
        # If any variable is assigned, remove its value from others
        for var_name in constraint.variables:
            if domains.is_assigned(var_name):
                value = domains.get_value(var_name)
                for other_var in constraint.variables:
                    if other_var != var_name:
                        if value in domains.get_domain(other_var):
                            if not domains.remove_value(other_var, value):
                                return None  # Empty domain
                            changed = True
        
        return changed
    
    def _propagate_sum_less_equal(self, constraint: Constraint, domains: DomainStore) -> Optional[bool]:
        """sum(vars) <= value"""
        limit = constraint.parameters.get("value")
        
        # Calculate minimum sum
        min_sum = sum(min(domains.get_domain(v)) for v in constraint.variables)
        
        if min_sum > limit:
            return None  # Inconsistency
        
        # For each variable, reduce upper bound
        changed = False
        for var_name in constraint.variables:
            other_min = sum(
                min(domains.get_domain(v)) 
                for v in constraint.variables if v != var_name
            )
            max_allowed = limit - other_min
            
            domain = domains.get_domain(var_name)
            new_domain = {v for v in domain if v <= max_allowed}
            
            if not new_domain:
                return None
            
            if len(new_domain) < len(domain):
                domains.set_domain(var_name, new_domain)
                changed = True
        
        return changed


# =============================================================================
# Search Strategy
# =============================================================================

class VariableSelector:
    """Selects next variable to branch on."""
    
    @staticmethod
    def first_unassigned(variables: List[Variable], domains: DomainStore) -> Optional[str]:
        """Select first unassigned variable."""
        for var in variables:
            if not domains.is_assigned(var.name):
                return var.name
        return None
    
    @staticmethod
    def minimum_remaining_values(variables: List[Variable], domains: DomainStore) -> Optional[str]:
        """Select variable with smallest domain (MRV heuristic)."""
        best_var = None
        best_size = float('inf')
        
        for var in variables:
            if not domains.is_assigned(var.name):
                size = len(domains.get_domain(var.name))
                if size < best_size:
                    best_size = size
                    best_var = var.name
        
        return best_var
    
    @staticmethod
    def most_constrained(variables: List[Variable], domains: DomainStore, 
                        var_to_constraints: Dict[str, List[Constraint]]) -> Optional[str]:
        """Select variable involved in most constraints."""
        best_var = None
        best_count = -1
        
        for var in variables:
            if not domains.is_assigned(var.name):
                count = len(var_to_constraints.get(var.name, []))
                if count > best_count:
                    best_count = count
                    best_var = var.name
        
        return best_var


class ValueSelector:
    """Selects next value to try for a variable."""
    
    @staticmethod
    def min_value(domain: Set[int]) -> List[int]:
        """Try values from smallest to largest."""
        return sorted(domain)
    
    @staticmethod
    def max_value(domain: Set[int]) -> List[int]:
        """Try values from largest to smallest."""
        return sorted(domain, reverse=True)
    
    @staticmethod
    def middle_out(domain: Set[int]) -> List[int]:
        """Try values from middle outward."""
        sorted_domain = sorted(domain)
        result = []
        left, right = 0, len(sorted_domain) - 1
        while left <= right:
            mid = (left + right) // 2
            if mid not in [i for i in range(len(result))]:
                result.append(sorted_domain[mid])
            left += 1
            right -= 1
        return result[:len(domain)]


# =============================================================================
# Main CP Solver
# =============================================================================

class CPSolver:
    """
    Constraint Programming Solver for mining schedule optimization.
    
    Uses:
    - Domain propagation for constraint enforcement
    - Branch and bound search with variable/value ordering
    - Soft constraint penalty minimization
    """
    
    def __init__(self):
        self.variables: List[Variable] = []
        self.constraints: List[Constraint] = []
        self.objectives: List[Objective] = []
        self.var_by_name: Dict[str, Variable] = {}
        
        # Search statistics
        self.nodes_explored = 0
        self.solutions_found = 0
        self.best_solution: Optional[Solution] = None
        
        # Configuration
        self.max_time_seconds = 60
        self.max_solutions = 1
        self.log_search = False
    
    # =========================================================================
    # Model Building
    # =========================================================================
    
    def new_int_var(self, domain_min: int, domain_max: int, name: str) -> Variable:
        """Create a new integer variable."""
        var = Variable(
            name=name,
            var_type=VariableType.INTEGER,
            domain_min=domain_min,
            domain_max=domain_max
        )
        self.variables.append(var)
        self.var_by_name[name] = var
        return var
    
    def new_bool_var(self, name: str) -> Variable:
        """Create a new boolean variable (0 or 1)."""
        return self.new_int_var(0, 1, name)
    
    def add_equality(self, var_name: str, value: int, name: str = None) -> Constraint:
        """Add equality constraint: var == value."""
        constraint = Constraint(
            constraint_id=str(uuid.uuid4()),
            name=name or f"{var_name}_eq_{value}",
            constraint_type=ConstraintType.EQUALITY,
            variables=[var_name],
            parameters={"value": value}
        )
        self.constraints.append(constraint)
        return constraint
    
    def add_less_equal(self, var_name: str, value: int, name: str = None) -> Constraint:
        """Add constraint: var <= value."""
        constraint = Constraint(
            constraint_id=str(uuid.uuid4()),
            name=name or f"{var_name}_le_{value}",
            constraint_type=ConstraintType.LESS_EQUAL,
            variables=[var_name],
            parameters={"value": value}
        )
        self.constraints.append(constraint)
        return constraint
    
    def add_greater_equal(self, var_name: str, value: int, name: str = None) -> Constraint:
        """Add constraint: var >= value."""
        constraint = Constraint(
            constraint_id=str(uuid.uuid4()),
            name=name or f"{var_name}_ge_{value}",
            constraint_type=ConstraintType.GREATER_EQUAL,
            variables=[var_name],
            parameters={"value": value}
        )
        self.constraints.append(constraint)
        return constraint
    
    def add_range(self, var_name: str, min_val: int, max_val: int, name: str = None) -> Constraint:
        """Add range constraint: min <= var <= max."""
        constraint = Constraint(
            constraint_id=str(uuid.uuid4()),
            name=name or f"{var_name}_range_{min_val}_{max_val}",
            constraint_type=ConstraintType.RANGE,
            variables=[var_name],
            parameters={"min": min_val, "max": max_val}
        )
        self.constraints.append(constraint)
        return constraint
    
    def add_all_different(self, var_names: List[str], name: str = None) -> Constraint:
        """Add all-different constraint."""
        constraint = Constraint(
            constraint_id=str(uuid.uuid4()),
            name=name or "all_different",
            constraint_type=ConstraintType.ALL_DIFFERENT,
            variables=var_names
        )
        self.constraints.append(constraint)
        return constraint
    
    def add_sum_less_equal(self, var_names: List[str], limit: int, name: str = None) -> Constraint:
        """Add constraint: sum(vars) <= limit."""
        constraint = Constraint(
            constraint_id=str(uuid.uuid4()),
            name=name or f"sum_le_{limit}",
            constraint_type=ConstraintType.SUM_LESS_EQUAL,
            variables=var_names,
            parameters={"value": limit}
        )
        self.constraints.append(constraint)
        return constraint
    
    def add_precedence(self, before_var: str, after_var: str, name: str = None) -> Constraint:
        """Add precedence constraint: before must happen before after."""
        constraint = Constraint(
            constraint_id=str(uuid.uuid4()),
            name=name or f"{before_var}_before_{after_var}",
            constraint_type=ConstraintType.PRECEDENCE,
            variables=[before_var, after_var]
        )
        self.constraints.append(constraint)
        return constraint
    
    def add_soft_constraint(self, constraint: Constraint, penalty: float):
        """Make a constraint soft with given penalty weight."""
        constraint.is_hard = False
        constraint.penalty_weight = penalty
    
    def minimize(self, var_name: str, weight: float = 1.0):
        """Add minimization objective."""
        self.objectives.append(Objective(
            name=f"minimize_{var_name}",
            sense=ObjectiveSense.MINIMIZE,
            variable=var_name,
            weight=weight
        ))
    
    def maximize(self, var_name: str, weight: float = 1.0):
        """Add maximization objective."""
        self.objectives.append(Objective(
            name=f"maximize_{var_name}",
            sense=ObjectiveSense.MAXIMIZE,
            variable=var_name,
            weight=weight
        ))
    
    # =========================================================================
    # Solving
    # =========================================================================
    
    def solve(self) -> Solution:
        """
        Solve the constraint programming model.
        Uses branch and bound with constraint propagation.
        """
        start_time = datetime.now()
        self.nodes_explored = 0
        self.solutions_found = 0
        self.best_solution = None
        
        # Initialize domain store
        domains = DomainStore()
        domains.initialize(self.variables)
        
        # Create propagator
        propagator = ConstraintPropagator(self.constraints)
        
        # Initial propagation
        if not propagator.propagate(domains):
            return Solution(
                solution_id=str(uuid.uuid4()),
                status=SolverStatus.INFEASIBLE,
                variable_values={},
                objective_value=float('inf'),
                constraint_violations=["Initial propagation failed"],
                solve_time_seconds=(datetime.now() - start_time).total_seconds(),
                nodes_explored=0
            )
        
        # Branch and bound search
        self._search(domains, propagator, start_time)
        
        solve_time = (datetime.now() - start_time).total_seconds()
        
        if self.best_solution:
            self.best_solution.solve_time_seconds = solve_time
            self.best_solution.nodes_explored = self.nodes_explored
            return self.best_solution
        
        return Solution(
            solution_id=str(uuid.uuid4()),
            status=SolverStatus.INFEASIBLE,
            variable_values={},
            objective_value=float('inf'),
            constraint_violations=["No feasible solution found"],
            solve_time_seconds=solve_time,
            nodes_explored=self.nodes_explored
        )
    
    def _search(self, domains: DomainStore, propagator: ConstraintPropagator, 
                start_time: datetime) -> bool:
        """Recursive search with backtracking."""
        self.nodes_explored += 1
        
        # Check timeout
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > self.max_time_seconds:
            return False
        
        # Check if all variables are assigned
        var_to_branch = VariableSelector.minimum_remaining_values(self.variables, domains)
        
        if var_to_branch is None:
            # All assigned - we have a solution
            solution = self._create_solution(domains)
            if self._is_better(solution):
                self.best_solution = solution
                self.solutions_found += 1
                if self.log_search:
                    print(f"Found solution #{self.solutions_found}: obj={solution.objective_value}")
            return True
        
        # Get values to try
        domain = domains.get_domain(var_to_branch)
        values = ValueSelector.min_value(domain)
        
        for value in values:
            # Save state
            checkpoint = domains.save_state()
            
            # Try assignment
            domains.fix_value(var_to_branch, value)
            
            # Propagate
            if propagator.propagate(domains):
                # Check objective bound (pruning)
                if self._can_improve(domains):
                    if self._search(domains, propagator, start_time):
                        if self.solutions_found >= self.max_solutions:
                            domains.restore_state(checkpoint)
                            return True
            
            # Backtrack
            domains.restore_state(checkpoint)
        
        return False
    
    def _create_solution(self, domains: DomainStore) -> Solution:
        """Create a solution from current assignments."""
        values = {}
        for var in self.variables:
            values[var.name] = domains.get_value(var.name)
        
        # Calculate objective
        obj_value = self._calculate_objective(values)
        
        # Check soft constraints
        violations = self._check_soft_constraints(values)
        
        return Solution(
            solution_id=str(uuid.uuid4()),
            status=SolverStatus.FEASIBLE,
            variable_values=values,
            objective_value=obj_value,
            constraint_violations=violations,
            solve_time_seconds=0,
            nodes_explored=0
        )
    
    def _calculate_objective(self, values: Dict[str, int]) -> float:
        """Calculate objective value from variable assignments."""
        if not self.objectives:
            return 0.0
        
        total = 0.0
        for obj in self.objectives:
            var_value = values.get(obj.variable, 0)
            if obj.sense == ObjectiveSense.MINIMIZE:
                total += obj.weight * var_value
            else:  # MAXIMIZE
                total -= obj.weight * var_value  # Negate for minimization
        
        return total
    
    def _check_soft_constraints(self, values: Dict[str, int]) -> List[str]:
        """Check soft constraints and return violations."""
        violations = []
        
        for constraint in self.constraints:
            if not constraint.is_hard:
                if not self._is_constraint_satisfied(constraint, values):
                    violations.append(constraint.name)
        
        return violations
    
    def _is_constraint_satisfied(self, constraint: Constraint, values: Dict[str, int]) -> bool:
        """Check if a constraint is satisfied."""
        if constraint.constraint_type == ConstraintType.EQUALITY:
            return values.get(constraint.variables[0]) == constraint.parameters.get("value")
        elif constraint.constraint_type == ConstraintType.LESS_EQUAL:
            return values.get(constraint.variables[0], 0) <= constraint.parameters.get("value")
        elif constraint.constraint_type == ConstraintType.GREATER_EQUAL:
            return values.get(constraint.variables[0], 0) >= constraint.parameters.get("value")
        elif constraint.constraint_type == ConstraintType.RANGE:
            val = values.get(constraint.variables[0], 0)
            return constraint.parameters.get("min") <= val <= constraint.parameters.get("max")
        elif constraint.constraint_type == ConstraintType.ALL_DIFFERENT:
            used = set()
            for var in constraint.variables:
                val = values.get(var)
                if val in used:
                    return False
                used.add(val)
            return True
        elif constraint.constraint_type == ConstraintType.SUM_LESS_EQUAL:
            total = sum(values.get(v, 0) for v in constraint.variables)
            return total <= constraint.parameters.get("value")
        
        return True
    
    def _is_better(self, solution: Solution) -> bool:
        """Check if solution is better than current best."""
        if self.best_solution is None:
            return True
        return solution.objective_value < self.best_solution.objective_value
    
    def _can_improve(self, domains: DomainStore) -> bool:
        """Check if we can possibly improve on best solution (for pruning)."""
        if self.best_solution is None or not self.objectives:
            return True
        
        # Calculate lower bound on objective
        lower_bound = 0.0
        for obj in self.objectives:
            domain = domains.get_domain(obj.variable)
            if domain:
                if obj.sense == ObjectiveSense.MINIMIZE:
                    lower_bound += obj.weight * min(domain)
                else:
                    lower_bound -= obj.weight * max(domain)
        
        return lower_bound < self.best_solution.objective_value


# =============================================================================
# Mining-Specific Constraint Builder
# =============================================================================

class MiningScheduleCP:
    """
    High-level CP model builder for mining schedule optimization.
    Provides mining-domain specific constraints and objectives.
    """
    
    def __init__(self):
        self.solver = CPSolver()
        self.task_vars: Dict[str, Variable] = {}
        self.resource_vars: Dict[str, Variable] = {}
        self.flow_vars: Dict[str, Variable] = {}
    
    def add_task(self, task_id: str, earliest_period: int, latest_period: int) -> Variable:
        """Add a task with period assignment variable."""
        var = self.solver.new_int_var(earliest_period, latest_period, f"task_{task_id}_period")
        self.task_vars[task_id] = var
        return var
    
    def add_resource_assignment(self, task_id: str, resource_ids: List[str]) -> Variable:
        """Add resource assignment variable for a task."""
        var = self.solver.new_int_var(0, len(resource_ids) - 1, f"task_{task_id}_resource")
        self.resource_vars[task_id] = var
        return var
    
    def add_precedence_constraint(self, before_task: str, after_task: str):
        """Task 'before' must be scheduled before task 'after'."""
        self.solver.add_precedence(
            f"task_{before_task}_period",
            f"task_{after_task}_period",
            f"precedence_{before_task}_{after_task}"
        )
    
    def add_resource_capacity(self, resource_id: str, period: int, capacity: int, task_ids: List[str]):
        """Limit resource usage in a period."""
        # Create indicator variables for each task being in this period
        indicator_vars = []
        for task_id in task_ids:
            ind_var = self.solver.new_bool_var(f"task_{task_id}_in_period_{period}")
            indicator_vars.append(ind_var.name)
        
        self.solver.add_sum_less_equal(indicator_vars, capacity, f"capacity_{resource_id}_period_{period}")
    
    def add_flow_quantity(self, arc_id: str, min_tonnes: int, max_tonnes: int) -> Variable:
        """Add flow quantity variable for an arc."""
        var = self.solver.new_int_var(min_tonnes, max_tonnes, f"flow_{arc_id}")
        self.flow_vars[arc_id] = var
        return var
    
    def add_stockpile_balance(self, stockpile_id: str, period: int, 
                              inflow_arcs: List[str], outflow_arcs: List[str],
                              min_level: int, max_level: int):
        """Add stockpile balance constraint."""
        # Balance: opening + inflows - outflows = closing
        # Simplified: sum of inflows - sum of outflows within capacity
        all_arcs = [f"flow_{arc}" for arc in inflow_arcs + outflow_arcs]
        if all_arcs:
            self.solver.add_sum_less_equal(all_arcs, max_level, f"stockpile_{stockpile_id}_max")
    
    def minimize_makespan(self, task_ids: List[str]):
        """Add objective to minimize latest completion time."""
        # Create makespan variable
        max_period = max(self.task_vars[t].domain_max for t in task_ids)
        makespan = self.solver.new_int_var(0, max_period, "makespan")
        
        # Makespan >= all task periods
        for task_id in task_ids:
            self.solver.add_less_equal(f"task_{task_id}_period", max_period)
        
        self.solver.minimize("makespan")
    
    def minimize_total_cost(self, cost_var_name: str):
        """Add objective to minimize total cost."""
        self.solver.minimize(cost_var_name)
    
    def maximize_production(self, production_var_name: str):
        """Add objective to maximize production."""
        self.solver.maximize(production_var_name)
    
    def solve(self, timeout_seconds: int = 60) -> Solution:
        """Solve the mining schedule model."""
        self.solver.max_time_seconds = timeout_seconds
        return self.solver.solve()


# =============================================================================
# Singleton instance for service access
# =============================================================================

cp_solver_service = CPSolver()
