"""
Schedule Results Entities - Section 3.15 of Enterprise Specification

These entities capture the outputs of scheduling runs:
- ScheduleRunRequest: Tracks scheduling job execution
- FlowResult: Period-by-period material flow records
- InventoryBalance: Stockpile/node balances per period
- DecisionExplanation: Explanations of optimizer decisions

These provide traceability and enable reporting.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime


class ScheduleRunRequest(Base):
    """
    Tracks a scheduling run request and its execution status.
    Enables async scheduling with progress monitoring.
    """
    __tablename__ = "schedule_run_requests"

    request_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Site context
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Run type
    schedule_type = Column(String, nullable=False)  # FastPass, FullPass
    
    # Version references
    site_model_version = Column(String, nullable=True)  # Semantic version of site config
    state_snapshot_id = Column(String, nullable=True)  # Reference to operational state
    
    # Target schedule version (created or updated by this run)
    target_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=True)
    
    # Horizon definition
    horizon_start_period = Column(String, ForeignKey("periods.period_id"), nullable=False)
    horizon_end_period = Column(String, ForeignKey("periods.period_id"), nullable=False)
    
    # Objective profile (defines weights and priorities)
    objective_profile_id = Column(String, nullable=True)
    objective_profile_snapshot = Column(JSON, nullable=True)  # Frozen copy of profile
    
    # Execution metadata
    run_initiated_by = Column(String, nullable=False)  # User ID
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Status tracking
    status = Column(String, default="Pending")  # Pending, Running, Complete, Failed, Cancelled
    progress_percent = Column(Float, default=0.0)
    current_stage = Column(String, nullable=True)  # e.g., "Stage 3: Resource Assignment"
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Error information (if failed)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Summary statistics (populated on completion)
    summary_stats = Column(JSON, nullable=True)
    # Example: {"tasks_created": 150, "total_tonnes": 500000, "infeasibilities": 0}
    
    # Relationships
    site = relationship("Site")

    def __repr__(self):
        return f"<ScheduleRunRequest {self.request_id[:8]}... {self.schedule_type} {self.status}>"


class FlowResult(Base):
    """
    Records material flow through an arc for a specific period.
    Created by the scheduling engine for each routing decision.
    """
    __tablename__ = "flow_results"

    flow_result_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=False)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=False)
    
    # Flow path
    from_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=True)
    to_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False)
    arc_id = Column(String, ForeignKey("flow_arcs.arc_id"), nullable=True)
    
    # Material
    material_type_id = Column(String, ForeignKey("material_types.material_type_id"), nullable=True)
    
    # Quantity
    tonnes = Column(Float, nullable=False)
    
    # Quality of material in this flow
    quality_vector = Column(JSON, default=dict)
    
    # Economic metrics
    cost = Column(Float, default=0.0)  # Haulage cost, processing cost, etc.
    benefit = Column(Float, default=0.0)  # Revenue if product, value added
    penalty_cost = Column(Float, default=0.0)  # Quality deviation penalties
    
    # Link to explanation
    decision_explanation_id = Column(String, ForeignKey("decision_explanations.explanation_id"), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    schedule_version = relationship("ScheduleVersion")
    decision_explanation = relationship("DecisionExplanation")

    def __repr__(self):
        return f"<FlowResult {self.tonnes}t from={self.from_node_id[:8] if self.from_node_id else 'source'}... to={self.to_node_id[:8]}...>"

    @property
    def net_value(self) -> float:
        """Calculate net value of this flow (benefit - cost - penalty)."""
        return self.benefit - self.cost - self.penalty_cost


class InventoryBalance(Base):
    """
    Records inventory state at a node for a specific period.
    Tracks opening, additions, reclaims, and closing balances.
    """
    __tablename__ = "inventory_balances"

    balance_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=False)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=False)
    node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False)
    
    # Balance components
    opening_tonnes = Column(Float, default=0.0)
    additions_tonnes = Column(Float, default=0.0)
    reclaim_tonnes = Column(Float, default=0.0)
    
    # Processing (for plant nodes)
    processing_in_tonnes = Column(Float, nullable=True)
    processing_out_tonnes = Column(Float, nullable=True)
    
    # Closing balance
    closing_tonnes = Column(Float, default=0.0)
    
    # Quality vectors
    opening_quality_vector = Column(JSON, default=dict)
    additions_quality_vector = Column(JSON, nullable=True)  # Weighted avg of additions
    closing_quality_vector = Column(JSON, default=dict)
    
    # Capacity utilization
    capacity_tonnes = Column(Float, nullable=True)
    utilization_percent = Column(Float, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    schedule_version = relationship("ScheduleVersion")

    def __repr__(self):
        return f"<InventoryBalance {self.node_id[:8]}... open={self.opening_tonnes} close={self.closing_tonnes}>"

    def calculate_closing(self):
        """Recalculate closing balance from components."""
        self.closing_tonnes = (
            self.opening_tonnes 
            + self.additions_tonnes 
            - self.reclaim_tonnes
            + (self.processing_in_tonnes or 0)
            - (self.processing_out_tonnes or 0)
        )


class DecisionExplanation(Base):
    """
    Explains why the optimizer made a specific decision.
    Provides transparency and debuggability.
    """
    __tablename__ = "decision_explanations"

    explanation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=False)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=True)
    
    # Decision categorization
    decision_type = Column(String, nullable=False)
    # Types: Routing, Blend, Cutpoint, StockpileStateSwitch, RateReduction, ResourceAssignment
    
    # Related entities
    related_task_id = Column(String, nullable=True)
    related_arc_id = Column(String, nullable=True)
    related_node_id = Column(String, nullable=True)
    
    # Human-readable summary
    summary_text = Column(Text, nullable=False)
    
    # Binding constraints that drove the decision
    # Example: [{"constraint": "Arc capacity", "value": 5000, "limit": 5000, "status": "binding"}]
    binding_constraints = Column(JSON, default=list)
    
    # Penalty breakdown
    # Example: [{"objective": "CV_ARB target", "deviation": -1.2, "penalty": 120.0}]
    penalty_breakdown = Column(JSON, default=list)
    
    # Total penalty/cost attributed to this decision
    total_penalty = Column(Float, default=0.0)
    
    # Alternatives that were considered (optional)
    # Example: [{"route": "ROM->Plant", "penalty": 500}, {"route": "ROM->Stockpile", "penalty": 200}]
    alternatives_considered = Column(JSON, nullable=True)
    
    # Sensitivity notes (optional)
    sensitivity_notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    schedule_version = relationship("ScheduleVersion")

    def __repr__(self):
        return f"<DecisionExplanation {self.decision_type}: {self.summary_text[:50]}...>"


class ObjectiveProfile(Base):
    """
    Defines the objective function and weights for optimization.
    Different profiles can prioritize different goals.
    """
    __tablename__ = "objective_profiles"

    profile_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    
    # Objective weights (higher = more important)
    # These define the multi-objective priority stack
    weights = Column(JSON, nullable=False)
    # Example: {
    #   "meet_demand": 100.0,
    #   "quality_compliance": 80.0,
    #   "maximize_value": 60.0,
    #   "minimize_rehandle": 40.0,
    #   "operational_smoothness": 20.0
    # }
    
    # Penalty scaling factors
    penalty_scales = Column(JSON, nullable=True)
    # Example: {"quality_deviation": 10.0, "capacity_violation": 1000.0}
    
    # Constraint modes (hard vs soft)
    constraint_modes = Column(JSON, nullable=True)
    # Example: {"cv_min": "hard", "ash_max": "soft"}
    
    # Active status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    # Relationships
    site = relationship("Site")

    def __repr__(self):
        return f"<ObjectiveProfile {self.name}>"
