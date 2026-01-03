"""
Staged Stockpile Entities - Section 3.12 of Enterprise Specification

Staged stockpiles are multi-pile configurations where each pile:
- Has a build specification (target tonnes, quality targets)
- Follows a state machine (Building -> Full -> Depleting -> Empty)
- Can converge quality as it fills

This enables sophisticated product blending and quality management.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer, Boolean
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime


class StagedStockpileConfig(Base):
    """
    Configuration for a multi-pile staged stockpile system.
    Attached to a FlowNode of type 'StagedStockpile'.
    """
    __tablename__ = "staged_stockpile_configs"

    config_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False, unique=True)
    
    # Pile configuration
    number_of_piles = Column(Integer, default=2)
    
    # State machine control
    state_machine_enabled = Column(Boolean, default=True)
    
    # Build target configuration
    # "FixedBuildList" = predefined sequence of builds
    # "VariableBuildTargets" = dynamic target assignment
    target_type = Column(String, default="FixedBuildList")
    
    # Allow material to be accepted even if off-spec when pile is near empty
    allow_offspec_early = Column(Boolean, default=False)
    
    # Default reclaim rule when pile is in Depleting state
    default_pile_reclaim_rule = Column(String, default="FIFO")  # FIFO, LIFO, Proportional
    
    # Global capacity per pile (can be overridden in BuildSpec)
    default_pile_capacity_tonnes = Column(Float, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    node = relationship("FlowNode")  # No back_populates to avoid cross-file issues
    build_specs = relationship("BuildSpec", back_populates="staged_config", order_by="BuildSpec.sequence")
    pile_states = relationship("StagedPileState", back_populates="staged_config")

    def __repr__(self):
        return f"<StagedStockpileConfig {self.number_of_piles} piles>"


class BuildSpec(Base):
    """
    A build specification defining target for a staged stockpile pile.
    Includes tonnage targets, quality objectives, and timing constraints.
    """
    __tablename__ = "build_specs"

    spec_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    staged_config_id = Column(String, ForeignKey("staged_stockpile_configs.config_id"), nullable=False)
    
    # Identification
    build_name = Column(String, nullable=False)  # e.g., "Product A - Jan Week 1"
    sequence = Column(Integer, nullable=False)  # Order in build list
    
    # Timing (optional)
    planned_start_period_id = Column(String, ForeignKey("periods.period_id"), nullable=True)
    planned_end_period_id = Column(String, ForeignKey("periods.period_id"), nullable=True)
    
    # Tonnage targets
    target_tonnes = Column(Float, nullable=False)
    min_threshold_tonnes = Column(Float, nullable=True)  # Minimum before reclaim allowed
    max_capacity_tonnes = Column(Float, nullable=True)  # Physical limit
    
    # Material eligibility rules (optional)
    # Example: {"material_types": ["coal_seam_a", "coal_seam_b"], "source_areas": ["pit_1"]}
    material_rules = Column(JSON, nullable=True)
    
    # Quality targets - list of objectives
    # Example: [{"field": "CV_ARB", "type": "Min", "value": 24.0, "weight": 1.0}]
    quality_targets = Column(JSON, default=list)
    
    # Penalty weights for quality deviations
    penalty_weights = Column(JSON, nullable=True)
    
    # Switching rule - when to transition to next build
    # "tonnage_reached" = switch when target_tonnes achieved
    # "quality_met" = switch when quality targets within tolerance
    # "period_end" = switch at planned_end_period
    # "manual" = only switch on explicit command
    switching_rule = Column(String, default="tonnage_reached")
    
    # Convergence rule - how quality tightens as pile fills
    # Optional expression or preset: "linear", "exponential", "none"
    convergence_rule = Column(String, default="none")
    convergence_parameters = Column(JSON, nullable=True)
    
    # Status
    status = Column(String, default="Pending")  # Pending, Active, Complete
    
    # Relationships
    staged_config = relationship("StagedStockpileConfig", back_populates="build_specs")

    def __repr__(self):
        return f"<BuildSpec {self.build_name} {self.target_tonnes}t>"

    def get_quality_target(self, field_name: str) -> dict:
        """Get the quality objective for a specific field."""
        if not self.quality_targets:
            return None
        for target in self.quality_targets:
            if target.get("field") == field_name:
                return target
        return None


class StagedPileState(Base):
    """
    Current state of an individual pile within a staged stockpile.
    Tracks inventory, quality, and state machine status.
    """
    __tablename__ = "staged_pile_states"

    state_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    staged_config_id = Column(String, ForeignKey("staged_stockpile_configs.config_id"), nullable=False)
    
    # Which pile this is (0-indexed)
    pile_index = Column(Integer, nullable=False)
    pile_name = Column(String, nullable=True)  # Optional display name
    
    # State machine status
    # Building = actively accepting material
    # Full = at capacity or target reached, no new material
    # Depleting = being reclaimed
    # Empty = awaiting new build spec assignment
    state = Column(String, default="Empty")
    
    # Current build spec assignment
    current_build_spec_id = Column(String, ForeignKey("build_specs.spec_id"), nullable=True)
    
    # Inventory
    current_tonnes = Column(Float, default=0.0)
    
    # Current quality (weighted average of contents)
    current_quality_vector = Column(JSON, default=dict)
    
    # Parcel tracking (if detailed tracking enabled)
    parcel_ids = Column(JSON, default=list)  # List of parcel IDs in this pile
    
    # State transition history
    last_state_change = Column(DateTime, nullable=True)
    state_change_reason = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    staged_config = relationship("StagedStockpileConfig", back_populates="pile_states")
    current_build_spec = relationship("BuildSpec")

    def __repr__(self):
        return f"<StagedPileState pile={self.pile_index} state={self.state} {self.current_tonnes}t>"

    def can_accept_material(self) -> bool:
        """Check if pile can accept new material."""
        return self.state == "Building"
    
    def can_reclaim(self) -> bool:
        """Check if pile can be reclaimed from."""
        return self.state in ["Depleting", "Full"] and self.current_tonnes > 0


class StagedPileTransaction(Base):
    """
    Records additions and reclaims from staged piles.
    Provides full audit trail for material movements.
    """
    __tablename__ = "staged_pile_transactions"

    transaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pile_state_id = Column(String, ForeignKey("staged_pile_states.state_id"), nullable=False)
    
    # Transaction type
    transaction_type = Column(String, nullable=False)  # Addition, Reclaim
    
    # Scheduling context
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=True)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=True)
    
    # Quantity
    tonnes = Column(Float, nullable=False)
    
    # Quality of material in this transaction
    quality_vector = Column(JSON, default=dict)
    
    # Source/destination reference
    source_reference = Column(String, nullable=True)  # Where material came from (for Addition)
    destination_reference = Column(String, nullable=True)  # Where material went (for Reclaim)
    
    # Resulting pile state after transaction
    pile_tonnes_after = Column(Float, nullable=False)
    pile_quality_after = Column(JSON, default=dict)
    
    # Timestamp
    transaction_time = Column(DateTime, default=datetime.datetime.utcnow)
