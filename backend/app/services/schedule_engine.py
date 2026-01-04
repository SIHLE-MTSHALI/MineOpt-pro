"""
Schedule Engine - Section 2 of Enterprise Specification

Main orchestrator for the 8-stage scheduling pipeline.
Supports FastPass (simplified) and FullPass (complete) optimization modes.

Pipeline Stages:
1. Input Validation - Check data integrity
2. Build Candidate List - Identify work to be scheduled
3. Resource Assignment - Allocate resources to tasks
4. Material Generation - Create parcels from mining
5. Routing & Blending - Determine material flow
6. Processing Optimization - Wash plant decisions
7. Feedback & Adjustment - Iterate if needed
8. Finalize Results - Persist schedule output
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..domain.models_scheduling import ScheduleVersion, Task
from ..domain.models_calendar import Calendar, Period
from ..domain.models_resource import Resource, ActivityArea, Activity
from ..domain.models_flow import FlowNetwork, FlowNode, FlowArc
from ..domain.models_parcel import Parcel, ParcelMovement
from ..domain.models_schedule_results import (
    ScheduleRunRequest, FlowResult, InventoryBalance, 
    DecisionExplanation, ObjectiveProfile
)
from .blending_service import BlendingService, blending_service
from .flow_optimizer import FlowOptimizer
from .lp_allocator import LPMaterialAllocator, create_lp_allocator


@dataclass
class ScheduleRunConfig:
    """Configuration for a schedule run."""
    site_id: str
    schedule_version_id: str
    horizon_start_period_id: Optional[str] = None
    horizon_end_period_id: Optional[str] = None
    objective_profile_id: Optional[str] = None
    max_iterations: int = 5
    target_gap_percent: float = 0.01
    use_lp_solver: bool = True  # Use LP solver for Full Pass (False = greedy)
    

@dataclass
class ScheduleRunResult:
    """Result of a schedule run."""
    success: bool
    schedule_version_id: str
    tasks_created: int
    flows_created: int
    total_tonnes: float
    total_cost: float
    total_benefit: float
    total_penalty: float
    diagnostics: List[str]
    explanation_count: int


class InputValidator:
    """Validates inputs before scheduling."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate(self, config: ScheduleRunConfig) -> Tuple[bool, List[str]]:
        """
        Validate all inputs for a schedule run.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        
        # Check site exists
        from ..domain.models_core import Site
        site = self.db.query(Site).filter(Site.site_id == config.site_id).first()
        if not site:
            errors.append(f"Site {config.site_id} not found")
        
        # Check schedule version exists
        version = self.db.query(ScheduleVersion)\
            .filter(ScheduleVersion.version_id == config.schedule_version_id)\
            .first()
        if not version:
            errors.append(f"Schedule version {config.schedule_version_id} not found")
        elif version.status == "Published":
            errors.append("Cannot modify published schedule version")
        
        # Check calendar exists with periods
        calendar = self.db.query(Calendar)\
            .filter(Calendar.site_id == config.site_id)\
            .first()
        if not calendar:
            errors.append("No calendar found for site")
        else:
            periods = self.db.query(Period)\
                .filter(Period.calendar_id == calendar.calendar_id)\
                .count()
            if periods == 0:
                errors.append("Calendar has no periods defined")
        
        # Check resources exist
        resources = self.db.query(Resource)\
            .filter(Resource.site_id == config.site_id)\
            .count()
        if resources == 0:
            errors.append("No resources found for site")
        
        # Check activity areas exist
        areas = self.db.query(ActivityArea)\
            .filter(ActivityArea.site_id == config.site_id)\
            .count()
        if areas == 0:
            errors.append("No activity areas found for site")
        
        return len(errors) == 0, errors


class CandidateBuilder:
    """Builds list of candidate work items to be scheduled."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def build_candidates(
        self, 
        site_id: str, 
        existing_task_area_ids: set
    ) -> List[Dict]:
        """
        Identify work candidates from activity areas.
        Returns list of candidate dicts with area info and quantities.
        """
        candidates = []
        
        # Get all unlocked activity areas
        areas = self.db.query(ActivityArea)\
            .filter(ActivityArea.site_id == site_id)\
            .filter(ActivityArea.is_locked == False)\
            .all()
        
        for area in areas:
            # Check if already scheduled
            if area.area_id in existing_task_area_ids:
                continue
            
            # Get available slices
            slice_states = area.slice_states or []
            for i, slice_state in enumerate(slice_states):
                status = slice_state.get('status', 'Available')
                if status in ['Available', 'Released']:
                    quantity = slice_state.get('quantity', 0)
                    if quantity > 0:
                        candidates.append({
                            'area_id': area.area_id,
                            'area_name': area.name,
                            'activity_id': area.activity_id,
                            'slice_index': i,
                            'quantity': quantity,
                            'material_type_id': slice_state.get('material_type_id'),
                            'quality_vector': slice_state.get('qualities', {}),
                            'priority': area.priority or 0
                        })
        
        # Sort by priority (descending)
        candidates.sort(key=lambda c: c['priority'], reverse=True)
        
        return candidates


class ResourceAssigner:
    """Assigns resources to tasks."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def assign_resources(
        self,
        candidates: List[Dict],
        resources: List[Resource],
        period: Period,
        period_usage: Dict[str, float]  # resource_id -> tonnes used
    ) -> List[Dict]:
        """
        Assign candidates to resources for a period.
        Returns list of assignment dicts.
        """
        assignments = []
        duration_hours = period.calculated_duration_hours if hasattr(period, 'calculated_duration_hours') else 12.0
        
        for candidate in candidates:
            # Find eligible resource with capacity
            for resource in resources:
                # Check if resource supports this activity
                supported = resource.supported_activities or []
                if supported and candidate['activity_id'] not in supported:
                    continue
                
                # Calculate capacity for this period
                base_capacity = (resource.base_rate or 0) * duration_hours
                used = period_usage.get(resource.resource_id, 0)
                remaining = base_capacity - used
                
                if remaining >= candidate['quantity']:
                    # Full assignment
                    assignments.append({
                        **candidate,
                        'resource_id': resource.resource_id,
                        'assigned_quantity': candidate['quantity']
                    })
                    period_usage[resource.resource_id] = used + candidate['quantity']
                    break
                elif remaining > 0:
                    # Partial assignment (resource can handle some)
                    assignments.append({
                        **candidate,
                        'resource_id': resource.resource_id,
                        'assigned_quantity': remaining
                    })
                    period_usage[resource.resource_id] = base_capacity
                    # Note: remaining candidate quantity would need to be re-queued
                    break
        
        return assignments


class MaterialGenerator:
    """Generates parcels from mining activities."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_parcels(
        self,
        assignments: List[Dict],
        period: Period,
        schedule_version_id: str
    ) -> List[Parcel]:
        """
        Create parcel records for scheduled mining.
        """
        parcels = []
        
        for assign in assignments:
            parcel = Parcel(
                parcel_id=str(uuid.uuid4()),
                site_id=None,  # Will be set from area
                source_reference=f"area:{assign['area_id']}:slice:{assign.get('slice_index', 0)}",
                period_available_from=period.period_id,
                quantity_tonnes=assign['assigned_quantity'],
                material_type_id=assign.get('material_type_id'),
                quality_vector=assign.get('quality_vector', {}),
                status="Available"
            )
            parcels.append(parcel)
        
        return parcels


class ScheduleEngine:
    """
    Orchestrates the 8-stage scheduling pipeline.
    Supports FastPass (simplified) and FullPass (complete) modes.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = InputValidator(db)
        self.candidate_builder = CandidateBuilder(db)
        self.resource_assigner = ResourceAssigner(db)
        self.material_generator = MaterialGenerator(db)
        self.flow_optimizer = FlowOptimizer(db)
        self.lp_allocator = create_lp_allocator(db)  # LP-based optimizer
        self.blending = blending_service
    
    def run_fast_pass(self, config: ScheduleRunConfig) -> ScheduleRunResult:
        """
        Quick schedule for interactive editing (target: <5 seconds).
        
        Stages executed:
        - Stage 1: Basic validation only
        - Stage 2-3: Candidate list + resource assignment
        - Stage 5: Greedy routing (no optimization)
        - Skip stages 4, 6, 7
        - Stage 8: Basic finalization
        """
        diagnostics = []
        diagnostics.append("Starting Fast Pass scheduling...")
        
        # Stage 1: Validation
        is_valid, errors = self.validator.validate(config)
        if not is_valid:
            return ScheduleRunResult(
                success=False,
                schedule_version_id=config.schedule_version_id,
                tasks_created=0,
                flows_created=0,
                total_tonnes=0,
                total_cost=0,
                total_benefit=0,
                total_penalty=0,
                diagnostics=errors,
                explanation_count=0
            )
        diagnostics.append("Validation passed")
        
        # Get resources
        resources = self.db.query(Resource)\
            .filter(Resource.site_id == config.site_id)\
            .filter(Resource.resource_type == "Excavator")\
            .all()
        
        # Get periods
        calendar = self.db.query(Calendar)\
            .filter(Calendar.site_id == config.site_id)\
            .first()
        
        periods = self.db.query(Period)\
            .filter(Period.calendar_id == calendar.calendar_id)\
            .order_by(Period.start_datetime)\
            .all()
        
        # Filter horizon if specified
        if config.horizon_start_period_id:
            periods = [p for p in periods if p.period_id >= config.horizon_start_period_id]
        if config.horizon_end_period_id:
            periods = [p for p in periods if p.period_id <= config.horizon_end_period_id]
        
        # Get existing tasks to avoid re-scheduling
        existing_tasks = self.db.query(Task)\
            .filter(Task.schedule_version_id == config.schedule_version_id)\
            .all()
        existing_area_ids = {t.activity_area_id for t in existing_tasks if t.activity_area_id}
        
        # Stage 2: Build candidates
        candidates = self.candidate_builder.build_candidates(config.site_id, existing_area_ids)
        diagnostics.append(f"Found {len(candidates)} work candidates")
        
        # Track results
        tasks_created = []
        total_tonnes = 0.0
        
        # Stage 3: Resource assignment per period
        for period in periods:
            if not candidates:
                break  # No more work
            
            period_usage = {}
            assignments = self.resource_assigner.assign_resources(
                candidates, resources, period, period_usage
            )
            
            for assign in assignments:
                # Create task
                task = Task(
                    task_id=str(uuid.uuid4()),
                    schedule_version_id=config.schedule_version_id,
                    resource_id=assign['resource_id'],
                    activity_id=assign['activity_id'],
                    period_id=period.period_id,
                    activity_area_id=assign['area_id'],
                    planned_quantity=assign['assigned_quantity'],
                    task_type="Mining",
                    status="Scheduled"
                )
                tasks_created.append(task)
                total_tonnes += assign['assigned_quantity']
                
                # Remove from candidates (area level)
                candidates = [c for c in candidates if c['area_id'] != assign['area_id']]
        
        # Stage 8: Finalize
        if tasks_created:
            self.db.add_all(tasks_created)
            self.db.commit()
        
        diagnostics.append(f"Created {len(tasks_created)} tasks")
        diagnostics.append(f"Total tonnage: {total_tonnes:,.0f}t")
        
        return ScheduleRunResult(
            success=True,
            schedule_version_id=config.schedule_version_id,
            tasks_created=len(tasks_created),
            flows_created=0,  # Fast pass skips flow generation
            total_tonnes=total_tonnes,
            total_cost=0,
            total_benefit=0,
            total_penalty=0,
            diagnostics=diagnostics,
            explanation_count=0
        )
    
    def run_full_pass(self, config: ScheduleRunConfig) -> ScheduleRunResult:
        """
        Authoritative schedule with full optimization.
        
        All 8 stages executed with iteration until convergence.
        Generates decision explanations and OptimiserDelay tasks.
        """
        diagnostics = []
        diagnostics.append("Starting Full Pass optimization...")
        
        # Stage 1: Full validation
        is_valid, errors = self.validator.validate(config)
        if not is_valid:
            return ScheduleRunResult(
                success=False,
                schedule_version_id=config.schedule_version_id,
                tasks_created=0,
                flows_created=0,
                total_tonnes=0,
                total_cost=0,
                total_benefit=0,
                total_penalty=0,
                diagnostics=errors,
                explanation_count=0
            )
        diagnostics.append("Validation passed")
        
        # Get resources
        resources = self.db.query(Resource)\
            .filter(Resource.site_id == config.site_id)\
            .filter(Resource.resource_type == "Excavator")\
            .all()
        
        # Get flow network
        network = self.db.query(FlowNetwork)\
            .filter(FlowNetwork.site_id == config.site_id)\
            .first()
        
        # Get periods
        calendar = self.db.query(Calendar)\
            .filter(Calendar.site_id == config.site_id)\
            .first()
        
        periods = self.db.query(Period)\
            .filter(Period.calendar_id == calendar.calendar_id)\
            .order_by(Period.start_datetime)\
            .all()
        
        # Get existing tasks
        existing_tasks = self.db.query(Task)\
            .filter(Task.schedule_version_id == config.schedule_version_id)\
            .all()
        existing_area_ids = {t.activity_area_id for t in existing_tasks if t.activity_area_id}
        
        # Stage 2: Build candidates
        candidates = self.candidate_builder.build_candidates(config.site_id, existing_area_ids)
        diagnostics.append(f"Found {len(candidates)} work candidates")
        
        # Track results
        tasks_created = []
        all_flows = []
        all_explanations = []
        total_tonnes = 0.0
        total_cost = 0.0
        total_benefit = 0.0
        total_penalty = 0.0
        
        # Multi-iteration optimization loop (Stage 7: Feedback & Adjustment)
        best_penalty = float('inf')
        best_solution = None
        iteration = 0
        
        while iteration < config.max_iterations:
            iteration += 1
            iteration_tasks = []
            iteration_flows = []
            iteration_explanations = []
            iteration_tonnes = 0.0
            iteration_cost = 0.0
            iteration_benefit = 0.0
            iteration_penalty = 0.0
            
            # Reset candidates for this iteration
            working_candidates = candidates.copy()
            
            # Iterate through periods
            for period in periods:
                if not working_candidates:
                    break
                
                # Stage 3: Resource assignment
                period_usage = {}
                assignments = self.resource_assigner.assign_resources(
                    working_candidates, resources, period, period_usage
                )
                
                # Stage 4: Material generation
                parcels = self.material_generator.generate_parcels(
                    assignments, period, config.schedule_version_id
                )
                
                # Create tasks for assignments
                for assign in assignments:
                    # Check if rate reduction needed (Variable Production Control)
                    rate_factor = self._calculate_rate_factor(assign, resources)
                    
                    if rate_factor < 1.0:
                        # Generate OptimiserDelay task explaining the reduction
                        delay_task = self._create_optimiser_delay_task(
                            config.schedule_version_id,
                            period.period_id,
                            assign,
                            rate_factor
                        )
                        iteration_tasks.append(delay_task)
                        
                        # Add explanation for why reduction was needed
                        explanation = DecisionExplanation(
                            explanation_id=str(uuid.uuid4()),
                            schedule_version_id=config.schedule_version_id,
                            period_id=period.period_id,
                            decision_type="RateReduction",
                            summary=f"Reduced rate to {rate_factor*100:.0f}% for {assign['area_name']}",
                            binding_constraint=self._get_binding_constraint(assign),
                            penalty_breakdown={"rate_reduction": (1-rate_factor) * 100}
                        )
                        iteration_explanations.append(explanation)
                    
                    task = Task(
                        task_id=str(uuid.uuid4()),
                        schedule_version_id=config.schedule_version_id,
                        resource_id=assign['resource_id'],
                        activity_id=assign['activity_id'],
                        period_id=period.period_id,
                        activity_area_id=assign['area_id'],
                        planned_quantity=assign['assigned_quantity'] * rate_factor,
                        material_type_id=assign.get('material_type_id'),
                        quality_vector=assign.get('quality_vector'),
                        task_type="Mining",
                        status="Scheduled"
                    )
                    iteration_tasks.append(task)
                    iteration_tonnes += assign['assigned_quantity'] * rate_factor
                    
                    # Remove from candidates
                    working_candidates = [c for c in working_candidates if c['area_id'] != assign['area_id']]
                
                # Stage 5: Flow optimization (if network exists)
                if network and parcels:
                    if config.use_lp_solver:
                        # Use LP solver for optimal allocation
                        lp_result = self.lp_allocator.solve_allocation(
                            parcels=parcels,
                            network=network,
                            period_id=period.period_id,
                            schedule_version_id=config.schedule_version_id,
                            existing_node_loads={}  # Could track across periods
                        )
                        if lp_result.success:
                            iteration_flows.extend(lp_result.flow_results)
                            iteration_explanations.extend(lp_result.explanations)
                            iteration_cost += lp_result.total_cost
                            iteration_penalty += lp_result.total_penalty
                            # Calculate benefit from flows
                            for flow in lp_result.flow_results:
                                iteration_benefit += flow.benefit or 0.0
                        else:
                            diagnostics.append(f"LP solver failed: {lp_result.solver_message}")
                    else:
                        # Use greedy optimizer (fallback)
                        flow_summary = self.flow_optimizer.optimize_period_flows(
                            period.period_id,
                            parcels,
                            network,
                            config.schedule_version_id
                        )
                        iteration_flows.extend(flow_summary.flow_results)
                        iteration_explanations.extend(flow_summary.explanations)
                        iteration_cost += flow_summary.total_cost
                        iteration_benefit += flow_summary.total_benefit
                        iteration_penalty += flow_summary.total_penalty
            
            # Stage 6: Processing optimization (wash plant)
            # Handled within flow_optimizer.optimize_period_flows
            
            # Check if this iteration is better
            if iteration_penalty < best_penalty:
                best_penalty = iteration_penalty
                best_solution = {
                    'tasks': iteration_tasks,
                    'flows': iteration_flows,
                    'explanations': iteration_explanations,
                    'tonnes': iteration_tonnes,
                    'cost': iteration_cost,
                    'benefit': iteration_benefit,
                    'penalty': iteration_penalty
                }
                diagnostics.append(f"Iteration {iteration}: New best solution (penalty: {iteration_penalty:.2f})")
            else:
                diagnostics.append(f"Iteration {iteration}: No improvement")
            
            # Check convergence (gap < target)
            if best_penalty == 0 or (iteration > 1 and abs(iteration_penalty - best_penalty) / max(best_penalty, 1) < config.target_gap_percent):
                diagnostics.append(f"Converged after {iteration} iterations")
                break
        
        # Use best solution
        if best_solution:
            tasks_created = best_solution['tasks']
            all_flows = best_solution['flows']
            all_explanations = best_solution['explanations']
            total_tonnes = best_solution['tonnes']
            total_cost = best_solution['cost']
            total_benefit = best_solution['benefit']
            total_penalty = best_solution['penalty']
        
        # Stage 8: Finalize
        if tasks_created:
            self.db.add_all(tasks_created)
        
        if all_flows:
            self.db.add_all(all_flows)
        
        if all_explanations:
            self.db.add_all(all_explanations)
        
        self.db.commit()
        
        diagnostics.append(f"Created {len(tasks_created)} tasks")
        diagnostics.append(f"Created {len(all_flows)} flow records")
        diagnostics.append(f"Total tonnage: {total_tonnes:,.0f}t")
        diagnostics.append(f"Net value: ${total_benefit - total_cost - total_penalty:,.0f}")
        
        return ScheduleRunResult(
            success=True,
            schedule_version_id=config.schedule_version_id,
            tasks_created=len(tasks_created),
            flows_created=len(all_flows),
            total_tonnes=total_tonnes,
            total_cost=total_cost,
            total_benefit=total_benefit,
            total_penalty=total_penalty,
            diagnostics=diagnostics,
            explanation_count=len(all_explanations)
        )
    
    def _calculate_rate_factor(self, assignment: Dict, resources: List[Resource]) -> float:
        """Calculate rate factor based on constraints."""
        # Check if quality constraints require rate reduction
        quality = assignment.get('quality_vector', {})
        
        # Example: reduce rate if quality is borderline
        if quality.get('Ash', 0) > 18:  # High ash requires slower processing
            return max(0.7, 1 - (quality['Ash'] - 18) * 0.05)
        
        # Check resource min rate factor
        for resource in resources:
            if resource.resource_id == assignment.get('resource_id'):
                min_factor = getattr(resource, 'min_rate_factor', None) or 0.5
                return max(min_factor, 1.0)
        
        return 1.0
    
    def _get_binding_constraint(self, assignment: Dict) -> str:
        """Determine the binding constraint for rate reduction."""
        quality = assignment.get('quality_vector', {})
        
        if quality.get('Ash', 0) > 18:
            return f"Ash quality ({quality['Ash']:.1f}%) exceeds threshold"
        
        return "Resource capacity constraint"
    
    def _create_optimiser_delay_task(
        self,
        schedule_version_id: str,
        period_id: str,
        assignment: Dict,
        rate_factor: float
    ) -> Task:
        """Create an OptimiserDelay task to explain rate reduction."""
        return Task(
            task_id=str(uuid.uuid4()),
            schedule_version_id=schedule_version_id,
            period_id=period_id,
            activity_area_id=assignment['area_id'],
            task_type="OptimiserDelay",
            status="Scheduled",
            delay_reason_code="RATE_REDUCTION",
            notes=f"Rate reduced to {rate_factor*100:.0f}% due to {self._get_binding_constraint(assignment)}"
        )
    
    def create_run_request(
        self,
        config: ScheduleRunConfig,
        run_type: str  # "FastPass" or "FullPass"
    ) -> ScheduleRunRequest:
        """Create and persist a run request for tracking."""
        request = ScheduleRunRequest(
            request_id=str(uuid.uuid4()),
            schedule_version_id=config.schedule_version_id,
            schedule_type=run_type,
            site_model_version="1.0",
            state_snapshot_id=None,
            horizon_start_period=config.horizon_start_period_id,
            horizon_end_period=config.horizon_end_period_id,
            run_initiated_by="system",
            objective_profile_id=config.objective_profile_id,
            timestamp=datetime.utcnow(),
            status="Running",
            progress_percent=0
        )
        self.db.add(request)
        self.db.commit()
        return request
    
    def update_run_status(
        self,
        request_id: str,
        status: str,
        progress: float = None
    ):
        """Update the status of a run request."""
        request = self.db.query(ScheduleRunRequest)\
            .filter(ScheduleRunRequest.request_id == request_id)\
            .first()
        if request:
            request.status = status
            if progress is not None:
                request.progress_percent = progress
            self.db.commit()
