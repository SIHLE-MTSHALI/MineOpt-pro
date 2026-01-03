"""
Stockpile Service - Section 3.11 of Enterprise Specification

Comprehensive stockpile management providing:
- Multiple reclaim methods (FIFO, LIFO, BlendedProportional)
- Parcel-tracked inventory
- Inventory balance tracking per period
- Capacity constraint enforcement
- Integration with quality blending
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..domain.models_flow import FlowNode, StockpileConfig
from ..domain.models_parcel import Parcel
from ..domain.models_schedule_results import InventoryBalance
from ..services.quality_service import QualityService, quality_service


@dataclass
class ReclaimResult:
    """Result of a reclaim operation."""
    reclaimed_tonnes: float
    reclaimed_quality: Dict[str, float]
    remaining_tonnes: float
    remaining_quality: Dict[str, float]
    parcels_used: List[str]  # Parcel IDs if parcel-tracked
    warnings: List[str]


@dataclass
class StockpileState:
    """Current state of a stockpile."""
    node_id: str
    name: str
    current_tonnes: float
    current_quality: Dict[str, float]
    capacity_tonnes: Optional[float]
    utilization_percent: float
    parcel_count: int
    inventory_method: str


@dataclass
class BalanceRecord:
    """Inventory balance for a period."""
    period_id: str
    opening_tonnes: float
    additions_tonnes: float
    reclaim_tonnes: float
    closing_tonnes: float
    closing_quality: Dict[str, float]


class StockpileService:
    """
    Comprehensive stockpile management service.
    
    Supports:
    - FIFO/LIFO/Proportional reclaim methods
    - Parcel-tracked and aggregate inventory
    - Capacity constraints
    - Period-by-period balance tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # -------------------------------------------------------------------------
    # Stockpile State
    # -------------------------------------------------------------------------
    
    def get_stockpile_state(self, node_id: str) -> Optional[StockpileState]:
        """Get the current state of a stockpile."""
        node = self.db.query(FlowNode)\
            .filter(FlowNode.node_id == node_id)\
            .first()
        
        if not node or node.node_type not in ["Stockpile", "StagedStockpile"]:
            return None
        
        config = node.stockpile_config
        if not config:
            return StockpileState(
                node_id=node_id,
                name=node.name,
                current_tonnes=0.0,
                current_quality={},
                capacity_tonnes=node.capacity_tonnes,
                utilization_percent=0.0,
                parcel_count=0,
                inventory_method="Aggregate"
            )
        
        capacity = config.max_capacity_tonnes or node.capacity_tonnes
        current = config.current_inventory_tonnes or 0.0
        utilization = (current / capacity * 100) if capacity and capacity > 0 else 0.0
        
        # Count parcels if parcel-tracked
        parcel_count = 0
        if config.inventory_method == "ParcelTracked":
            parcel_ids = config.parcel_ids or []
            parcel_count = len(parcel_ids)
        
        return StockpileState(
            node_id=node_id,
            name=node.name,
            current_tonnes=current,
            current_quality=config.current_grade_vector or {},
            capacity_tonnes=capacity,
            utilization_percent=round(utilization, 1),
            parcel_count=parcel_count,
            inventory_method=config.inventory_method or "Aggregate"
        )
    
    # -------------------------------------------------------------------------
    # Dump Material
    # -------------------------------------------------------------------------
    
    def dump_material(
        self,
        node_id: str,
        quantity_tonnes: float,
        quality_vector: Dict[str, float],
        source_reference: str = None,
        period_id: str = None,
        create_parcel: bool = False
    ) -> Tuple[bool, str, Dict]:
        """
        Deposit material onto a stockpile.
        
        Args:
            node_id: Target stockpile node
            quantity_tonnes: Amount to deposit
            quality_vector: Quality of material
            source_reference: Optional source tracking
            period_id: Scheduling period context
            create_parcel: Whether to create a parcel record
            
        Returns:
            Tuple of (success, message, updated_state)
        """
        node = self.db.query(FlowNode)\
            .filter(FlowNode.node_id == node_id)\
            .first()
        
        if not node:
            return False, "Stockpile not found", {}
        
        config = node.stockpile_config
        if not config:
            # Auto-create config
            config = StockpileConfig(
                config_id=str(uuid.uuid4()),
                node_id=node_id,
                inventory_method="Aggregate"
            )
            self.db.add(config)
            self.db.flush()
        
        # Check capacity
        current = config.current_inventory_tonnes or 0.0
        capacity = config.max_capacity_tonnes
        
        if capacity and (current + quantity_tonnes) > capacity:
            overflow = (current + quantity_tonnes) - capacity
            return False, f"Capacity exceeded by {overflow:.0f}t", {}
        
        # Calculate new blended quality
        new_quality = quality_service.calculate_incremental_blend(
            config.current_grade_vector or {},
            current,
            quality_vector,
            quantity_tonnes
        )
        
        # Update state
        config.current_inventory_tonnes = current + quantity_tonnes
        config.current_grade_vector = new_quality
        
        # Create parcel if tracked
        if create_parcel or config.inventory_method == "ParcelTracked":
            parcel = Parcel(
                parcel_id=str(uuid.uuid4()),
                source_reference=source_reference or f"dump:{node_id}",
                period_available_from=period_id,
                quantity_tonnes=quantity_tonnes,
                quality_vector=quality_vector,
                status="InStockpile",
                current_location_node_id=node_id,
                created_at=datetime.utcnow()
            )
            self.db.add(parcel)
            
            # Track parcel ID
            parcel_ids = config.parcel_ids or []
            parcel_ids.append(parcel.parcel_id)
            config.parcel_ids = parcel_ids
        
        self.db.commit()
        
        return True, "Material deposited", {
            "node_id": node_id,
            "current_tonnes": config.current_inventory_tonnes,
            "current_quality": config.current_grade_vector
        }
    
    # -------------------------------------------------------------------------
    # Reclaim Material
    # -------------------------------------------------------------------------
    
    def reclaim_material(
        self,
        node_id: str,
        quantity_tonnes: float,
        reclaim_method: str = "FIFO",
        period_id: str = None
    ) -> ReclaimResult:
        """
        Reclaim material from a stockpile.
        
        Args:
            node_id: Source stockpile node
            quantity_tonnes: Amount to reclaim
            reclaim_method: FIFO, LIFO, or BlendedProportional
            period_id: Scheduling period context
            
        Returns:
            ReclaimResult with reclaimed quality and updated state
        """
        node = self.db.query(FlowNode)\
            .filter(FlowNode.node_id == node_id)\
            .first()
        
        if not node:
            return ReclaimResult(
                reclaimed_tonnes=0,
                reclaimed_quality={},
                remaining_tonnes=0,
                remaining_quality={},
                parcels_used=[],
                warnings=["Stockpile not found"]
            )
        
        config = node.stockpile_config
        if not config:
            return ReclaimResult(
                reclaimed_tonnes=0,
                reclaimed_quality={},
                remaining_tonnes=0,
                remaining_quality={},
                parcels_used=[],
                warnings=["No stockpile configuration"]
            )
        
        current = config.current_inventory_tonnes or 0.0
        current_quality = config.current_grade_vector or {}
        
        # Check availability
        if quantity_tonnes > current:
            quantity_tonnes = current  # Reclaim all available
        
        if quantity_tonnes <= 0:
            return ReclaimResult(
                reclaimed_tonnes=0,
                reclaimed_quality={},
                remaining_tonnes=current,
                remaining_quality=current_quality,
                parcels_used=[],
                warnings=["No inventory available"]
            )
        
        # Choose reclaim method
        if config.inventory_method == "ParcelTracked":
            result = self._reclaim_parcel_tracked(
                config, quantity_tonnes, reclaim_method
            )
        else:
            result = self._reclaim_aggregate(
                config, quantity_tonnes, current, current_quality
            )
        
        self.db.commit()
        return result
    
    def _reclaim_aggregate(
        self,
        config: StockpileConfig,
        quantity: float,
        current: float,
        current_quality: Dict[str, float]
    ) -> ReclaimResult:
        """Reclaim from aggregate (non-parcel-tracked) stockpile."""
        # For aggregate, reclaimed quality = current quality
        reclaimed_quality = current_quality.copy()
        
        remaining = current - quantity
        
        # Update config
        config.current_inventory_tonnes = remaining
        # Quality stays the same for aggregate stockpiles
        
        return ReclaimResult(
            reclaimed_tonnes=quantity,
            reclaimed_quality=reclaimed_quality,
            remaining_tonnes=remaining,
            remaining_quality=config.current_grade_vector or {},
            parcels_used=[],
            warnings=[]
        )
    
    def _reclaim_parcel_tracked(
        self,
        config: StockpileConfig,
        quantity: float,
        method: str
    ) -> ReclaimResult:
        """Reclaim from parcel-tracked stockpile."""
        parcel_ids = config.parcel_ids or []
        
        if not parcel_ids:
            return ReclaimResult(
                reclaimed_tonnes=0,
                reclaimed_quality={},
                remaining_tonnes=config.current_inventory_tonnes or 0,
                remaining_quality=config.current_grade_vector or {},
                parcels_used=[],
                warnings=["No parcels in stockpile"]
            )
        
        # Fetch parcels
        parcels = self.db.query(Parcel)\
            .filter(Parcel.parcel_id.in_(parcel_ids))\
            .all()
        
        # Sort based on method
        if method == "LIFO":
            parcels.sort(key=lambda p: p.created_at or datetime.min, reverse=True)
        elif method == "FIFO":
            parcels.sort(key=lambda p: p.created_at or datetime.min)
        # BlendedProportional takes proportionally from all
        
        reclaimed_parcels = []
        reclaimed_sources = []
        remaining_to_reclaim = quantity
        
        if method == "BlendedProportional":
            # Take proportionally from all parcels
            total_available = sum(p.quantity_tonnes for p in parcels)
            if total_available > 0:
                ratio = min(quantity / total_available, 1.0)
                
                for parcel in parcels:
                    take = parcel.quantity_tonnes * ratio
                    reclaimed_parcels.append({
                        'quantity_tonnes': take,
                        'quality_vector': parcel.quality_vector or {}
                    })
                    reclaimed_sources.append(parcel.parcel_id)
                    parcel.quantity_tonnes -= take
                    
                    # Remove empty parcels
                    if parcel.quantity_tonnes <= 0:
                        parcel_ids.remove(parcel.parcel_id)
                        self.db.delete(parcel)
        else:
            # FIFO or LIFO - take from sorted order
            for parcel in parcels:
                if remaining_to_reclaim <= 0:
                    break
                
                available = parcel.quantity_tonnes
                take = min(available, remaining_to_reclaim)
                
                reclaimed_parcels.append({
                    'quantity_tonnes': take,
                    'quality_vector': parcel.quality_vector or {}
                })
                reclaimed_sources.append(parcel.parcel_id)
                
                remaining_to_reclaim -= take
                parcel.quantity_tonnes -= take
                
                # Remove empty parcels
                if parcel.quantity_tonnes <= 0:
                    if parcel.parcel_id in parcel_ids:
                        parcel_ids.remove(parcel.parcel_id)
                    self.db.delete(parcel)
        
        # Calculate blended quality of reclaimed material
        if reclaimed_parcels:
            blend_result = quality_service.calculate_blend_quality(reclaimed_parcels)
            reclaimed_quality = blend_result.quality_vector
            reclaimed_tonnes = blend_result.total_tonnes
        else:
            reclaimed_quality = {}
            reclaimed_tonnes = 0
        
        # Update config
        config.parcel_ids = parcel_ids
        config.current_inventory_tonnes = sum(
            p.quantity_tonnes for p in parcels if p.parcel_id in parcel_ids
        )
        
        # Recalculate remaining quality
        remaining_parcels = [p for p in parcels if p.parcel_id in parcel_ids]
        if remaining_parcels:
            remaining_sources = [{
                'quantity_tonnes': p.quantity_tonnes,
                'quality_vector': p.quality_vector or {}
            } for p in remaining_parcels]
            remaining_blend = quality_service.calculate_blend_quality(remaining_sources)
            config.current_grade_vector = remaining_blend.quality_vector
        else:
            config.current_grade_vector = {}
        
        return ReclaimResult(
            reclaimed_tonnes=reclaimed_tonnes,
            reclaimed_quality=reclaimed_quality,
            remaining_tonnes=config.current_inventory_tonnes,
            remaining_quality=config.current_grade_vector,
            parcels_used=reclaimed_sources,
            warnings=[]
        )
    
    # -------------------------------------------------------------------------
    # Inventory Balance Tracking
    # -------------------------------------------------------------------------
    
    def create_balance_record(
        self,
        schedule_version_id: str,
        period_id: str,
        node_id: str,
        opening_tonnes: float,
        additions_tonnes: float,
        reclaim_tonnes: float,
        closing_quality: Dict[str, float]
    ) -> InventoryBalance:
        """Create an inventory balance record for a period."""
        closing_tonnes = opening_tonnes + additions_tonnes - reclaim_tonnes
        
        balance = InventoryBalance(
            balance_id=str(uuid.uuid4()),
            schedule_version_id=schedule_version_id,
            period_id=period_id,
            node_id=node_id,
            opening_tonnes=opening_tonnes,
            additions_tonnes=additions_tonnes,
            reclaim_tonnes=reclaim_tonnes,
            closing_tonnes=max(0, closing_tonnes),
            closing_quality_vector=closing_quality
        )
        self.db.add(balance)
        return balance
    
    def get_balance_history(
        self,
        schedule_version_id: str,
        node_id: str
    ) -> List[BalanceRecord]:
        """Get inventory balance history for a stockpile."""
        balances = self.db.query(InventoryBalance)\
            .filter(InventoryBalance.schedule_version_id == schedule_version_id)\
            .filter(InventoryBalance.node_id == node_id)\
            .order_by(InventoryBalance.period_id)\
            .all()
        
        return [
            BalanceRecord(
                period_id=b.period_id,
                opening_tonnes=b.opening_tonnes,
                additions_tonnes=b.additions_tonnes,
                reclaim_tonnes=b.reclaim_tonnes,
                closing_tonnes=b.closing_tonnes,
                closing_quality=b.closing_quality_vector or {}
            )
            for b in balances
        ]
    
    def calculate_period_balance(
        self,
        schedule_version_id: str,
        period_id: str,
        node_id: str
    ) -> BalanceRecord:
        """Calculate balance for a specific period based on movements."""
        from ..domain.models_schedule_results import FlowResult
        
        # Get previous period closing as opening
        prev_balance = self.db.query(InventoryBalance)\
            .filter(InventoryBalance.schedule_version_id == schedule_version_id)\
            .filter(InventoryBalance.node_id == node_id)\
            .filter(InventoryBalance.period_id < period_id)\
            .order_by(InventoryBalance.period_id.desc())\
            .first()
        
        opening = prev_balance.closing_tonnes if prev_balance else 0.0
        
        # Sum additions (flows TO this node)
        additions = self.db.query(FlowResult)\
            .filter(FlowResult.schedule_version_id == schedule_version_id)\
            .filter(FlowResult.period_id == period_id)\
            .filter(FlowResult.to_node_id == node_id)\
            .all()
        additions_tonnes = sum(f.tonnes for f in additions)
        
        # Sum reclaims (flows FROM this node)
        reclaims = self.db.query(FlowResult)\
            .filter(FlowResult.schedule_version_id == schedule_version_id)\
            .filter(FlowResult.period_id == period_id)\
            .filter(FlowResult.from_node_id == node_id)\
            .all()
        reclaim_tonnes = sum(f.tonnes for f in reclaims)
        
        closing = opening + additions_tonnes - reclaim_tonnes
        
        # Get current quality from stockpile
        state = self.get_stockpile_state(node_id)
        closing_quality = state.current_quality if state else {}
        
        return BalanceRecord(
            period_id=period_id,
            opening_tonnes=opening,
            additions_tonnes=additions_tonnes,
            reclaim_tonnes=reclaim_tonnes,
            closing_tonnes=max(0, closing),
            closing_quality=closing_quality
        )
    
    # -------------------------------------------------------------------------
    # Capacity Enforcement
    # -------------------------------------------------------------------------
    
    def check_capacity(
        self,
        node_id: str,
        additional_tonnes: float
    ) -> Tuple[bool, float]:
        """
        Check if stockpile can accept additional material.
        
        Returns:
            Tuple of (can_accept, available_capacity)
        """
        state = self.get_stockpile_state(node_id)
        if not state:
            return False, 0.0
        
        if not state.capacity_tonnes:
            # No capacity limit
            return True, float('inf')
        
        available = state.capacity_tonnes - state.current_tonnes
        can_accept = additional_tonnes <= available
        
        return can_accept, max(0, available)
    
    def get_utilization(self, node_id: str) -> float:
        """Get current capacity utilization percentage."""
        state = self.get_stockpile_state(node_id)
        return state.utilization_percent if state else 0.0
