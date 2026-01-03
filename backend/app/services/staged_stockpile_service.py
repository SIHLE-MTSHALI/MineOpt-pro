"""
Staged Stockpile Service - Section 3.12 of Enterprise Specification

Multi-pile stockpile management providing:
- State machine transitions (Building → Full → Depleting → Empty)
- BuildSpec progression logic
- Quality convergence rules
- Integration with scheduling engine
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..domain.models_staged_stockpile import (
    StagedStockpileConfig, BuildSpec, StagedPileState, StagedPileTransaction
)
from ..domain.models_flow import FlowNode
from ..domain.models_parcel import Parcel
from ..services.quality_service import QualityService, quality_service


@dataclass
class PileStatus:
    """Current status of a single pile in a staged stockpile."""
    pile_index: int
    pile_name: str
    state: str  # Building, Full, Depleting, Empty
    current_tonnes: float
    target_tonnes: float
    current_quality: Dict[str, float]
    build_spec_name: Optional[str]
    progress_percent: float


@dataclass
class StagedStockpileStatus:
    """Overall status of a staged stockpile."""
    node_id: str
    node_name: str
    number_of_piles: int
    total_tonnes: float
    piles: List[PileStatus]
    building_pile_index: Optional[int]
    depleting_pile_index: Optional[int]
    active_build_spec: Optional[str]


@dataclass
class MaterialAcceptResult:
    """Result of attempting to accept material."""
    accepted: bool
    pile_index: int
    tonnes_accepted: float
    reason: str


class StagedStockpileService:
    """
    Manages multi-pile staged stockpiles with state machine logic.
    
    State Machine:
    - Empty: Awaiting build spec assignment
    - Building: Actively accepting material
    - Full: At target tonnage, awaiting reclaim
    - Depleting: Being reclaimed
    
    Transitions:
    - Empty → Building: When assigned a new build spec
    - Building → Full: When target tonnage reached
    - Full → Depleting: When reclaim begins
    - Depleting → Empty: When pile is empty
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # -------------------------------------------------------------------------
    # Status Queries
    # -------------------------------------------------------------------------
    
    def get_staged_stockpile_status(
        self, 
        node_id: str
    ) -> Optional[StagedStockpileStatus]:
        """Get comprehensive status of a staged stockpile."""
        node = self.db.query(FlowNode)\
            .filter(FlowNode.node_id == node_id)\
            .first()
        
        if not node or node.node_type != "StagedStockpile":
            return None
        
        # Get config via query since relationship was removed
        config = self.db.query(StagedStockpileConfig)\
            .filter(StagedStockpileConfig.node_id == node_id)\
            .first()
        
        if not config:
            return None
        
        # Get pile states
        pile_states = self.db.query(StagedPileState)\
            .filter(StagedPileState.staged_config_id == config.config_id)\
            .order_by(StagedPileState.pile_index)\
            .all()
        
        piles = []
        building_index = None
        depleting_index = None
        total_tonnes = 0.0
        
        for ps in pile_states:
            # Get build spec if assigned
            build_spec = None
            target_tonnes = 0.0
            if ps.current_build_spec_id:
                build_spec = self.db.query(BuildSpec)\
                    .filter(BuildSpec.spec_id == ps.current_build_spec_id)\
                    .first()
                if build_spec:
                    target_tonnes = build_spec.target_tonnes
            
            progress = (ps.current_tonnes / target_tonnes * 100) if target_tonnes > 0 else 0.0
            
            piles.append(PileStatus(
                pile_index=ps.pile_index,
                pile_name=ps.pile_name or f"Pile {ps.pile_index + 1}",
                state=ps.state,
                current_tonnes=ps.current_tonnes,
                target_tonnes=target_tonnes,
                current_quality=ps.current_quality_vector or {},
                build_spec_name=build_spec.build_name if build_spec else None,
                progress_percent=round(progress, 1)
            ))
            
            total_tonnes += ps.current_tonnes
            
            if ps.state == "Building":
                building_index = ps.pile_index
            elif ps.state == "Depleting":
                depleting_index = ps.pile_index
        
        # Get active build spec
        active_spec = None
        if building_index is not None and piles:
            active_spec = piles[building_index].build_spec_name
        
        return StagedStockpileStatus(
            node_id=node_id,
            node_name=node.name,
            number_of_piles=config.number_of_piles,
            total_tonnes=total_tonnes,
            piles=piles,
            building_pile_index=building_index,
            depleting_pile_index=depleting_index,
            active_build_spec=active_spec
        )
    
    # -------------------------------------------------------------------------
    # Material Acceptance
    # -------------------------------------------------------------------------
    
    def accept_material(
        self,
        node_id: str,
        quantity_tonnes: float,
        quality_vector: Dict[str, float],
        source_reference: str = None,
        period_id: str = None
    ) -> MaterialAcceptResult:
        """
        Accept material into the staged stockpile.
        
        Material goes to the pile in "Building" state.
        Checks quality against build spec if convergence rules apply.
        """
        config = self.db.query(StagedStockpileConfig)\
            .filter(StagedStockpileConfig.node_id == node_id)\
            .first()
        
        if not config:
            return MaterialAcceptResult(
                accepted=False,
                pile_index=-1,
                tonnes_accepted=0,
                reason="Staged stockpile config not found"
            )
        
        # Find building pile
        building_pile = self.db.query(StagedPileState)\
            .filter(StagedPileState.staged_config_id == config.config_id)\
            .filter(StagedPileState.state == "Building")\
            .first()
        
        if not building_pile:
            return MaterialAcceptResult(
                accepted=False,
                pile_index=-1,
                tonnes_accepted=0,
                reason="No pile in Building state"
            )
        
        # Get build spec for capacity check
        build_spec = None
        if building_pile.current_build_spec_id:
            build_spec = self.db.query(BuildSpec)\
                .filter(BuildSpec.spec_id == building_pile.current_build_spec_id)\
                .first()
        
        # Check capacity
        max_capacity = config.default_pile_capacity_tonnes
        if build_spec and build_spec.max_capacity_tonnes:
            max_capacity = build_spec.max_capacity_tonnes
        
        if max_capacity:
            available = max_capacity - building_pile.current_tonnes
            if quantity_tonnes > available:
                quantity_tonnes = available
        
        if quantity_tonnes <= 0:
            return MaterialAcceptResult(
                accepted=False,
                pile_index=building_pile.pile_index,
                tonnes_accepted=0,
                reason="Pile at capacity"
            )
        
        # Blend quality
        new_quality = quality_service.calculate_incremental_blend(
            building_pile.current_quality_vector or {},
            building_pile.current_tonnes,
            quality_vector,
            quantity_tonnes
        )
        
        # Update pile state
        building_pile.current_tonnes += quantity_tonnes
        building_pile.current_quality_vector = new_quality
        building_pile.updated_at = datetime.utcnow()
        
        # Record transaction
        transaction = StagedPileTransaction(
            transaction_id=str(uuid.uuid4()),
            pile_state_id=building_pile.state_id,
            transaction_type="Addition",
            period_id=period_id,
            tonnes=quantity_tonnes,
            quality_vector=quality_vector,
            source_reference=source_reference,
            pile_tonnes_after=building_pile.current_tonnes,
            pile_quality_after=new_quality
        )
        self.db.add(transaction)
        
        # Check if target reached → transition to Full
        if build_spec and building_pile.current_tonnes >= build_spec.target_tonnes:
            self._transition_pile(building_pile, "Full", "Target tonnage reached")
            # Try to assign next build spec to an empty pile
            self._assign_next_build_spec(config)
        
        self.db.commit()
        
        return MaterialAcceptResult(
            accepted=True,
            pile_index=building_pile.pile_index,
            tonnes_accepted=quantity_tonnes,
            reason="Material accepted"
        )
    
    # -------------------------------------------------------------------------
    # Material Reclaim
    # -------------------------------------------------------------------------
    
    def reclaim_material(
        self,
        node_id: str,
        quantity_tonnes: float,
        period_id: str = None
    ) -> Tuple[float, Dict[str, float], str]:
        """
        Reclaim material from the depleting pile.
        
        Returns:
            Tuple of (tonnes_reclaimed, quality, message)
        """
        config = self.db.query(StagedStockpileConfig)\
            .filter(StagedStockpileConfig.node_id == node_id)\
            .first()
        
        if not config:
            return 0, {}, "Config not found"
        
        # Find depleting pile
        depleting_pile = self.db.query(StagedPileState)\
            .filter(StagedPileState.staged_config_id == config.config_id)\
            .filter(StagedPileState.state == "Depleting")\
            .first()
        
        if not depleting_pile:
            # Check for Full pile to transition
            full_pile = self.db.query(StagedPileState)\
                .filter(StagedPileState.staged_config_id == config.config_id)\
                .filter(StagedPileState.state == "Full")\
                .first()
            
            if full_pile:
                self._transition_pile(full_pile, "Depleting", "Reclaim started")
                depleting_pile = full_pile
            else:
                return 0, {}, "No pile available for reclaim"
        
        # Reclaim material
        available = depleting_pile.current_tonnes
        reclaim = min(quantity_tonnes, available)
        
        if reclaim <= 0:
            return 0, {}, "No material in pile"
        
        reclaim_quality = depleting_pile.current_quality_vector or {}
        
        # Update pile
        depleting_pile.current_tonnes -= reclaim
        depleting_pile.updated_at = datetime.utcnow()
        
        # Record transaction
        transaction = StagedPileTransaction(
            transaction_id=str(uuid.uuid4()),
            pile_state_id=depleting_pile.state_id,
            transaction_type="Reclaim",
            period_id=period_id,
            tonnes=reclaim,
            quality_vector=reclaim_quality,
            pile_tonnes_after=depleting_pile.current_tonnes,
            pile_quality_after=depleting_pile.current_quality_vector
        )
        self.db.add(transaction)
        
        # Check if empty → transition and start new build
        if depleting_pile.current_tonnes <= 0:
            self._transition_pile(depleting_pile, "Empty", "Pile depleted")
            depleting_pile.current_quality_vector = {}
            depleting_pile.current_build_spec_id = None
            # Try to assign new build spec
            self._assign_next_build_spec(config)
        
        self.db.commit()
        
        return reclaim, reclaim_quality, "Material reclaimed"
    
    # -------------------------------------------------------------------------
    # State Machine
    # -------------------------------------------------------------------------
    
    def _transition_pile(
        self,
        pile: StagedPileState,
        new_state: str,
        reason: str
    ):
        """Transition a pile to a new state."""
        pile.state = new_state
        pile.last_state_change = datetime.utcnow()
        pile.state_change_reason = reason
    
    def _assign_next_build_spec(self, config: StagedStockpileConfig):
        """
        Assign the next pending build spec to an empty pile.
        """
        # Find empty pile
        empty_pile = self.db.query(StagedPileState)\
            .filter(StagedPileState.staged_config_id == config.config_id)\
            .filter(StagedPileState.state == "Empty")\
            .first()
        
        if not empty_pile:
            return  # No empty pile available
        
        # Find next pending build spec
        next_spec = self.db.query(BuildSpec)\
            .filter(BuildSpec.staged_config_id == config.config_id)\
            .filter(BuildSpec.status == "Pending")\
            .order_by(BuildSpec.sequence)\
            .first()
        
        if not next_spec:
            return  # No pending specs
        
        # Assign and transition
        empty_pile.current_build_spec_id = next_spec.spec_id
        next_spec.status = "Active"
        self._transition_pile(empty_pile, "Building", f"Assigned to {next_spec.build_name}")
    
    def start_pile_reclaim(self, node_id: str, pile_index: int) -> Tuple[bool, str]:
        """
        Manually start reclaim on a full pile.
        Transitions pile from Full → Depleting.
        """
        config = self.db.query(StagedStockpileConfig)\
            .filter(StagedStockpileConfig.node_id == node_id)\
            .first()
        
        if not config:
            return False, "Config not found"
        
        pile = self.db.query(StagedPileState)\
            .filter(StagedPileState.staged_config_id == config.config_id)\
            .filter(StagedPileState.pile_index == pile_index)\
            .first()
        
        if not pile:
            return False, "Pile not found"
        
        if pile.state != "Full":
            return False, f"Pile is {pile.state}, not Full"
        
        self._transition_pile(pile, "Depleting", "Manual reclaim started")
        self.db.commit()
        
        return True, "Reclaim started"
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def initialize_pile_states(self, config_id: str, num_piles: int):
        """Create initial pile state records for a config."""
        for i in range(num_piles):
            existing = self.db.query(StagedPileState)\
                .filter(StagedPileState.staged_config_id == config_id)\
                .filter(StagedPileState.pile_index == i)\
                .first()
            
            if not existing:
                pile = StagedPileState(
                    state_id=str(uuid.uuid4()),
                    staged_config_id=config_id,
                    pile_index=i,
                    pile_name=f"Pile {i + 1}",
                    state="Empty",
                    current_tonnes=0.0,
                    current_quality_vector={}
                )
                self.db.add(pile)
        
        self.db.commit()
