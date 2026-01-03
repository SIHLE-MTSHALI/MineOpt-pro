"""
Wash Plant Service - Section 3.13 of Enterprise Specification

Coal Handling and Preparation Plant (CHPP) integration providing:
- Wash table interpolation for yield and quality prediction
- Cutpoint selection modes (Fixed RD, Target Quality, Optimizer)
- Feed → Product quality transformation
- Multi-stage washing support
"""

from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..domain import models_flow
from ..domain.models_wash_table import WashTable, WashTableRow, WashPlantOperatingPoint


@dataclass
class WashResult:
    """Result of washing material at a given cutpoint."""
    cutpoint_rd: float
    yield_fraction: float
    product_tonnes: float
    reject_tonnes: float
    product_quality: Dict[str, float]
    reject_quality: Dict[str, float]
    selection_mode: str
    rationale: str


@dataclass
class CutpointAnalysis:
    """Analysis of different cutpoint options."""
    optimal_cutpoint: float
    analyses: List[Dict]
    selection_rationale: str


@dataclass
class PlantThroughputResult:
    """Result of processing material through the plant."""
    feed_tonnes: float
    product_tonnes: float
    reject_tonnes: float
    feed_quality: Dict[str, float]
    product_quality: Dict[str, float]
    reject_quality: Dict[str, float]


class WashPlantService:
    """
    Manages coal washing operations and cutpoint selection.
    
    Cutpoint Selection Modes:
    - FixedRD: Use a predetermined RD cutpoint
    - TargetQuality: Find RD that achieves target quality
    - OptimizerSelected: Choose RD based on cost/benefit analysis
    """
    
    def __init__(self, db: Session = None):
        self.db = db
    
    # -------------------------------------------------------------------------
    # Legacy Static Methods (backwards compatible)
    # -------------------------------------------------------------------------
    
    @staticmethod
    def calculate_yield_and_quality(
        feed_quality: Dict[str, float],
        target_ash: float,
        efficiency_factor: float = 0.95
    ) -> Tuple[float, Dict[str, float]]:
        """
        Simulates a wash run using simplified model.
        Returns (Yield_Fraction, Product_Quality_Vector).
        """
        feed_ash = feed_quality.get("Ash_ADB", 25.0)
        feed_cv = feed_quality.get("CV_ARB", 20.0)
        
        if feed_ash <= target_ash:
            return 1.0, feed_quality
            
        ash_reduction = feed_ash - target_ash
        yield_loss_pct = ash_reduction * 1.5
        theoretical_yield = (100.0 - yield_loss_pct) / 100.0
        actual_yield = max(0.0, theoretical_yield * efficiency_factor)
        
        cv_upgrade = ash_reduction * 0.8
        product_cv = feed_cv + cv_upgrade
        
        product_quality = {
            "Ash_ADB": target_ash,
            "CV_ARB": product_cv,
        }
        
        return actual_yield, product_quality

    @staticmethod
    def process_batch(
        plant_config: models_flow.WashPlantConfig,
        feed_force_tonnes: float,
        feed_quality: Dict[str, float]
    ) -> Dict:
        """Runs a batch through the plant (legacy method)."""
        target_ash = 10.0
        if plant_config.cutpoint_selection_mode == "TargetQuality":
            target_ash = 12.0
            
        yield_frac, prod_qual = WashPlantService.calculate_yield_and_quality(
            feed_quality, target_ash, 
            efficiency_factor=plant_config.yield_adjustment_factor or 1.0
        )
        
        product_tonnes = feed_force_tonnes * yield_frac
        reject_tonnes = feed_force_tonnes - product_tonnes
        
        return {
            "input_tonnes": feed_force_tonnes,
            "yield_fraction": yield_frac,
            "product_tonnes": product_tonnes,
            "product_quality": prod_qual,
            "reject_tonnes": reject_tonnes
        }
    
    # -------------------------------------------------------------------------
    # Wash Table Operations
    # -------------------------------------------------------------------------
    
    def get_wash_table(self, table_id: str) -> Optional[WashTable]:
        """Get a wash table by ID."""
        if not self.db:
            return None
        return self.db.query(WashTable)\
            .filter(WashTable.table_id == table_id)\
            .first()
    
    def interpolate_wash_table(
        self,
        table_id: str,
        rd_cutpoint: float
    ) -> Tuple[float, Dict[str, float], Dict[str, float]]:
        """Interpolate wash table for yield and qualities at RD."""
        table = self.get_wash_table(table_id)
        if not table:
            return 0.0, {}, {}
        return table.get_yield_at_rd(rd_cutpoint)
    
    # -------------------------------------------------------------------------
    # Cutpoint Selection: Fixed RD
    # -------------------------------------------------------------------------
    
    def select_cutpoint_fixed(
        self,
        table_id: str,
        fixed_rd: float,
        feed_tonnes: float,
        feed_quality: Dict[str, float]
    ) -> WashResult:
        """Fixed RD mode - use predetermined cutpoint."""
        yield_frac, prod_quality, reject_quality = self.interpolate_wash_table(
            table_id, fixed_rd
        )
        
        product_tonnes = feed_tonnes * yield_frac
        reject_tonnes = feed_tonnes * (1 - yield_frac)
        
        return WashResult(
            cutpoint_rd=fixed_rd,
            yield_fraction=yield_frac,
            product_tonnes=product_tonnes,
            reject_tonnes=reject_tonnes,
            product_quality=prod_quality,
            reject_quality=reject_quality,
            selection_mode="FixedRD",
            rationale=f"Fixed cutpoint at RD {fixed_rd:.2f}"
        )
    
    # -------------------------------------------------------------------------
    # Cutpoint Selection: Target Quality
    # -------------------------------------------------------------------------
    
    def select_cutpoint_target_quality(
        self,
        table_id: str,
        target_field: str,
        target_value: float,
        target_type: str,  # "Max", "Min", "Target"
        feed_tonnes: float,
        rd_min: float = 1.3,
        rd_max: float = 2.0,
        rd_step: float = 0.01
    ) -> WashResult:
        """
        Target Quality mode - find RD that achieves target quality.
        
        For Max: Find highest yield where quality <= target
        For Min: Find highest yield where quality >= target
        """
        table = self.get_wash_table(table_id)
        if not table:
            return WashResult(
                cutpoint_rd=0, yield_fraction=0, product_tonnes=0,
                reject_tonnes=feed_tonnes, product_quality={},
                reject_quality={}, selection_mode="TargetQuality",
                rationale="Wash table not found"
            )
        
        best_rd = rd_min
        best_yield = 0.0
        best_quality = {}
        best_deviation = float('inf')
        
        rd = rd_min
        while rd <= rd_max:
            yield_frac, prod_quality, _ = table.get_yield_at_rd(rd)
            
            if target_field not in prod_quality:
                rd += rd_step
                continue
            
            quality_val = prod_quality[target_field]
            
            if target_type == "Max" and quality_val <= target_value:
                if yield_frac > best_yield:
                    best_rd, best_yield, best_quality = rd, yield_frac, prod_quality
            elif target_type == "Min" and quality_val >= target_value:
                if yield_frac > best_yield:
                    best_rd, best_yield, best_quality = rd, yield_frac, prod_quality
            else:
                deviation = abs(quality_val - target_value)
                if deviation < best_deviation:
                    best_rd, best_yield, best_quality = rd, yield_frac, prod_quality
                    best_deviation = deviation
            
            rd += rd_step
        
        _, _, reject_quality = table.get_yield_at_rd(best_rd)
        
        return WashResult(
            cutpoint_rd=best_rd,
            yield_fraction=best_yield,
            product_tonnes=feed_tonnes * best_yield,
            reject_tonnes=feed_tonnes * (1 - best_yield),
            product_quality=best_quality,
            reject_quality=reject_quality,
            selection_mode="TargetQuality",
            rationale=f"RD {best_rd:.2f} for {target_field} {target_type} {target_value}"
        )
    
    # -------------------------------------------------------------------------
    # Cutpoint Selection: Optimizer
    # -------------------------------------------------------------------------
    
    def select_cutpoint_optimizer(
        self,
        table_id: str,
        feed_tonnes: float,
        product_price: float,
        reject_cost: float = 0.0,
        quality_penalties: List[Dict] = None,
        rd_min: float = 1.3,
        rd_max: float = 2.0,
        rd_step: float = 0.02
    ) -> Tuple[WashResult, CutpointAnalysis]:
        """
        Optimizer mode - choose RD based on cost/benefit analysis.
        Net Value = Product Revenue - Reject Cost - Quality Penalties
        """
        table = self.get_wash_table(table_id)
        if not table:
            empty = WashResult(0, 0, 0, feed_tonnes, {}, {}, "Optimizer", "No table")
            return empty, CutpointAnalysis(0, [], "No table")
        
        analyses = []
        best_rd, best_net = rd_min, float('-inf')
        best_result = None
        
        rd = rd_min
        while rd <= rd_max:
            yield_frac, prod_qual, reject_qual = table.get_yield_at_rd(rd)
            prod_t = feed_tonnes * yield_frac
            rej_t = feed_tonnes * (1 - yield_frac)
            
            revenue = prod_t * product_price
            rej_cost = rej_t * reject_cost
            
            penalty = 0.0
            if quality_penalties:
                for p in quality_penalties:
                    field = p.get('field')
                    limit = p.get('limit', 0)
                    ltype = p.get('limit_type', 'Max')
                    rate = p.get('penalty_per_unit', 0)
                    if field in prod_qual:
                        val = prod_qual[field]
                        if ltype == 'Max' and val > limit:
                            penalty += (val - limit) * rate * prod_t
                        elif ltype == 'Min' and val < limit:
                            penalty += (limit - val) * rate * prod_t
            
            net = revenue - rej_cost - penalty
            
            analyses.append({
                'rd': round(rd, 3), 'yield': round(yield_frac, 4),
                'product_tonnes': round(prod_t, 1), 'net_value': round(net, 2)
            })
            
            if net > best_net:
                best_net, best_rd = net, rd
                best_result = WashResult(
                    rd, yield_frac, prod_t, rej_t, prod_qual, reject_qual,
                    "OptimizerSelected", f"RD {rd:.2f} net ${net:,.0f}"
                )
            
            rd += rd_step
        
        analysis = CutpointAnalysis(best_rd, analyses, f"Net ${best_net:,.0f}")
        return best_result or WashResult(rd_min, 0, 0, feed_tonnes, {}, {}, "Optimizer", "No valid RD"), analysis
    
    # -------------------------------------------------------------------------
    # Plant Processing
    # -------------------------------------------------------------------------
    
    def process_feed(
        self,
        node_id: str,
        feed_tonnes: float,
        feed_quality: Dict[str, float],
        period_id: str = None,
        schedule_version_id: str = None
    ) -> PlantThroughputResult:
        """Process material through wash plant using configured mode."""
        if not self.db:
            return PlantThroughputResult(feed_tonnes, 0, feed_tonnes, feed_quality, {}, {})
        
        config = self.db.query(models_flow.WashPlantConfig)\
            .filter(models_flow.WashPlantConfig.node_id == node_id).first()
        
        if not config or not config.wash_table_id:
            return PlantThroughputResult(feed_tonnes, 0, feed_tonnes, feed_quality, {}, {})
        
        mode = config.cutpoint_selection_mode or "FixedRD"
        
        if mode == "FixedRD":
            rd = getattr(config, 'default_cutpoint_rd', 1.5) or 1.5
            result = self.select_cutpoint_fixed(config.wash_table_id, rd, feed_tonnes, feed_quality)
        elif mode == "TargetQuality":
            field = getattr(config, 'target_quality_field', 'Ash_ADB') or 'Ash_ADB'
            value = getattr(config, 'target_quality_value', 14.0) or 14.0
            ttype = getattr(config, 'target_quality_type', 'Max') or 'Max'
            result = self.select_cutpoint_target_quality(
                config.wash_table_id, field, value, ttype, feed_tonnes
            )
        else:
            price = getattr(config, 'product_price_per_tonne', 100.0) or 100.0
            cost = getattr(config, 'reject_cost_per_tonne', 5.0) or 5.0
            penalties = getattr(config, 'quality_penalty_config', None)
            result, _ = self.select_cutpoint_optimizer(
                config.wash_table_id, feed_tonnes, price, cost, penalties
            )
        
        # Record operating point if scheduling context provided
        if schedule_version_id and period_id:
            op = WashPlantOperatingPoint(
                operating_point_id=str(uuid.uuid4()),
                schedule_version_id=schedule_version_id,
                period_id=period_id,
                wash_plant_node_id=node_id,
                wash_table_id=config.wash_table_id,
                feed_tonnes=feed_tonnes,
                feed_quality_vector=feed_quality,
                cutpoint_rd=result.cutpoint_rd,
                product_tonnes=result.product_tonnes,
                reject_tonnes=result.reject_tonnes,
                product_quality_vector=result.product_quality,
                reject_quality_vector=result.reject_quality,
                yield_fraction=result.yield_fraction,
                cutpoint_selection_mode=result.selection_mode,
                selection_rationale=result.rationale
            )
            self.db.add(op)
            self.db.commit()
        
        return PlantThroughputResult(
            feed_tonnes, result.product_tonnes, result.reject_tonnes,
            feed_quality, result.product_quality, result.reject_quality
        )


# Singleton for simple use cases
wash_plant_service = WashPlantService()

