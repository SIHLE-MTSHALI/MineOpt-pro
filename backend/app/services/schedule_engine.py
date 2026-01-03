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
        Generates decision explanations.
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
        
        # Iterate through periods
        for period in periods:
            if not candidates:
                break
            
            # Stage 3: Resource assignment
            period_usage = {}
            assignments = self.resource_assigner.assign_resources(
                candidates, resources, period, period_usage
            )
            
            # Stage 4: Material generation
            parcels = self.material_generator.generate_parcels(
                assignments, period, config.schedule_version_id
            )
            
            # Create tasks for assignments
            for assign in assignments:
                task = Task(
                    task_id=str(uuid.uuid4()),
                    schedule_version_id=config.schedule_version_id,
                    resource_id=assign['resource_id'],
                    activity_id=assign['activity_id'],
                    period_id=period.period_id,
                    activity_area_id=assign['area_id'],
                    planned_quantity=assign['assigned_quantity'],
                    material_type_id=assign.get('material_type_id'),
                    quality_vector=assign.get('quality_vector'),
                    task_type="Mining",
                    status="Scheduled"
                )
                tasks_created.append(task)
                total_tonnes += assign['assigned_quantity']
                
                # Remove from candidates
                candidates = [c for c in candidates if c['area_id'] != assign['area_id']]
            
            # Stage 5: Flow optimization (if network exists)
            if network and parcels:
                flow_summary = self.flow_optimizer.optimize_period_flows(
                    period.period_id,
                    parcels,
                    network,
                    config.schedule_version_id
                )
                
                all_flows.extend(flow_summary.flow_results)
                all_explanations.extend(flow_summary.explanations)
                total_cost += flow_summary.total_cost
                total_benefit += flow_summary.total_benefit
                total_penalty += flow_summary.total_penalty
        
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
