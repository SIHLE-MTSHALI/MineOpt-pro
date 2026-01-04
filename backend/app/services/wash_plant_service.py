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
    
    # -------------------------------------------------------------------------
    # Multi-Stage Processing
    # -------------------------------------------------------------------------
    
    def process_multi_stage(
        self,
        node_id: str,
        feed_tonnes: float,
        feed_quality: Dict[str, float],
        stage_configs: List[Dict] = None,
        period_id: str = None,
        schedule_version_id: str = None
    ) -> Dict:
        """
        Process material through multiple wash stages.
        
        Stage 2 can process either:
        - Reject from stage 1 (reject_to_stage_2: true)
        - Product from stage 1 for further cleaning
        
        Returns combined result with stage-by-stage breakdown.
        """
        if not stage_configs:
            # Default 2-stage config: main plant + reject reprocessing
            stage_configs = [
                {'stage': 1, 'table_id': 'primary', 'mode': 'FixedRD', 'cutpoint_rd': 1.5},
                {'stage': 2, 'table_id': 'secondary', 'mode': 'FixedRD', 'cutpoint_rd': 1.7, 
                 'feed_from_reject': True}
            ]
        
        stages = []
        current_product = 0.0
        current_product_quality = {}
        total_reject = 0.0
        total_reject_quality = {}
        
        # Stage 1 - Primary processing
        stage1 = stage_configs[0] if stage_configs else {}
        s1_result = self._process_single_stage(
            table_id=stage1.get('table_id'),
            feed_tonnes=feed_tonnes,
            feed_quality=feed_quality,
            mode=stage1.get('mode', 'FixedRD'),
            cutpoint_rd=stage1.get('cutpoint_rd', 1.5),
            target_field=stage1.get('target_field'),
            target_value=stage1.get('target_value'),
            target_type=stage1.get('target_type')
        )
        
        stages.append({
            'stage': 1,
            'feed_tonnes': feed_tonnes,
            'product_tonnes': s1_result.product_tonnes,
            'reject_tonnes': s1_result.reject_tonnes,
            'yield': s1_result.yield_fraction,
            'cutpoint_rd': s1_result.cutpoint_rd,
            'product_quality': s1_result.product_quality
        })
        
        current_product = s1_result.product_tonnes
        current_product_quality = s1_result.product_quality
        stage1_reject_tonnes = s1_result.reject_tonnes
        stage1_reject_quality = s1_result.reject_quality
        
        # Stage 2 - Secondary processing (if configured)
        if len(stage_configs) > 1:
            stage2 = stage_configs[1]
            
            # Determine stage 2 feed
            if stage2.get('feed_from_reject', False):
                # Process reject from stage 1
                s2_feed = stage1_reject_tonnes
                s2_feed_quality = stage1_reject_quality
            else:
                # Further clean product from stage 1
                s2_feed = s1_result.product_tonnes
                s2_feed_quality = s1_result.product_quality
            
            if s2_feed > 0:
                s2_result = self._process_single_stage(
                    table_id=stage2.get('table_id'),
                    feed_tonnes=s2_feed,
                    feed_quality=s2_feed_quality,
                    mode=stage2.get('mode', 'FixedRD'),
                    cutpoint_rd=stage2.get('cutpoint_rd', 1.7),
                    target_field=stage2.get('target_field'),
                    target_value=stage2.get('target_value'),
                    target_type=stage2.get('target_type')
                )
                
                stages.append({
                    'stage': 2,
                    'feed_tonnes': s2_feed,
                    'product_tonnes': s2_result.product_tonnes,
                    'reject_tonnes': s2_result.reject_tonnes,
                    'yield': s2_result.yield_fraction,
                    'cutpoint_rd': s2_result.cutpoint_rd,
                    'product_quality': s2_result.product_quality
                })
                
                if stage2.get('feed_from_reject', False):
                    # Stage 2 product adds to stage 1 product
                    total_product = current_product + s2_result.product_tonnes
                    total_product_quality = self._blend_qualities(
                        current_product_quality, current_product,
                        s2_result.product_quality, s2_result.product_tonnes
                    )
                    total_reject = s2_result.reject_tonnes
                else:
                    # Stage 2 replaces stage 1 product
                    total_product = s2_result.product_tonnes
                    total_product_quality = s2_result.product_quality
                    total_reject = stage1_reject_tonnes + s2_result.reject_tonnes
                
                current_product = total_product
                current_product_quality = total_product_quality
        else:
            total_reject = stage1_reject_tonnes
        
        overall_yield = current_product / feed_tonnes if feed_tonnes > 0 else 0
        
        return {
            'feed_tonnes': feed_tonnes,
            'feed_quality': feed_quality,
            'final_product_tonnes': current_product,
            'final_product_quality': current_product_quality,
            'final_reject_tonnes': total_reject,
            'overall_yield': overall_yield,
            'stages': stages,
            'num_stages': len(stages)
        }
    
    def _process_single_stage(
        self,
        table_id: str,
        feed_tonnes: float,
        feed_quality: Dict[str, float],
        mode: str = 'FixedRD',
        cutpoint_rd: float = 1.5,
        target_field: str = None,
        target_value: float = None,
        target_type: str = None
    ) -> WashResult:
        """Process a single wash stage."""
        if not table_id or not self.db:
            # Use simplified model
            yield_frac, prod_qual = self.calculate_yield_and_quality(
                feed_quality, 12.0, 0.95
            )
            return WashResult(
                cutpoint_rd=cutpoint_rd,
                yield_fraction=yield_frac,
                product_tonnes=feed_tonnes * yield_frac,
                reject_tonnes=feed_tonnes * (1 - yield_frac),
                product_quality=prod_qual,
                reject_quality=feed_quality,
                selection_mode=mode,
                rationale="Simplified model"
            )
        
        if mode == 'TargetQuality' and target_field:
            return self.select_cutpoint_target_quality(
                table_id, target_field, target_value or 14.0,
                target_type or 'Max', feed_tonnes
            )
        else:
            return self.select_cutpoint_fixed(
                table_id, cutpoint_rd, feed_tonnes, feed_quality
            )
    
    def _blend_qualities(
        self,
        q1: Dict[str, float], t1: float,
        q2: Dict[str, float], t2: float
    ) -> Dict[str, float]:
        """Blend two quality vectors by tonnage weight."""
        total = t1 + t2
        if total <= 0:
            return {}
        
        blended = {}
        all_fields = set(q1.keys()) | set(q2.keys())
        for field in all_fields:
            v1 = q1.get(field, 0) * t1
            v2 = q2.get(field, 0) * t2
            blended[field] = (v1 + v2) / total
        return blended
    
    # -------------------------------------------------------------------------
    # Yield Adjustment Model
    # -------------------------------------------------------------------------
    
    def apply_yield_adjustment(
        self,
        theoretical_yield: float,
        misplacement_model: Dict = None,
        efficiency_factor: float = 0.95,
        historical_correction: float = 1.0
    ) -> float:
        """
        Apply yield adjustments for real-world conditions.
        
        Args:
            theoretical_yield: Yield from wash table interpolation
            misplacement_model: Configuration for misplacement calculation
                - near_gravity_factor: Extra loss for material near cutpoint RD
                - fines_factor: Loss due to fine coal in reject
            efficiency_factor: Overall plant efficiency (0-1)
            historical_correction: Calibration from actual vs predicted history
        
        Returns:
            Adjusted yield fraction
        """
        base_yield = theoretical_yield * efficiency_factor
        
        if misplacement_model:
            # Near-gravity misplacement (more loss for material close to cutpoint)
            ngf = misplacement_model.get('near_gravity_factor', 0.02)
            fines = misplacement_model.get('fines_factor', 0.01)
            
            # Apply losses
            base_yield *= (1 - ngf - fines)
        
        # Apply historical calibration
        adjusted_yield = base_yield * historical_correction
        
        return max(0.0, min(1.0, adjusted_yield))
    
    def calibrate_from_history(
        self,
        node_id: str,
        lookback_points: int = 10
    ) -> float:
        """
        Calculate historical correction factor from actual vs predicted.
        
        Returns ratio of actual/predicted yields from recent operating points.
        """
        if not self.db:
            return 1.0
        
        # Get recent operating points
        recent = self.db.query(WashPlantOperatingPoint)\
            .filter(WashPlantOperatingPoint.wash_plant_node_id == node_id)\
            .order_by(WashPlantOperatingPoint.period_id.desc())\
            .limit(lookback_points)\
            .all()
        
        if len(recent) < 3:
            return 1.0  # Not enough data
        
        # Compare predicted vs actual (would need actual yield tracking)
        # For now return 1.0 as placeholder
        return 1.0
    
    # -------------------------------------------------------------------------
    # Period-by-Period Cutpoint Optimization
    # -------------------------------------------------------------------------
    
    def optimize_cutpoints_for_schedule(
        self,
        node_id: str,
        period_feeds: List[Dict],
        product_price: float,
        reject_cost: float = 0.0,
        quality_penalties: List[Dict] = None,
        constraint_cv_min: float = None,
        constraint_ash_max: float = None
    ) -> List[Dict]:
        """
        Optimize cutpoint selection across multiple periods.
        
        Considers cumulative quality requirements - may accept lower
        yield in one period to maintain overall quality.
        
        Args:
            period_feeds: List of {period_id, feed_tonnes, feed_quality}
            product_price: $/tonne for product
            reject_cost: $/tonne disposal cost
            quality_penalties: Penalty structure for quality deviations
            constraint_cv_min: Minimum CV constraint (cumulative)
            constraint_ash_max: Maximum Ash constraint (cumulative)
        
        Returns:
            Optimized cutpoint plan per period
        """
        if not self.db:
            return []
        
        config = self.db.query(models_flow.WashPlantConfig)\
            .filter(models_flow.WashPlantConfig.node_id == node_id).first()
        
        if not config or not config.wash_table_id:
            return []
        
        results = []
        cumulative_product = 0.0
        cumulative_quality = {}
        
        for pf in period_feeds:
            period_id = pf.get('period_id')
            feed_tonnes = pf.get('feed_tonnes', 0)
            feed_quality = pf.get('feed_quality', {})
            
            if feed_tonnes <= 0:
                continue
            
            # Run optimizer for this period
            result, analysis = self.select_cutpoint_optimizer(
                config.wash_table_id,
                feed_tonnes,
                product_price,
                reject_cost,
                quality_penalties
            )
            
            # Check if cumulative quality constraints would be violated
            if constraint_ash_max or constraint_cv_min:
                new_cumulative = cumulative_product + result.product_tonnes
                new_quality = self._blend_qualities(
                    cumulative_quality, cumulative_product,
                    result.product_quality, result.product_tonnes
                )
                
                # Adjust if constraints violated
                needs_adjustment = False
                if constraint_ash_max and new_quality.get('Ash_ADB', 0) > constraint_ash_max:
                    needs_adjustment = True
                if constraint_cv_min and new_quality.get('CV_ARB', 0) < constraint_cv_min:
                    needs_adjustment = True
                
                if needs_adjustment:
                    # Re-optimize with quality target mode
                    if constraint_ash_max:
                        result = self.select_cutpoint_target_quality(
                            config.wash_table_id, 'Ash_ADB', 
                            constraint_ash_max * 0.95, 'Max', feed_tonnes
                        )
            
            cumulative_product += result.product_tonnes
            cumulative_quality = self._blend_qualities(
                cumulative_quality, cumulative_product - result.product_tonnes,
                result.product_quality, result.product_tonnes
            )
            
            results.append({
                'period_id': period_id,
                'recommended_cutpoint': result.cutpoint_rd,
                'expected_yield': result.yield_fraction,
                'expected_product_tonnes': result.product_tonnes,
                'expected_product_quality': result.product_quality,
                'rationale': result.rationale,
                'cumulative_product': cumulative_product,
                'cumulative_quality': cumulative_quality
            })
        
        return results


# Singleton for simple use cases
wash_plant_service = WashPlantService()

