"""
Coal Quality Simulation Service

Implements Monte Carlo simulation for:
- Quality uncertainty propagation through blending
- Probability of meeting product specifications
- Quality confidence intervals
- Sensitivity analysis (which parcels drive variance)

Uses numpy for efficient sampling and statistical calculations.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityDistribution:
    """
    Represents uncertainty in a quality parameter.
    
    Supports normal, triangular, and uniform distributions.
    """
    field_name: str
    mean: float
    std_dev: float = 0.0  # For normal distribution
    min_val: Optional[float] = None  # For triangular/uniform
    max_val: Optional[float] = None
    distribution_type: str = "normal"  # normal, triangular, uniform
    
    def sample(self, n_samples: int = 1000, rng: np.random.Generator = None) -> np.ndarray:
        """Generate random samples from this distribution."""
        if rng is None:
            rng = np.random.default_rng()
        
        if self.distribution_type == "normal":
            return rng.normal(self.mean, max(self.std_dev, 0.001), n_samples)
        
        elif self.distribution_type == "triangular":
            left = self.min_val if self.min_val else self.mean - 3 * self.std_dev
            right = self.max_val if self.max_val else self.mean + 3 * self.std_dev
            return rng.triangular(left, self.mean, right, n_samples)
        
        elif self.distribution_type == "uniform":
            low = self.min_val if self.min_val else self.mean - self.std_dev
            high = self.max_val if self.max_val else self.mean + self.std_dev
            return rng.uniform(low, high, n_samples)
        
        else:
            # Default to constant
            return np.full(n_samples, self.mean)


@dataclass
class ParcelQualityModel:
    """
    Quality model for a parcel with uncertainty.
    """
    parcel_id: str
    source_reference: str
    quantity_tonnes: float
    quality_distributions: Dict[str, QualityDistribution] = field(default_factory=dict)
    
    @classmethod
    def from_parcel(cls, parcel, uncertainty_factors: Dict[str, float] = None):
        """
        Create quality model from a parcel with specified uncertainty.
        
        uncertainty_factors: Dict of field_name -> relative std dev (e.g., 0.05 for 5%)
        """
        uncertainty_factors = uncertainty_factors or {
            'CV': 0.03,    # 3% CV uncertainty
            'Ash': 0.08,   # 8% Ash uncertainty
            'Moisture': 0.10,  # 10% Moisture uncertainty
            'Sulphur': 0.05,
            'Volatile': 0.05
        }
        
        quality = parcel.quality_vector or {}
        distributions = {}
        
        for field_name, mean_value in quality.items():
            if isinstance(mean_value, (int, float)):
                rel_std = uncertainty_factors.get(field_name, 0.05)
                distributions[field_name] = QualityDistribution(
                    field_name=field_name,
                    mean=float(mean_value),
                    std_dev=float(mean_value) * rel_std,
                    distribution_type="normal"
                )
        
        return cls(
            parcel_id=parcel.parcel_id,
            source_reference=parcel.source_reference or '',
            quantity_tonnes=parcel.quantity_tonnes or 0,
            quality_distributions=distributions
        )


@dataclass
class QualitySpec:
    """Product quality specification with min/max limits."""
    field_name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    target_value: Optional[float] = None
    penalty_per_unit: float = 0.0  # $/unit deviation
    is_hard_constraint: bool = True


@dataclass
class SimulationResult:
    """Results from a Monte Carlo simulation run."""
    n_simulations: int
    quality_stats: Dict[str, Dict[str, float]]  # field -> {mean, std, p5, p50, p95}
    spec_compliance: Dict[str, float]  # field -> probability of meeting spec
    overall_compliance: float  # Probability all specs met
    confidence_intervals: Dict[str, Tuple[float, float]]  # field -> (lower, upper)
    sensitivity: Dict[str, float]  # parcel_id -> contribution to variance
    simulation_time_ms: float
    
    def to_dict(self) -> Dict:
        """Convert to serializable dictionary."""
        return {
            "n_simulations": self.n_simulations,
            "quality_stats": self.quality_stats,
            "spec_compliance": self.spec_compliance,
            "overall_compliance": self.overall_compliance,
            "confidence_intervals": {
                k: {"lower": v[0], "upper": v[1]} 
                for k, v in self.confidence_intervals.items()
            },
            "sensitivity": self.sensitivity,
            "simulation_time_ms": self.simulation_time_ms
        }


class QualitySimulator:
    """
    Monte Carlo simulator for coal quality uncertainty.
    
    Propagates quality uncertainty through:
    1. Parcel quality sampling
    2. Blending calculations
    3. Wash plant yield uncertainty
    4. Product quality aggregation
    
    Outputs:
    - Probability of meeting specifications
    - Quality confidence intervals
    - Sensitivity analysis
    """
    
    def __init__(
        self,
        n_simulations: int = 1000,
        random_seed: Optional[int] = None,
        confidence_level: float = 0.90
    ):
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(random_seed)
        self.confidence_level = confidence_level
    
    def simulate_blend(
        self,
        parcels: List[ParcelQualityModel],
        specs: Optional[List[QualitySpec]] = None
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation for blended quality.
        
        Args:
            parcels: List of parcel quality models with uncertainty
            specs: Optional quality specifications to check compliance
        
        Returns:
            SimulationResult with statistics and compliance probabilities
        """
        start_time = datetime.utcnow()
        
        if not parcels:
            return self._empty_result()
        
        # Get all quality fields
        all_fields = set()
        for parcel in parcels:
            all_fields.update(parcel.quality_distributions.keys())
        
        # Sample quality for each parcel
        parcel_samples = {}
        for parcel in parcels:
            parcel_samples[parcel.parcel_id] = {
                'quantity': parcel.quantity_tonnes,
                'quality': {}
            }
            for field in all_fields:
                if field in parcel.quality_distributions:
                    parcel_samples[parcel.parcel_id]['quality'][field] = \
                        parcel.quality_distributions[field].sample(self.n_simulations, self.rng)
                else:
                    # Default to 0 if field not present
                    parcel_samples[parcel.parcel_id]['quality'][field] = \
                        np.zeros(self.n_simulations)
        
        # Calculate blended quality (tonnage-weighted average)
        total_quantity = sum(p.quantity_tonnes for p in parcels)
        
        blended_quality = {}
        for field in all_fields:
            weighted_sum = np.zeros(self.n_simulations)
            for parcel in parcels:
                weight = parcel.quantity_tonnes / total_quantity if total_quantity > 0 else 0
                weighted_sum += weight * parcel_samples[parcel.parcel_id]['quality'][field]
            blended_quality[field] = weighted_sum
        
        # Calculate statistics
        quality_stats = {}
        confidence_intervals = {}
        
        alpha = (1 - self.confidence_level) / 2
        
        for field, samples in blended_quality.items():
            quality_stats[field] = {
                'mean': float(np.mean(samples)),
                'std': float(np.std(samples)),
                'p5': float(np.percentile(samples, 5)),
                'p50': float(np.percentile(samples, 50)),
                'p95': float(np.percentile(samples, 95)),
                'min': float(np.min(samples)),
                'max': float(np.max(samples))
            }
            
            confidence_intervals[field] = (
                float(np.percentile(samples, alpha * 100)),
                float(np.percentile(samples, (1 - alpha) * 100))
            )
        
        # Check spec compliance
        spec_compliance = {}
        compliance_mask = np.ones(self.n_simulations, dtype=bool)
        
        if specs:
            for spec in specs:
                if spec.field_name not in blended_quality:
                    continue
                    
                samples = blended_quality[spec.field_name]
                field_compliant = np.ones(self.n_simulations, dtype=bool)
                
                if spec.min_value is not None:
                    field_compliant &= (samples >= spec.min_value)
                if spec.max_value is not None:
                    field_compliant &= (samples <= spec.max_value)
                
                spec_compliance[spec.field_name] = float(np.mean(field_compliant))
                
                if spec.is_hard_constraint:
                    compliance_mask &= field_compliant
        
        overall_compliance = float(np.mean(compliance_mask))
        
        # Sensitivity analysis (variance contribution)
        sensitivity = self._calculate_sensitivity(parcels, blended_quality, total_quantity)
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return SimulationResult(
            n_simulations=self.n_simulations,
            quality_stats=quality_stats,
            spec_compliance=spec_compliance,
            overall_compliance=overall_compliance,
            confidence_intervals=confidence_intervals,
            sensitivity=sensitivity,
            simulation_time_ms=duration_ms
        )
    
    def simulate_with_wash_plant(
        self,
        parcels: List[ParcelQualityModel],
        yield_mean: float = 0.85,
        yield_std: float = 0.02,
        ash_rejection_improvement: float = 0.3,
        specs: Optional[List[QualitySpec]] = None
    ) -> SimulationResult:
        """
        Simulate quality including wash plant processing.
        
        The wash plant:
        - Reduces tonnage by (1 - yield)
        - Improves ash content by ash_rejection_improvement
        - Slightly increases CV (energy concentration)
        """
        start_time = datetime.utcnow()
        
        if not parcels:
            return self._empty_result()
        
        # Sample wash plant yield
        yield_samples = self.rng.normal(yield_mean, yield_std, self.n_simulations)
        yield_samples = np.clip(yield_samples, 0.5, 0.99)
        
        # Get all quality fields
        all_fields = set()
        for parcel in parcels:
            all_fields.update(parcel.quality_distributions.keys())
        
        # Sample and process quality
        total_input_qty = sum(p.quantity_tonnes for p in parcels)
        total_output_qty = total_input_qty * yield_samples
        
        blended_quality = {}
        
        for field in all_fields:
            weighted_sum = np.zeros(self.n_simulations)
            
            for parcel in parcels:
                weight = parcel.quantity_tonnes / total_input_qty if total_input_qty > 0 else 0
                
                if field in parcel.quality_distributions:
                    samples = parcel.quality_distributions[field].sample(
                        self.n_simulations, self.rng
                    )
                else:
                    samples = np.zeros(self.n_simulations)
                
                weighted_sum += weight * samples
            
            # Apply wash plant effects
            if field == 'Ash':
                # Reduce ash based on rejection
                weighted_sum = weighted_sum * (1 - ash_rejection_improvement * (1 - yield_samples))
            elif field == 'CV':
                # Slight CV increase due to concentration
                weighted_sum = weighted_sum * (1 + 0.02 * (1 - yield_samples))
            elif field == 'Moisture':
                # Surface moisture added by washing
                weighted_sum = weighted_sum + 2.0 * self.rng.uniform(0.8, 1.2, self.n_simulations)
            
            blended_quality[field] = weighted_sum
        
        # Calculate statistics (same as simulate_blend)
        quality_stats = {}
        confidence_intervals = {}
        alpha = (1 - self.confidence_level) / 2
        
        for field, samples in blended_quality.items():
            quality_stats[field] = {
                'mean': float(np.mean(samples)),
                'std': float(np.std(samples)),
                'p5': float(np.percentile(samples, 5)),
                'p50': float(np.percentile(samples, 50)),
                'p95': float(np.percentile(samples, 95))
            }
            confidence_intervals[field] = (
                float(np.percentile(samples, alpha * 100)),
                float(np.percentile(samples, (1 - alpha) * 100))
            )
        
        # Add yield stats
        quality_stats['yield'] = {
            'mean': float(np.mean(yield_samples)),
            'std': float(np.std(yield_samples)),
            'p5': float(np.percentile(yield_samples, 5)),
            'p50': float(np.percentile(yield_samples, 50)),
            'p95': float(np.percentile(yield_samples, 95))
        }
        quality_stats['output_tonnes'] = {
            'mean': float(np.mean(total_output_qty)),
            'std': float(np.std(total_output_qty)),
            'p5': float(np.percentile(total_output_qty, 5)),
            'p50': float(np.percentile(total_output_qty, 50)),
            'p95': float(np.percentile(total_output_qty, 95))
        }
        
        # Spec compliance
        spec_compliance = {}
        compliance_mask = np.ones(self.n_simulations, dtype=bool)
        
        if specs:
            for spec in specs:
                if spec.field_name not in blended_quality:
                    continue
                samples = blended_quality[spec.field_name]
                field_compliant = np.ones(self.n_simulations, dtype=bool)
                if spec.min_value is not None:
                    field_compliant &= (samples >= spec.min_value)
                if spec.max_value is not None:
                    field_compliant &= (samples <= spec.max_value)
                spec_compliance[spec.field_name] = float(np.mean(field_compliant))
                if spec.is_hard_constraint:
                    compliance_mask &= field_compliant
        
        overall_compliance = float(np.mean(compliance_mask))
        
        # Sensitivity
        sensitivity = self._calculate_sensitivity(parcels, blended_quality, total_input_qty)
        
        end_time = datetime.utcnow()
        
        return SimulationResult(
            n_simulations=self.n_simulations,
            quality_stats=quality_stats,
            spec_compliance=spec_compliance,
            overall_compliance=overall_compliance,
            confidence_intervals=confidence_intervals,
            sensitivity=sensitivity,
            simulation_time_ms=(end_time - start_time).total_seconds() * 1000
        )
    
    def _calculate_sensitivity(
        self,
        parcels: List[ParcelQualityModel],
        blended_quality: Dict[str, np.ndarray],
        total_quantity: float
    ) -> Dict[str, float]:
        """
        Calculate sensitivity: which parcels contribute most to variance.
        
        Uses a simple weight-based approximation:
        Contribution ≈ (parcel_qty / total_qty)² × parcel_variance
        """
        sensitivity = {}
        
        # Focus on key quality fields
        key_fields = ['CV', 'Ash']
        
        for parcel in parcels:
            weight = parcel.quantity_tonnes / total_quantity if total_quantity > 0 else 0
            
            # Calculate contribution to variance
            contribution = 0
            for field in key_fields:
                if field in parcel.quality_distributions:
                    dist = parcel.quality_distributions[field]
                    contribution += (weight ** 2) * (dist.std_dev ** 2)
            
            sensitivity[parcel.parcel_id] = float(contribution)
        
        # Normalize to percentages
        total_contrib = sum(sensitivity.values())
        if total_contrib > 0:
            sensitivity = {k: v / total_contrib * 100 for k, v in sensitivity.items()}
        
        # Sort by contribution
        sensitivity = dict(sorted(sensitivity.items(), key=lambda x: x[1], reverse=True))
        
        return sensitivity
    
    def _empty_result(self) -> SimulationResult:
        """Return empty result for edge cases."""
        return SimulationResult(
            n_simulations=self.n_simulations,
            quality_stats={},
            spec_compliance={},
            overall_compliance=0.0,
            confidence_intervals={},
            sensitivity={},
            simulation_time_ms=0
        )


# Convenience function to create simulator
def create_quality_simulator(
    n_simulations: int = 1000,
    random_seed: int = None
) -> QualitySimulator:
    """Create a quality simulator with specified parameters."""
    return QualitySimulator(n_simulations=n_simulations, random_seed=random_seed)
