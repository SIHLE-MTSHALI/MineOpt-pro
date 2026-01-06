"""
Simulation Service - Monte Carlo Quality Uncertainty Modeling

Provides:
- Monte Carlo simulation for quality variance
- Risk probability calculations
- Uncertainty parameter management
- P5/P50/P95 confidence bands
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
import math
from datetime import datetime


@dataclass
class UncertaintyParams:
    """Uncertainty parameters for a quality field."""
    mean: float
    std_dev: float
    distribution: str = "normal"  # normal, lognormal, triangular
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class SimulationInput:
    """Input configuration for simulation."""
    schedule_version_id: str
    iterations: int = 1000
    quality_targets: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # field: (min, max)
    confidence_levels: List[float] = field(default_factory=lambda: [0.05, 0.50, 0.95])


@dataclass
class SimulationResult:
    """Result of a Monte Carlo simulation."""
    simulation_id: str
    schedule_version_id: str
    iterations: int
    completed_at: datetime
    quality_distributions: Dict[str, Dict]  # field: {mean, std, p5, p50, p95}
    compliance_probability: Dict[str, float]  # field: probability of meeting spec
    overall_risk_score: float  # 0-100, lower is better
    risk_breakdown: List[Dict]  # List of risk factors


class SimulationService:
    """
    Monte Carlo simulation service for quality uncertainty analysis.
    
    Runs stochastic simulations to assess probability of meeting
    quality specifications given uncertainty in source material.
    """

    def __init__(self, db=None):
        self.db = db
        self._rng = random.Random()

    def set_seed(self, seed: int):
        """Set random seed for reproducibility."""
        self._rng.seed(seed)

    def _sample_value(self, params: UncertaintyParams) -> float:
        """Sample a value from the uncertainty distribution."""
        if params.distribution == "normal":
            value = self._rng.gauss(params.mean, params.std_dev)
        elif params.distribution == "lognormal":
            # Log-normal: mean and std are for underlying normal
            mu = math.log(params.mean**2 / math.sqrt(params.std_dev**2 + params.mean**2))
            sigma = math.sqrt(math.log(1 + (params.std_dev**2 / params.mean**2)))
            value = self._rng.lognormvariate(mu, sigma)
        elif params.distribution == "triangular":
            # Triangular: use min, mean, max
            min_v = params.min_value or (params.mean - 2 * params.std_dev)
            max_v = params.max_value or (params.mean + 2 * params.std_dev)
            value = self._rng.triangular(min_v, max_v, params.mean)
        else:
            value = params.mean

        # Clamp to bounds if specified
        if params.min_value is not None:
            value = max(value, params.min_value)
        if params.max_value is not None:
            value = min(value, params.max_value)

        return value

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from a list of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        idx = int(percentile * len(sorted_values))
        idx = min(idx, len(sorted_values) - 1)
        return sorted_values[idx]

    def run_monte_carlo(
        self,
        parcels: List[Dict],
        uncertainty_params: Dict[str, Dict[str, UncertaintyParams]],
        targets: Dict[str, Tuple[float, float]],
        iterations: int = 1000,
        seed: Optional[int] = None
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation for quality uncertainty.
        
        Args:
            parcels: List of parcel dicts with parcel_id, tonnes, quality_vector
            uncertainty_params: {parcel_id: {field: UncertaintyParams}}
            targets: Quality targets {field: (min_value, max_value)}
            iterations: Number of simulation iterations
            seed: Random seed for reproducibility
            
        Returns:
            SimulationResult with probability distributions
        """
        if seed is not None:
            self.set_seed(seed)

        # Initialize result collectors
        quality_samples: Dict[str, List[float]] = {}
        compliance_counts: Dict[str, int] = {}

        for field in targets.keys():
            quality_samples[field] = []
            compliance_counts[field] = 0

        # Run iterations
        for _ in range(iterations):
            # Simulate quality for each parcel
            iteration_totals: Dict[str, float] = {f: 0.0 for f in targets}
            iteration_weights: Dict[str, float] = {f: 0.0 for f in targets}

            for parcel in parcels:
                parcel_id = parcel.get("parcel_id", "unknown")
                tonnes = parcel.get("tonnes", 0)
                base_quality = parcel.get("quality_vector", {})

                for field in targets.keys():
                    base_value = base_quality.get(field, 0)
                    
                    # Get uncertainty parameters for this parcel/field
                    parcel_params = uncertainty_params.get(parcel_id, {})
                    field_params = parcel_params.get(field)

                    if field_params:
                        # Sample with uncertainty
                        sampled_value = self._sample_value(field_params)
                    else:
                        # Use base value with default 5% variation
                        std_dev = abs(base_value) * 0.05
                        sampled_value = self._rng.gauss(base_value, std_dev) if std_dev > 0 else base_value

                    iteration_totals[field] += sampled_value * tonnes
                    iteration_weights[field] += tonnes

            # Calculate weighted average for this iteration
            iteration_quality = {}
            for field in targets.keys():
                if iteration_weights[field] > 0:
                    iteration_quality[field] = iteration_totals[field] / iteration_weights[field]
                else:
                    iteration_quality[field] = 0

                quality_samples[field].append(iteration_quality[field])

                # Check compliance
                min_val, max_val = targets[field]
                if min_val <= iteration_quality[field] <= max_val:
                    compliance_counts[field] += 1

        # Calculate results
        quality_distributions = {}
        compliance_probability = {}

        for field in targets.keys():
            samples = quality_samples[field]
            mean_val = sum(samples) / len(samples) if samples else 0
            std_val = (sum((x - mean_val) ** 2 for x in samples) / len(samples)) ** 0.5 if samples else 0

            quality_distributions[field] = {
                "mean": round(mean_val, 4),
                "std": round(std_val, 4),
                "p5": round(self._calculate_percentile(samples, 0.05), 4),
                "p50": round(self._calculate_percentile(samples, 0.50), 4),
                "p95": round(self._calculate_percentile(samples, 0.95), 4),
                "min": round(min(samples), 4) if samples else 0,
                "max": round(max(samples), 4) if samples else 0
            }

            compliance_probability[field] = round(compliance_counts[field] / iterations, 4)

        # Calculate overall risk score (0-100, lower is better)
        avg_compliance = sum(compliance_probability.values()) / len(compliance_probability) if compliance_probability else 1
        overall_risk_score = round((1 - avg_compliance) * 100, 2)

        # Build risk breakdown
        risk_breakdown = []
        for field, prob in compliance_probability.items():
            if prob < 1.0:
                min_val, max_val = targets[field]
                risk_breakdown.append({
                    "field": field,
                    "compliance_probability": prob,
                    "risk_level": "high" if prob < 0.8 else "medium" if prob < 0.95 else "low",
                    "target_range": f"{min_val} - {max_val}",
                    "expected_value": quality_distributions[field]["p50"]
                })

        # Sort by risk (lowest probability first)
        risk_breakdown.sort(key=lambda x: x["compliance_probability"])

        return SimulationResult(
            simulation_id=f"sim-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            schedule_version_id="",  # Filled by caller
            iterations=iterations,
            completed_at=datetime.utcnow(),
            quality_distributions=quality_distributions,
            compliance_probability=compliance_probability,
            overall_risk_score=overall_risk_score,
            risk_breakdown=risk_breakdown
        )

    def get_risk_bands(
        self,
        quality_field: str,
        result: SimulationResult
    ) -> Dict[str, float]:
        """
        Get risk bands (P5, P50, P95) for a specific quality field.
        
        Args:
            quality_field: Name of the quality field
            result: SimulationResult from run_monte_carlo
            
        Returns:
            Dict with p5, p50, p95 values
        """
        dist = result.quality_distributions.get(quality_field, {})
        return {
            "p5": dist.get("p5", 0),
            "p50": dist.get("p50", 0),
            "p95": dist.get("p95", 0)
        }

    def to_dict(self, result: SimulationResult) -> Dict:
        """Convert SimulationResult to dictionary for API response."""
        return {
            "simulation_id": result.simulation_id,
            "schedule_version_id": result.schedule_version_id,
            "iterations": result.iterations,
            "completed_at": result.completed_at.isoformat(),
            "quality_distributions": result.quality_distributions,
            "compliance_probability": result.compliance_probability,
            "overall_risk_score": result.overall_risk_score,
            "risk_breakdown": result.risk_breakdown
        }
