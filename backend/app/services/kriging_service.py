"""
Kriging Service - Phase 3 Block Model with Kriging

Geostatistical estimation for block model grade prediction.
Implements:
- Semi-variogram calculation and fitting
- Ordinary kriging estimation
- Inverse Distance Weighting (IDW) fallback
- Cross-validation for model selection

Uses PyKrige library for kriging calculations (BSD license - FREE).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import curve_fit
import math

try:
    from pykrige.ok import OrdinaryKriging
    PYKRIGE_AVAILABLE = True
except ImportError:
    PYKRIGE_AVAILABLE = False


class VariogramModel(str, Enum):
    """Supported variogram models."""
    SPHERICAL = "spherical"
    EXPONENTIAL = "exponential"
    GAUSSIAN = "gaussian"
    LINEAR = "linear"


@dataclass
class SamplePoint:
    """A sample point with coordinates and value."""
    x: float  # Easting
    y: float  # Northing
    z: float  # Elevation
    value: float
    weight: float = 1.0
    hole_id: Optional[str] = None


@dataclass
class VariogramParams:
    """Fitted variogram parameters."""
    model: VariogramModel
    nugget: float = 0.0      # Micro-scale variance (C0)
    sill: float = 1.0        # Total variance (C0 + C)
    range: float = 100.0     # Range of influence (a)
    anisotropy: float = 1.0  # Ratio of major/minor axes
    azimuth: float = 0.0     # Direction of major axis
    r_squared: float = 0.0   # Fit quality
    
    @property
    def partial_sill(self) -> float:
        """The structured variance component (C = sill - nugget)."""
        return self.sill - self.nugget


@dataclass
class ExperimentalVariogram:
    """Experimental variogram data."""
    lags: np.ndarray
    semivariances: np.ndarray
    pair_counts: np.ndarray
    

@dataclass
class BlockEstimate:
    """Estimated value for a block."""
    block_id: str
    x: float
    y: float
    z: float
    estimated_value: float
    estimation_variance: float
    estimation_method: str
    num_samples: int


@dataclass
class KrigingResult:
    """Result of a kriging estimation."""
    success: bool
    estimates: List[BlockEstimate] = field(default_factory=list)
    variogram_params: Optional[VariogramParams] = None
    cross_validation_rmse: Optional[float] = None
    errors: List[str] = field(default_factory=list)


class KrigingService:
    """
    Geostatistical estimation service.
    
    Provides:
    - Variogram calculation and fitting
    - Ordinary kriging estimation
    - IDW estimation as fallback
    - Cross-validation
    """
    
    def __init__(self):
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check that required libraries are available."""
        if not PYKRIGE_AVAILABLE:
            print("Warning: PyKrige not installed. Some kriging features may be limited.")
    
    # =========================================================================
    # VARIOGRAM CALCULATION
    # =========================================================================
    
    def calculate_experimental_variogram(
        self,
        samples: List[SamplePoint],
        num_lags: int = 15,
        lag_size: Optional[float] = None,
        max_lag: Optional[float] = None
    ) -> ExperimentalVariogram:
        """
        Calculate the experimental semi-variogram.
        
        Args:
            samples: List of sample points with values
            num_lags: Number of lag bins
            lag_size: Size of each lag bin (auto-calculated if None)
            max_lag: Maximum lag distance (auto-calculated if None)
            
        Returns:
            ExperimentalVariogram with lag distances and semivariances
        """
        n = len(samples)
        
        # Extract coordinates and values
        coords = np.array([[s.x, s.y, s.z] for s in samples])
        values = np.array([s.value for s in samples])
        
        # Calculate pairwise distances
        distances = squareform(pdist(coords))
        
        # Auto-calculate lag parameters
        if max_lag is None:
            max_lag = np.max(distances) / 2  # Rule of thumb
        
        if lag_size is None:
            lag_size = max_lag / num_lags
        
        # Initialize lag bins
        lags = np.zeros(num_lags)
        semivariances = np.zeros(num_lags)
        pair_counts = np.zeros(num_lags, dtype=int)
        
        # Calculate semivariance for each lag
        for i in range(n):
            for j in range(i + 1, n):
                dist = distances[i, j]
                if dist > 0 and dist <= max_lag:
                    # Determine lag bin
                    lag_idx = int(dist / lag_size)
                    if lag_idx >= num_lags:
                        lag_idx = num_lags - 1
                    
                    # Add to semivariance
                    squared_diff = (values[i] - values[j]) ** 2
                    semivariances[lag_idx] += squared_diff
                    pair_counts[lag_idx] += 1
        
        # Finalize semivariances (divide by 2N)
        for k in range(num_lags):
            lags[k] = (k + 0.5) * lag_size
            if pair_counts[k] > 0:
                semivariances[k] = semivariances[k] / (2 * pair_counts[k])
        
        return ExperimentalVariogram(
            lags=lags,
            semivariances=semivariances,
            pair_counts=pair_counts
        )
    
    def fit_variogram(
        self,
        experimental: ExperimentalVariogram,
        model: VariogramModel = VariogramModel.SPHERICAL,
        initial_params: Optional[Dict[str, float]] = None
    ) -> VariogramParams:
        """
        Fit a theoretical variogram model to experimental data.
        
        Args:
            experimental: Experimental variogram
            model: Theoretical model type
            initial_params: Initial parameter estimates
            
        Returns:
            VariogramParams with fitted parameters
        """
        # Filter out lags with no pairs
        valid = experimental.pair_counts > 0
        lags = experimental.lags[valid]
        semivar = experimental.semivariances[valid]
        
        if len(lags) < 3:
            # Not enough data, return defaults
            return VariogramParams(
                model=model,
                nugget=0.0,
                sill=np.var([s for s in semivar if s > 0]) if any(semivar > 0) else 1.0,
                range=max(lags) / 2 if len(lags) > 0 else 100.0
            )
        
        # Define model functions
        def spherical(h, c0, c, a):
            """Spherical variogram model."""
            result = np.zeros_like(h)
            mask = h <= a
            result[mask] = c0 + c * (1.5 * h[mask] / a - 0.5 * (h[mask] / a) ** 3)
            result[~mask] = c0 + c
            return result
        
        def exponential(h, c0, c, a):
            """Exponential variogram model."""
            return c0 + c * (1 - np.exp(-h / a))
        
        def gaussian(h, c0, c, a):
            """Gaussian variogram model."""
            return c0 + c * (1 - np.exp(-(h / a) ** 2))
        
        def linear(h, c0, c, a):
            """Linear variogram model."""
            return c0 + c * np.minimum(h / a, 1.0)
        
        model_funcs = {
            VariogramModel.SPHERICAL: spherical,
            VariogramModel.EXPONENTIAL: exponential,
            VariogramModel.GAUSSIAN: gaussian,
            VariogramModel.LINEAR: linear,
        }
        
        func = model_funcs[model]
        
        # Initial parameter estimates
        if initial_params:
            p0 = [
                initial_params.get("nugget", 0),
                initial_params.get("sill", np.max(semivar)),
                initial_params.get("range", lags[np.argmax(semivar > 0.95 * np.max(semivar))] if any(semivar > 0) else max(lags) / 2)
            ]
        else:
            # Auto-estimate
            p0 = [
                0,  # Nugget
                np.max(semivar) if any(semivar > 0) else 1.0,  # Sill
                max(lags) / 2  # Range
            ]
        
        # Bounds
        bounds = (
            [0, 0, lags[0] if len(lags) > 0 else 0.001],  # Lower bounds
            [np.max(semivar) * 0.5, np.max(semivar) * 2, max(lags) * 2]  # Upper bounds
        )
        
        try:
            popt, pcov = curve_fit(
                func, lags, semivar, p0=p0, bounds=bounds, maxfev=10000
            )
            
            # Calculate R-squared
            ss_res = np.sum((semivar - func(lags, *popt)) ** 2)
            ss_tot = np.sum((semivar - np.mean(semivar)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            return VariogramParams(
                model=model,
                nugget=popt[0],
                sill=popt[0] + popt[1],
                range=popt[2],
                r_squared=r_squared
            )
            
        except Exception as e:
            # Fallback to defaults
            return VariogramParams(
                model=model,
                nugget=0.0,
                sill=np.max(semivar) if any(semivar > 0) else 1.0,
                range=max(lags) / 2 if len(lags) > 0 else 100.0,
                r_squared=0.0
            )
    
    def auto_fit_variogram(
        self,
        samples: List[SamplePoint]
    ) -> VariogramParams:
        """
        Automatically fit the best variogram model.
        
        Tries multiple models and returns the best fit.
        """
        experimental = self.calculate_experimental_variogram(samples)
        
        best_params = None
        best_r_squared = -1
        
        for model in [VariogramModel.SPHERICAL, VariogramModel.EXPONENTIAL, VariogramModel.GAUSSIAN]:
            params = self.fit_variogram(experimental, model)
            if params.r_squared > best_r_squared:
                best_r_squared = params.r_squared
                best_params = params
        
        return best_params or VariogramParams(model=VariogramModel.SPHERICAL)
    
    # =========================================================================
    # KRIGING ESTIMATION
    # =========================================================================
    
    def ordinary_kriging(
        self,
        samples: List[SamplePoint],
        target_points: List[Tuple[float, float, float]],
        variogram_params: Optional[VariogramParams] = None,
        max_samples: int = 20,
        min_samples: int = 3,
        search_radius: Optional[float] = None
    ) -> List[BlockEstimate]:
        """
        Perform ordinary kriging estimation.
        
        Args:
            samples: Sample data points
            target_points: List of (x, y, z) points to estimate
            variogram_params: Pre-fitted variogram (auto-fit if None)
            max_samples: Maximum samples to use for each estimate
            min_samples: Minimum samples required for estimate
            search_radius: Search radius for nearby samples
            
        Returns:
            List of BlockEstimate for each target point
        """
        if len(samples) < min_samples:
            return []
        
        # Auto-fit variogram if needed
        if variogram_params is None:
            variogram_params = self.auto_fit_variogram(samples)
        
        # Use PyKrige if available
        if PYKRIGE_AVAILABLE:
            return self._kriging_with_pykrige(
                samples, target_points, variogram_params, 
                max_samples, min_samples, search_radius
            )
        else:
            # Fallback to simple implementation
            return self._kriging_simple(
                samples, target_points, variogram_params,
                max_samples, min_samples, search_radius
            )
    
    def _kriging_with_pykrige(
        self,
        samples: List[SamplePoint],
        target_points: List[Tuple[float, float, float]],
        params: VariogramParams,
        max_samples: int,
        min_samples: int,
        search_radius: Optional[float]
    ) -> List[BlockEstimate]:
        """Use PyKrige for kriging estimation."""
        estimates = []
        
        # Extract sample data - use 2D kriging (x, y only)
        x = np.array([s.x for s in samples])
        y = np.array([s.y for s in samples])
        vals = np.array([s.value for s in samples])
        
        # Map our model to PyKrige model names
        model_map = {
            VariogramModel.SPHERICAL: "spherical",
            VariogramModel.EXPONENTIAL: "exponential",
            VariogramModel.GAUSSIAN: "gaussian",
            VariogramModel.LINEAR: "linear",
        }
        
        try:
            # Create kriging object
            ok = OrdinaryKriging(
                x, y, vals,
                variogram_model=model_map.get(params.model, "spherical"),
                variogram_parameters={
                    "sill": params.sill,
                    "range": params.range,
                    "nugget": params.nugget
                },
                nlags=15,
                verbose=False
            )
            
            # Estimate at target points
            for i, (tx, ty, tz) in enumerate(target_points):
                try:
                    est_value, est_var = ok.execute(
                        "points", 
                        np.array([tx]), 
                        np.array([ty])
                    )
                    
                    estimates.append(BlockEstimate(
                        block_id=f"block_{i}",
                        x=tx,
                        y=ty,
                        z=tz,
                        estimated_value=float(est_value[0]),
                        estimation_variance=float(est_var[0]),
                        estimation_method="ordinary_kriging",
                        num_samples=len(samples)
                    ))
                except Exception:
                    # Fall back to IDW for this point
                    idw_est = self._idw_single_point(samples, tx, ty, tz)
                    estimates.append(BlockEstimate(
                        block_id=f"block_{i}",
                        x=tx,
                        y=ty,
                        z=tz,
                        estimated_value=idw_est,
                        estimation_variance=0.0,
                        estimation_method="idw_fallback",
                        num_samples=len(samples)
                    ))
                    
        except Exception as e:
            # Fall back to IDW for all points
            return self.inverse_distance_weighting(samples, target_points)
        
        return estimates
    
    def _kriging_simple(
        self,
        samples: List[SamplePoint],
        target_points: List[Tuple[float, float, float]],
        params: VariogramParams,
        max_samples: int,
        min_samples: int,
        search_radius: Optional[float]
    ) -> List[BlockEstimate]:
        """Simple kriging implementation without PyKrige."""
        # For simplicity, fall back to IDW when PyKrige is not available
        estimates = self.inverse_distance_weighting(samples, target_points)
        
        # Mark as kriging with fallback method
        for est in estimates:
            est.estimation_method = "idw_fallback"
        
        return estimates
    
    # =========================================================================
    # INVERSE DISTANCE WEIGHTING
    # =========================================================================
    
    def inverse_distance_weighting(
        self,
        samples: List[SamplePoint],
        target_points: List[Tuple[float, float, float]],
        power: float = 2.0,
        max_samples: int = 20,
        search_radius: Optional[float] = None
    ) -> List[BlockEstimate]:
        """
        Estimate using Inverse Distance Weighting.
        
        Args:
            samples: Sample data points
            target_points: Points to estimate
            power: Power parameter (higher = more weight to nearest)
            max_samples: Maximum samples to use
            search_radius: Optional search radius
            
        Returns:
            List of BlockEstimate
        """
        estimates = []
        
        for i, (tx, ty, tz) in enumerate(target_points):
            est_value = self._idw_single_point(
                samples, tx, ty, tz, power, max_samples, search_radius
            )
            
            estimates.append(BlockEstimate(
                block_id=f"block_{i}",
                x=tx,
                y=ty,
                z=tz,
                estimated_value=est_value,
                estimation_variance=0.0,  # IDW doesn't provide variance
                estimation_method="inverse_distance_weighting",
                num_samples=min(len(samples), max_samples)
            ))
        
        return estimates
    
    def _idw_single_point(
        self,
        samples: List[SamplePoint],
        tx: float, ty: float, tz: float,
        power: float = 2.0,
        max_samples: int = 20,
        search_radius: Optional[float] = None
    ) -> float:
        """Estimate a single point using IDW."""
        if not samples:
            return 0.0
        
        # Calculate distances
        distances = []
        for s in samples:
            d = math.sqrt((s.x - tx)**2 + (s.y - ty)**2 + (s.z - tz)**2)
            if search_radius is None or d <= search_radius:
                distances.append((d, s.value))
        
        if not distances:
            return 0.0
        
        # Sort by distance and take nearest
        distances.sort(key=lambda x: x[0])
        distances = distances[:max_samples]
        
        # Check for coincident point
        if distances[0][0] < 0.001:
            return distances[0][1]
        
        # Calculate IDW weights
        weights = []
        values = []
        for d, v in distances:
            if d > 0:
                w = 1.0 / (d ** power)
                weights.append(w)
                values.append(v)
        
        if not weights:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights)
        estimate = sum(w * v for w, v in zip(weights, values)) / total_weight
        
        return estimate
    
    # =========================================================================
    # CROSS-VALIDATION
    # =========================================================================
    
    def cross_validate(
        self,
        samples: List[SamplePoint],
        variogram_params: Optional[VariogramParams] = None,
        method: str = "kriging"
    ) -> float:
        """
        Perform leave-one-out cross-validation.
        
        Returns RMSE of cross-validation predictions.
        """
        if len(samples) < 5:
            return float('inf')
        
        errors_squared = []
        
        for i, target in enumerate(samples):
            # Use all other samples
            training = [s for j, s in enumerate(samples) if j != i]
            
            # Estimate the left-out point
            if method == "kriging":
                estimates = self.ordinary_kriging(
                    training, 
                    [(target.x, target.y, target.z)],
                    variogram_params
                )
            else:
                estimates = self.inverse_distance_weighting(
                    training,
                    [(target.x, target.y, target.z)]
                )
            
            if estimates:
                error = target.value - estimates[0].estimated_value
                errors_squared.append(error ** 2)
        
        if not errors_squared:
            return float('inf')
        
        rmse = math.sqrt(sum(errors_squared) / len(errors_squared))
        return rmse


# Singleton instance
_kriging_service: Optional[KrigingService] = None


def get_kriging_service() -> KrigingService:
    """Get the singleton kriging service instance."""
    global _kriging_service
    if _kriging_service is None:
        _kriging_service = KrigingService()
    return _kriging_service
