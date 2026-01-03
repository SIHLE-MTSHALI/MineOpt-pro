"""
Quality Service - Section 3 of Enterprise Specification

Comprehensive quality management service providing:
- Quality vector blending with multiple aggregation rules
- Basis conversion (ARB, ADB, DB, DAF)
- Constraint evaluation with penalty curves
- Quality tracking through flow stages
- Missing data policy enforcement
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..domain import models_resource
import math


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class BlendQualityResult:
    """Result of a quality blending calculation."""
    quality_vector: Dict[str, float]
    total_tonnes: float
    source_count: int
    warnings: List[str]


@dataclass
class ConstraintCheckResult:
    """Result of checking quality against constraints."""
    is_compliant: bool
    compliance_percent: float  # 0-100
    violations: List[str]
    penalties: Dict[str, float]
    total_penalty: float
    hard_constraint_violated: bool


@dataclass 
class QualityStageRecord:
    """Tracks quality at a specific stage in the flow."""
    stage: str  # insitu, rom, stockpile, feed, product, final
    reference_id: str  # area_id, parcel_id, node_id, etc.
    quality_vector: Dict[str, float]
    quantity_tonnes: float
    timestamp: str


# =============================================================================
# Main Service Class
# =============================================================================

class QualityService:
    """
    Comprehensive quality management for coal mine scheduling.
    
    Supports:
    - Weighted average blending
    - Multiple aggregation rules per field
    - Basis conversion (ARB/ADB/DB/DAF)
    - Penalty curve evaluation
    - Hard/soft constraint handling
    """
    
    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------
    
    @staticmethod
    def validate_quality_vector(
        quality_vector: Dict[str, float], 
        fields: List[models_resource.QualityField]
    ) -> List[str]:
        """
        Validates that a quality vector matches the site's defined fields.
        Enforces missing_data_policy per field.
        
        Returns a list of warnings/errors.
        """
        errors = []
        for field in fields:
            if field.name not in quality_vector:
                if field.missing_data_policy == "Error":
                    errors.append(f"Missing required quality field: {field.name}")
                elif field.missing_data_policy == "Warning":
                    errors.append(f"Warning: Missing quality field: {field.name}")
                # "Ignore" produces no message
        return errors
    
    @staticmethod
    def apply_missing_data_defaults(
        quality_vector: Dict[str, float],
        fields: List[models_resource.QualityField]
    ) -> Dict[str, float]:
        """
        Apply default values for missing fields based on policy.
        """
        result = quality_vector.copy()
        for field in fields:
            if field.name not in result:
                policy = getattr(field, 'missing_data_policy', 'Ignore')
                if policy in ['UseDefault', 'Warning']:
                    default = getattr(field, 'default_value', None)
                    if default is not None:
                        result[field.name] = default
        return result
    
    # -------------------------------------------------------------------------
    # Basis Conversion
    # -------------------------------------------------------------------------
    
    @staticmethod
    def convert_basis(
        value: float, 
        start_basis: str, 
        target_basis: str, 
        moisture_arb: float = 0.0, 
        moisture_adb: float = 0.0,
        moisture_inherent: float = 0.0
    ) -> float:
        """
        Converts a value between quality bases.
        
        Supported conversions:
        - ARB (As Received Basis) <-> ADB (Air Dried Basis)
        - ADB <-> DB (Dry Basis)  
        - DB <-> DAF (Dry Ash Free)
        
        Formulae (ISO standards):
        - ADB = ARB × (100 - IM) / (100 - TM)
        - DB = ADB × 100 / (100 - IM)
        - DAF = DB × 100 / (100 - Ash_DB)
        
        Args:
            value: The quality value to convert
            start_basis: Source basis (ARB, ADB, DB, DAF)
            target_basis: Target basis
            moisture_arb: Total Moisture for ARB (%)
            moisture_adb: Inherent Moisture for ADB (%)
            moisture_inherent: Alternative name for inherent moisture
        """
        if start_basis == target_basis:
            return value
        
        # Use moisture_inherent if moisture_adb not specified
        if moisture_adb == 0 and moisture_inherent > 0:
            moisture_adb = moisture_inherent
            
        # Validate inputs
        if moisture_arb >= 100 or moisture_adb >= 100:
            return 0.0
            
        factor = 1.0
        
        # ARB to ADB
        if start_basis == "ARB" and target_basis == "ADB":
            if (100 - moisture_arb) == 0:
                return 0.0
            factor = (100 - moisture_adb) / (100 - moisture_arb)
            
        # ADB to ARB
        elif start_basis == "ADB" and target_basis == "ARB":
            if (100 - moisture_adb) == 0:
                return 0.0
            factor = (100 - moisture_arb) / (100 - moisture_adb)
            
        # ADB to DB
        elif start_basis == "ADB" and target_basis == "DB":
            if (100 - moisture_adb) == 0:
                return 0.0
            factor = 100 / (100 - moisture_adb)
            
        # DB to ADB
        elif start_basis == "DB" and target_basis == "ADB":
            factor = (100 - moisture_adb) / 100
            
        # ARB to DB (via ADB)
        elif start_basis == "ARB" and target_basis == "DB":
            adb_value = QualityService.convert_basis(
                value, "ARB", "ADB", moisture_arb, moisture_adb
            )
            return QualityService.convert_basis(
                adb_value, "ADB", "DB", moisture_arb, moisture_adb
            )
            
        # DB to ARB (via ADB)
        elif start_basis == "DB" and target_basis == "ARB":
            adb_value = QualityService.convert_basis(
                value, "DB", "ADB", moisture_arb, moisture_adb
            )
            return QualityService.convert_basis(
                adb_value, "ADB", "ARB", moisture_arb, moisture_adb
            )
            
        return round(value * factor, 4)
    
    @staticmethod
    def convert_quality_vector_basis(
        quality_vector: Dict[str, float],
        fields: List[models_resource.QualityField],
        target_basis: str,
        moisture_arb: float = 0.0,
        moisture_adb: float = 0.0
    ) -> Dict[str, float]:
        """
        Convert all fields in a quality vector to target basis.
        Only converts fields that have a defined basis.
        """
        result = {}
        for field in fields:
            field_name = field.name
            if field_name in quality_vector:
                source_basis = getattr(field, 'unit_basis', None)
                if source_basis and source_basis != target_basis:
                    result[field_name] = QualityService.convert_basis(
                        quality_vector[field_name],
                        source_basis,
                        target_basis,
                        moisture_arb,
                        moisture_adb
                    )
                else:
                    result[field_name] = quality_vector[field_name]
        return result
    
    # -------------------------------------------------------------------------
    # Blending
    # -------------------------------------------------------------------------
    
    @staticmethod
    def calculate_blend_quality(
        sources: List[Dict],  # Each has {quality_vector, quantity_tonnes}
        fields: Optional[List[models_resource.QualityField]] = None
    ) -> BlendQualityResult:
        """
        Calculates blended quality from multiple sources.
        
        Supports aggregation rules per field:
        - WeightedAverage: Mass-weighted average (default)
        - Sum: Sum of all values
        - Min: Minimum value
        - Max: Maximum value
        
        Args:
            sources: List of dicts with 'quality_vector' and 'quantity_tonnes'
            fields: Optional field definitions with aggregation rules
            
        Returns:
            BlendQualityResult with combined quality vector
        """
        warnings = []
        
        if not sources:
            return BlendQualityResult(
                quality_vector={},
                total_tonnes=0.0,
                source_count=0,
                warnings=["No sources provided for blending"]
            )
        
        # Build field aggregation rules map
        field_rules = {}
        if fields:
            for f in fields:
                rule = getattr(f, 'aggregation_rule', 'WeightedAverage')
                field_rules[f.name] = rule
        
        # Collect all field names present
        all_fields = set()
        for src in sources:
            qv = src.get('quality_vector', {})
            if qv:
                all_fields.update(qv.keys())
        
        # Calculate blended value for each field
        result = {}
        total_tonnes = sum(s.get('quantity_tonnes', 0) for s in sources)
        
        for field_name in all_fields:
            rule = field_rules.get(field_name, 'WeightedAverage')
            
            if rule == 'WeightedAverage':
                weighted_sum = 0.0
                weight_total = 0.0
                for src in sources:
                    qv = src.get('quality_vector', {})
                    tonnes = src.get('quantity_tonnes', 0)
                    if field_name in qv and tonnes > 0:
                        weighted_sum += qv[field_name] * tonnes
                        weight_total += tonnes
                result[field_name] = round(weighted_sum / weight_total, 4) if weight_total > 0 else 0.0
                
            elif rule == 'Sum':
                result[field_name] = sum(
                    s.get('quality_vector', {}).get(field_name, 0)
                    for s in sources
                )
                
            elif rule == 'Min':
                values = [
                    s.get('quality_vector', {}).get(field_name)
                    for s in sources
                    if field_name in s.get('quality_vector', {})
                ]
                result[field_name] = min(values) if values else 0.0
                
            elif rule == 'Max':
                values = [
                    s.get('quality_vector', {}).get(field_name)
                    for s in sources
                    if field_name in s.get('quality_vector', {})
                ]
                result[field_name] = max(values) if values else 0.0
                
            else:
                # Default to weighted average
                weighted_sum = 0.0
                weight_total = 0.0
                for src in sources:
                    qv = src.get('quality_vector', {})
                    tonnes = src.get('quantity_tonnes', 0)
                    if field_name in qv and tonnes > 0:
                        weighted_sum += qv[field_name] * tonnes
                        weight_total += tonnes
                result[field_name] = round(weighted_sum / weight_total, 4) if weight_total > 0 else 0.0
        
        return BlendQualityResult(
            quality_vector=result,
            total_tonnes=total_tonnes,
            source_count=len(sources),
            warnings=warnings
        )
    
    @staticmethod
    def calculate_incremental_blend(
        existing_quality: Dict[str, float],
        existing_tonnes: float,
        additional_quality: Dict[str, float],
        additional_tonnes: float
    ) -> Dict[str, float]:
        """
        Calculate resulting quality when adding material to existing inventory.
        Useful for stockpile updates.
        """
        if existing_tonnes <= 0:
            return additional_quality.copy()
        if additional_tonnes <= 0:
            return existing_quality.copy()
            
        total = existing_tonnes + additional_tonnes
        result = {}
        
        all_fields = set(existing_quality.keys()) | set(additional_quality.keys())
        for field in all_fields:
            existing_val = existing_quality.get(field, 0.0)
            additional_val = additional_quality.get(field, 0.0)
            result[field] = round(
                (existing_val * existing_tonnes + additional_val * additional_tonnes) / total,
                4
            )
        
        return result
    
    # -------------------------------------------------------------------------
    # Constraint Evaluation
    # -------------------------------------------------------------------------
    
    @staticmethod
    def evaluate_constraints(
        quality_vector: Dict[str, float],
        constraints: List[Dict],  # List of constraint definitions
        tolerance: float = 0.0
    ) -> ConstraintCheckResult:
        """
        Evaluate quality against a set of constraints.
        
        Constraint format:
        {
            "field": "CV_ARB",
            "type": "Min" | "Max" | "Target" | "Range",
            "value": 23.0,  # For Min/Max/Target
            "min_value": 22.0,  # For Range
            "max_value": 25.0,  # For Range
            "penalty_weight": 1.0,
            "penalty_type": "Linear" | "Quadratic" | "Step",
            "hard_constraint": false
        }
        """
        violations = []
        penalties = {}
        total_penalty = 0.0
        hard_violated = False
        checks_passed = 0
        total_checks = 0
        
        for constraint in constraints:
            field_name = constraint.get('field') or constraint.get('quality_field_id')
            if not field_name or field_name not in quality_vector:
                continue
                
            total_checks += 1
            actual = quality_vector[field_name]
            constraint_type = constraint.get('type') or constraint.get('objective_type', 'Range')
            is_hard = constraint.get('hard_constraint', False)
            penalty_weight = constraint.get('penalty_weight', 1.0)
            penalty_type = constraint.get('penalty_type', 'Linear')
            
            violation = None
            deviation = 0.0
            
            # Check constraint based on type
            if constraint_type == 'Min':
                min_val = constraint.get('value') or constraint.get('min_value', 0)
                if actual < min_val - tolerance:
                    deviation = min_val - actual
                    violation = f"{field_name}: {actual:.2f} < min {min_val:.2f}"
                else:
                    checks_passed += 1
                    
            elif constraint_type == 'Max':
                max_val = constraint.get('value') or constraint.get('max_value', 0)
                if actual > max_val + tolerance:
                    deviation = actual - max_val
                    violation = f"{field_name}: {actual:.2f} > max {max_val:.2f}"
                else:
                    checks_passed += 1
                    
            elif constraint_type == 'Target':
                target = constraint.get('value') or constraint.get('target_value', 0)
                deviation = abs(actual - target)
                if deviation > tolerance:
                    violation = f"{field_name}: {actual:.2f} != target {target:.2f}"
                else:
                    checks_passed += 1
                    
            elif constraint_type == 'Range':
                min_val = constraint.get('min_value', float('-inf'))
                max_val = constraint.get('max_value', float('inf'))
                if actual < min_val - tolerance:
                    deviation = min_val - actual
                    violation = f"{field_name}: {actual:.2f} < min {min_val:.2f}"
                elif actual > max_val + tolerance:
                    deviation = actual - max_val
                    violation = f"{field_name}: {actual:.2f} > max {max_val:.2f}"
                else:
                    checks_passed += 1
            
            # Calculate penalty if violated
            if deviation > 0:
                penalty = QualityService._calculate_penalty(
                    deviation, penalty_weight, penalty_type, constraint
                )
                penalties[field_name] = penalty
                total_penalty += penalty
                
                if violation:
                    violations.append(violation)
                    if is_hard:
                        hard_violated = True
        
        compliance_percent = (checks_passed / total_checks * 100) if total_checks > 0 else 100.0
        
        return ConstraintCheckResult(
            is_compliant=len(violations) == 0 and not hard_violated,
            compliance_percent=round(compliance_percent, 1),
            violations=violations,
            penalties=penalties,
            total_penalty=total_penalty,
            hard_constraint_violated=hard_violated
        )
    
    @staticmethod
    def _calculate_penalty(
        deviation: float,
        weight: float,
        penalty_type: str,
        constraint: Dict
    ) -> float:
        """
        Calculate penalty cost for a quality deviation.
        
        Penalty Types:
        - Linear: penalty = weight × deviation
        - Quadratic: penalty = weight × deviation²
        - Step: penalty = step_value if deviation > 0
        - Exponential: penalty = weight × (e^deviation - 1)
        """
        if penalty_type == 'Quadratic':
            coefficient = constraint.get('coefficient', 1.0)
            return weight * coefficient * (deviation ** 2)
            
        elif penalty_type == 'Step':
            step_value = constraint.get('step_value', weight)
            return step_value if deviation > 0 else 0.0
            
        elif penalty_type == 'Exponential':
            return weight * (math.exp(deviation) - 1)
            
        else:  # Linear (default)
            return weight * deviation
    
    # -------------------------------------------------------------------------
    # Quality Tracking
    # -------------------------------------------------------------------------
    
    @staticmethod
    def create_stage_record(
        stage: str,
        reference_id: str,
        quality_vector: Dict[str, float],
        quantity_tonnes: float,
        timestamp: str = None
    ) -> QualityStageRecord:
        """
        Create a quality tracking record for a specific stage.
        
        Stages:
        - insitu: Block model in-situ quality
        - rom: Run-of-mine material from mining
        - stockpile: Current stockpile inventory quality
        - feed: Plant feed blend quality
        - product: Post-wash product quality
        - final: Final product stockpile quality
        """
        import datetime
        if timestamp is None:
            timestamp = datetime.datetime.utcnow().isoformat()
            
        return QualityStageRecord(
            stage=stage,
            reference_id=reference_id,
            quality_vector=quality_vector,
            quantity_tonnes=quantity_tonnes,
            timestamp=timestamp
        )
    
    @staticmethod
    def track_quality_through_flow(
        stages: List[QualityStageRecord]
    ) -> Dict[str, Dict]:
        """
        Summarize quality changes through flow stages.
        Returns stage-by-stage quality comparison.
        """
        summary = {}
        for record in stages:
            summary[record.stage] = {
                'reference_id': record.reference_id,
                'quality': record.quality_vector,
                'tonnes': record.quantity_tonnes,
                'timestamp': record.timestamp
            }
        return summary


# =============================================================================
# Default Quality Field Definitions
# =============================================================================

THERMAL_COAL_QUALITY_FIELDS = [
    {
        "name": "CV_ARB",
        "display_name": "Calorific Value (ARB)",
        "unit": "MJ/kg",
        "unit_basis": "ARB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 2,
        "typical_min": 18.0,
        "typical_max": 28.0
    },
    {
        "name": "CV_ADB",
        "display_name": "Calorific Value (ADB)",
        "unit": "MJ/kg",
        "unit_basis": "ADB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 2,
        "typical_min": 20.0,
        "typical_max": 30.0
    },
    {
        "name": "Ash_ADB",
        "display_name": "Ash Content (ADB)",
        "unit": "%",
        "unit_basis": "ADB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 2,
        "typical_min": 8.0,
        "typical_max": 25.0
    },
    {
        "name": "TM",
        "display_name": "Total Moisture",
        "unit": "%",
        "unit_basis": "ARB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 2,
        "typical_min": 5.0,
        "typical_max": 20.0
    },
    {
        "name": "IM",
        "display_name": "Inherent Moisture",
        "unit": "%",
        "unit_basis": "ADB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 2,
        "typical_min": 2.0,
        "typical_max": 8.0
    },
    {
        "name": "Sulphur_ADB",
        "display_name": "Sulphur (ADB)",
        "unit": "%",
        "unit_basis": "ADB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 3,
        "typical_min": 0.3,
        "typical_max": 2.0
    },
    {
        "name": "VM_ADB",
        "display_name": "Volatile Matter (ADB)",
        "unit": "%",
        "unit_basis": "ADB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 2,
        "typical_min": 20.0,
        "typical_max": 40.0
    },
    {
        "name": "FC_ADB",
        "display_name": "Fixed Carbon (ADB)",
        "unit": "%",
        "unit_basis": "ADB",
        "aggregation_rule": "WeightedAverage",
        "display_precision": 2,
        "typical_min": 40.0,
        "typical_max": 65.0
    },
    {
        "name": "HGI",
        "display_name": "Hardgrove Grindability Index",
        "unit": "",
        "unit_basis": None,
        "aggregation_rule": "WeightedAverage",
        "display_precision": 0,
        "typical_min": 40,
        "typical_max": 80
    },
    {
        "name": "Size_Plus50mm",
        "display_name": "Size +50mm",
        "unit": "%",
        "unit_basis": None,
        "aggregation_rule": "WeightedAverage",
        "display_precision": 1,
        "typical_min": 0,
        "typical_max": 30
    },
    {
        "name": "Size_Minus2mm",
        "display_name": "Size -2mm (Fines)",
        "unit": "%",
        "unit_basis": None,
        "aggregation_rule": "WeightedAverage",
        "display_precision": 1,
        "typical_min": 5,
        "typical_max": 25
    }
]


# Singleton instance
quality_service = QualityService()

