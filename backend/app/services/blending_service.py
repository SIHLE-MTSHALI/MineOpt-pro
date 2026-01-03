"""
Blending Service - Section 3.8 of Enterprise Specification

Handles quality blending calculations for material mixing:
- Weighted average quality calculations
- Multi-field aggregation with different rules
- Spec compliance checking with penalty evaluation
- Optimal blend selection for quality targets
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class BlendResult:
    """Result of a blend quality calculation."""
    quality_vector: Dict[str, float]
    total_tonnes: float
    parcel_count: int


@dataclass
class ComplianceResult:
    """Result of a spec compliance check."""
    is_compliant: bool
    violations: List[str]
    total_penalty: float
    field_penalties: Dict[str, float]


class BlendingService:
    """
    Handles quality blending calculations and constraint checking.
    
    Key responsibilities:
    - Calculate blended quality from multiple parcels
    - Evaluate compliance against quality objectives
    - Calculate penalty costs for quality deviations
    - Find optimal blend to meet targets
    """
    
    def calculate_blend_quality(
        self,
        parcels: List[dict],  # List of parcel-like dicts with quality_vector and quantity_tonnes
        quality_fields: List[dict] = None  # Optional field definitions with aggregation rules
    ) -> BlendResult:
        """
        Calculates weighted average quality for a set of parcels.
        
        Args:
            parcels: List of parcels, each with 'quantity_tonnes' and 'quality_vector'
            quality_fields: Optional list of quality field definitions
            
        Returns:
            BlendResult with combined quality vector and totals
        """
        if not parcels:
            return BlendResult(quality_vector={}, total_tonnes=0.0, parcel_count=0)
        
        # Collect all quality fields present
        all_fields = set()
        for p in parcels:
            qv = p.get('quality_vector', {})
            if qv:
                all_fields.update(qv.keys())
        
        # Build field rules map
        field_rules = {}
        if quality_fields:
            for f in quality_fields:
                field_name = f.get('name') or f.get('quality_field_id')
                field_rules[field_name] = f.get('aggregation_rule', 'WeightedAverage')
        
        # Calculate weighted averages and other aggregations
        result = {}
        total_tonnes = 0.0
        
        for field in all_fields:
            rule = field_rules.get(field, 'WeightedAverage')
            
            if rule == 'WeightedAverage':
                # Mass-weighted average
                weighted_sum = 0.0
                total_weight = 0.0
                
                for p in parcels:
                    qv = p.get('quality_vector', {})
                    tonnes = p.get('quantity_tonnes', 0)
                    if field in qv and tonnes > 0:
                        weighted_sum += qv[field] * tonnes
                        total_weight += tonnes
                
                result[field] = weighted_sum / total_weight if total_weight > 0 else 0.0
                
            elif rule == 'Sum':
                # Total sum (e.g., total tonnage)
                result[field] = sum(
                    p.get('quality_vector', {}).get(field, 0) 
                    for p in parcels
                )
                
            elif rule == 'Min':
                # Minimum value (e.g., worst case)
                values = [
                    p.get('quality_vector', {}).get(field, float('inf'))
                    for p in parcels
                    if field in p.get('quality_vector', {})
                ]
                result[field] = min(values) if values else 0.0
                
            elif rule == 'Max':
                # Maximum value
                values = [
                    p.get('quality_vector', {}).get(field, float('-inf'))
                    for p in parcels
                    if field in p.get('quality_vector', {})
                ]
                result[field] = max(values) if values else 0.0
                
            else:
                # Default to weighted average
                weighted_sum = 0.0
                total_weight = 0.0
                for p in parcels:
                    qv = p.get('quality_vector', {})
                    tonnes = p.get('quantity_tonnes', 0)
                    if field in qv and tonnes > 0:
                        weighted_sum += qv[field] * tonnes
                        total_weight += tonnes
                result[field] = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        total_tonnes = sum(p.get('quantity_tonnes', 0) for p in parcels)
        
        return BlendResult(
            quality_vector=result,
            total_tonnes=total_tonnes,
            parcel_count=len(parcels)
        )

    def check_spec_compliance(
        self,
        blend_quality: Dict[str, float],
        objectives: List[dict]  # List of ArcQualityObjective-like dicts
    ) -> ComplianceResult:
        """
        Check if a blend quality meets specification objectives.
        
        Args:
            blend_quality: Quality vector to check
            objectives: List of quality objectives with type, target, min, max, etc.
            
        Returns:
            ComplianceResult with compliance status, violations, and penalties
        """
        violations = []
        field_penalties = {}
        total_penalty = 0.0
        is_compliant = True
        
        for obj in objectives:
            field_id = obj.get('quality_field_id') or obj.get('field')
            if not field_id or field_id not in blend_quality:
                continue
            
            actual_value = blend_quality[field_id]
            obj_type = obj.get('objective_type', 'Range')
            penalty_weight = obj.get('penalty_weight', 1.0)
            hard_constraint = obj.get('hard_constraint', False)
            tolerance = obj.get('tolerance', 0.0)
            
            # Get bounds
            target = obj.get('target_value')
            min_val = obj.get('min_value')
            max_val = obj.get('max_value')
            
            # Check violation
            violation = None
            deviation = 0.0
            
            if obj_type == 'Target' and target is not None:
                deviation = abs(actual_value - target)
                if deviation > tolerance:
                    violation = f"{field_id}: actual {actual_value:.2f} != target {target:.2f}"
                    
            elif obj_type == 'Min' and min_val is not None:
                if actual_value < min_val - tolerance:
                    deviation = min_val - actual_value
                    violation = f"{field_id}: actual {actual_value:.2f} < min {min_val:.2f}"
                    
            elif obj_type == 'Max' and max_val is not None:
                if actual_value > max_val + tolerance:
                    deviation = actual_value - max_val
                    violation = f"{field_id}: actual {actual_value:.2f} > max {max_val:.2f}"
                    
            elif obj_type == 'Range':
                if min_val is not None and actual_value < min_val - tolerance:
                    deviation = min_val - actual_value
                    violation = f"{field_id}: actual {actual_value:.2f} < min {min_val:.2f}"
                elif max_val is not None and actual_value > max_val + tolerance:
                    deviation = actual_value - max_val
                    violation = f"{field_id}: actual {actual_value:.2f} > max {max_val:.2f}"
            
            # Calculate penalty
            if deviation > 0:
                penalty = self._calculate_penalty(deviation, penalty_weight, obj)
                field_penalties[field_id] = penalty
                total_penalty += penalty
                
                if violation:
                    violations.append(violation)
                    
                if hard_constraint:
                    is_compliant = False
        
        return ComplianceResult(
            is_compliant=is_compliant and len(violations) == 0,
            violations=violations,
            total_penalty=total_penalty,
            field_penalties=field_penalties
        )

    def _calculate_penalty(
        self,
        deviation: float,
        weight: float,
        objective: dict
    ) -> float:
        """
        Calculate penalty cost for a quality deviation.
        
        Supports penalty function types:
        - Linear: penalty = weight * deviation
        - Quadratic: penalty = weight * deviation^2
        - Step: penalty = weight if deviation > 0 else 0
        """
        penalty_override = objective.get('penalty_function_override', {})
        penalty_type = penalty_override.get('type', 'Linear')
        
        if penalty_type == 'Quadratic':
            coefficient = penalty_override.get('parameters', {}).get('coefficient', 1.0)
            return weight * coefficient * (deviation ** 2)
            
        elif penalty_type == 'Step':
            step_value = penalty_override.get('parameters', {}).get('step_value', weight)
            return step_value if deviation > 0 else 0.0
            
        else:  # Linear (default)
            return weight * deviation

    def find_optimal_blend(
        self,
        available_parcels: List[dict],
        target_spec: List[dict],
        target_tonnes: float,
        quality_fields: List[dict] = None
    ) -> Tuple[List[dict], Dict[str, float], float]:
        """
        Select parcels to minimize quality deviation from targets while meeting tonnage.
        
        Uses a greedy approach for simplicity (full optimization would use LP/QP solver).
        
        Args:
            available_parcels: List of parcels available for blending
            target_spec: Quality objectives to meet
            target_tonnes: Target blend quantity
            quality_fields: Optional field definitions
            
        Returns:
            Tuple of (selected_parcels, achieved_quality, total_penalty)
        """
        if not available_parcels or target_tonnes <= 0:
            return [], {}, 0.0
        
        # Sort parcels by how well they match targets (greedy)
        scored_parcels = []
        for p in available_parcels:
            # Calculate a score based on deviation from target
            qv = p.get('quality_vector', {})
            score = 0.0
            for obj in target_spec:
                field_id = obj.get('quality_field_id') or obj.get('field')
                if field_id and field_id in qv:
                    target = obj.get('target_value')
                    if target is not None:
                        score += abs(qv[field_id] - target)
            scored_parcels.append((score, p))
        
        # Sort by score (lower = better match)
        scored_parcels.sort(key=lambda x: x[0])
        
        # Select parcels until target tonnage is met
        selected = []
        remaining_tonnes = target_tonnes
        
        for score, parcel in scored_parcels:
            if remaining_tonnes <= 0:
                break
            
            parcel_tonnes = parcel.get('quantity_tonnes', 0)
            if parcel_tonnes <= 0:
                continue
            
            if parcel_tonnes <= remaining_tonnes:
                selected.append(parcel)
                remaining_tonnes -= parcel_tonnes
            else:
                # Partial parcel - create a slice
                partial = parcel.copy()
                partial['quantity_tonnes'] = remaining_tonnes
                selected.append(partial)
                remaining_tonnes = 0
        
        # Calculate achieved blend
        blend_result = self.calculate_blend_quality(selected, quality_fields)
        
        # Calculate penalty
        compliance = self.check_spec_compliance(blend_result.quality_vector, target_spec)
        
        return selected, blend_result.quality_vector, compliance.total_penalty

    def calculate_incremental_blend(
        self,
        existing_quality: Dict[str, float],
        existing_tonnes: float,
        additional_quality: Dict[str, float],
        additional_tonnes: float
    ) -> Dict[str, float]:
        """
        Calculate resulting quality when adding material to an existing blend.
        Useful for stockpile updates.
        """
        if existing_tonnes <= 0:
            return additional_quality.copy()
        
        if additional_tonnes <= 0:
            return existing_quality.copy()
        
        total_tonnes = existing_tonnes + additional_tonnes
        result = {}
        
        # Get all fields
        all_fields = set(existing_quality.keys()) | set(additional_quality.keys())
        
        for field in all_fields:
            existing_val = existing_quality.get(field, 0.0)
            additional_val = additional_quality.get(field, 0.0)
            
            # Weighted average
            result[field] = (
                (existing_val * existing_tonnes + additional_val * additional_tonnes) 
                / total_tonnes
            )
        
        return result


# Singleton instance for easy import
blending_service = BlendingService()
