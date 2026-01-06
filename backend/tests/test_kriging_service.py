"""
Unit Tests for Kriging Service - Phase 3 Verification

Tests for:
- Experimental variogram calculation
- Variogram model fitting
- Ordinary kriging estimation
- IDW estimation
- Cross-validation
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.kriging_service import (
    KrigingService,
    SamplePoint,
    VariogramParams,
    VariogramModel,
    ExperimentalVariogram,
    BlockEstimate,
    get_kriging_service
)


class TestSamplePoint:
    """Tests for SamplePoint dataclass."""
    
    def test_create_sample_point(self):
        """Test creating a sample point."""
        point = SamplePoint(x=100.0, y=200.0, z=50.0, value=25.5)
        
        assert point.x == 100.0
        assert point.y == 200.0
        assert point.z == 50.0
        assert point.value == 25.5
        assert point.weight == 1.0
        assert point.hole_id is None
    
    def test_sample_point_with_hole_id(self):
        """Test sample point with hole ID."""
        point = SamplePoint(
            x=100.0, y=200.0, z=50.0, 
            value=25.5, 
            hole_id="BH001"
        )
        
        assert point.hole_id == "BH001"


class TestVariogramParams:
    """Tests for VariogramParams dataclass."""
    
    def test_create_variogram_params(self):
        """Test creating variogram parameters."""
        params = VariogramParams(
            model=VariogramModel.SPHERICAL,
            nugget=0.5,
            sill=10.0,
            range=100.0
        )
        
        assert params.model == VariogramModel.SPHERICAL
        assert params.nugget == 0.5
        assert params.sill == 10.0
        assert params.range == 100.0
    
    def test_partial_sill(self):
        """Test partial sill calculation."""
        params = VariogramParams(
            model=VariogramModel.SPHERICAL,
            nugget=2.0,
            sill=10.0,
            range=100.0
        )
        
        assert params.partial_sill == 8.0  # sill - nugget


class TestExperimentalVariogram:
    """Tests for experimental variogram calculation."""
    
    @pytest.fixture
    def kriging_service(self):
        return KrigingService()
    
    @pytest.fixture
    def sample_data(self):
        """Create synthetic sample data with known spatial structure."""
        samples = []
        np.random.seed(42)
        
        # Generate samples on a grid with some noise
        for i in range(5):
            for j in range(5):
                x = i * 20.0 + np.random.uniform(-2, 2)
                y = j * 20.0 + np.random.uniform(-2, 2)
                z = 0.0
                # Add spatial correlation to values
                value = 20.0 + 0.05 * x + 0.03 * y + np.random.uniform(-2, 2)
                samples.append(SamplePoint(x=x, y=y, z=z, value=value))
        
        return samples
    
    def test_calculate_experimental_variogram(self, kriging_service, sample_data):
        """Test experimental variogram calculation."""
        variogram = kriging_service.calculate_experimental_variogram(
            sample_data,
            num_lags=10
        )
        
        assert isinstance(variogram, ExperimentalVariogram)
        assert len(variogram.lags) == 10
        assert len(variogram.semivariances) == 10
        assert len(variogram.pair_counts) == 10
        
        # Verify lags are increasing
        for i in range(1, len(variogram.lags)):
            assert variogram.lags[i] > variogram.lags[i-1]
    
    def test_variogram_with_custom_lag_size(self, kriging_service, sample_data):
        """Test variogram with custom lag size."""
        variogram = kriging_service.calculate_experimental_variogram(
            sample_data,
            num_lags=5,
            lag_size=20.0
        )
        
        # Check lag spacing is approximately 20
        assert variogram.lags[0] == pytest.approx(10.0, rel=0.1)  # Midpoint of first bin


class TestVariogramFitting:
    """Tests for variogram model fitting."""
    
    @pytest.fixture
    def kriging_service(self):
        return KrigingService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data."""
        samples = []
        np.random.seed(42)
        
        for i in range(10):
            for j in range(10):
                x = i * 10.0
                y = j * 10.0
                z = 0.0
                value = 25.0 + np.random.uniform(-5, 5)
                samples.append(SamplePoint(x=x, y=y, z=z, value=value))
        
        return samples
    
    def test_fit_spherical_variogram(self, kriging_service, sample_data):
        """Test fitting spherical variogram."""
        experimental = kriging_service.calculate_experimental_variogram(sample_data)
        params = kriging_service.fit_variogram(experimental, VariogramModel.SPHERICAL)
        
        assert params.model == VariogramModel.SPHERICAL
        assert params.nugget >= 0
        assert params.sill > 0
        assert params.range > 0
    
    def test_fit_exponential_variogram(self, kriging_service, sample_data):
        """Test fitting exponential variogram."""
        experimental = kriging_service.calculate_experimental_variogram(sample_data)
        params = kriging_service.fit_variogram(experimental, VariogramModel.EXPONENTIAL)
        
        assert params.model == VariogramModel.EXPONENTIAL
    
    def test_auto_fit_variogram(self, kriging_service, sample_data):
        """Test automatic variogram fitting."""
        params = kriging_service.auto_fit_variogram(sample_data)
        
        assert params is not None
        assert params.model in [VariogramModel.SPHERICAL, VariogramModel.EXPONENTIAL, VariogramModel.GAUSSIAN]


class TestIDWEstimation:
    """Tests for Inverse Distance Weighting estimation."""
    
    @pytest.fixture
    def kriging_service(self):
        return KrigingService()
    
    @pytest.fixture
    def simple_samples(self):
        """Create simple sample data."""
        return [
            SamplePoint(x=0, y=0, z=0, value=10.0),
            SamplePoint(x=100, y=0, z=0, value=20.0),
            SamplePoint(x=0, y=100, z=0, value=15.0),
            SamplePoint(x=100, y=100, z=0, value=25.0),
        ]
    
    def test_idw_at_sample_location(self, kriging_service, simple_samples):
        """Test IDW at exact sample location returns sample value."""
        estimates = kriging_service.inverse_distance_weighting(
            simple_samples,
            [(0, 0, 0)]
        )
        
        assert len(estimates) == 1
        assert estimates[0].estimated_value == pytest.approx(10.0, rel=0.01)
    
    def test_idw_at_center(self, kriging_service, simple_samples):
        """Test IDW at center of four samples."""
        estimates = kriging_service.inverse_distance_weighting(
            simple_samples,
            [(50, 50, 0)]
        )
        
        # Should be weighted average of all four
        assert len(estimates) == 1
        # All equidistant, so should be mean
        expected = (10 + 20 + 15 + 25) / 4
        assert estimates[0].estimated_value == pytest.approx(expected, rel=0.1)
    
    def test_idw_multiple_targets(self, kriging_service, simple_samples):
        """Test IDW at multiple target points."""
        targets = [
            (25, 25, 0),
            (75, 75, 0),
        ]
        
        estimates = kriging_service.inverse_distance_weighting(
            simple_samples,
            targets
        )
        
        assert len(estimates) == 2
        assert estimates[0].estimation_method == "inverse_distance_weighting"
        assert estimates[1].estimation_method == "inverse_distance_weighting"
    
    def test_idw_with_different_powers(self, kriging_service, simple_samples):
        """Test IDW with different power parameters."""
        # Higher power = more weight to nearest samples
        targets = [(10, 10, 0)]
        
        estimates_p2 = kriging_service.inverse_distance_weighting(
            simple_samples, targets, power=2.0
        )
        
        estimates_p3 = kriging_service.inverse_distance_weighting(
            simple_samples, targets, power=3.0
        )
        
        # Both should be valid estimates
        assert estimates_p2[0].estimated_value > 0
        assert estimates_p3[0].estimated_value > 0


class TestOrdinaryKriging:
    """Tests for ordinary kriging estimation."""
    
    @pytest.fixture
    def kriging_service(self):
        return KrigingService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for kriging."""
        samples = []
        np.random.seed(42)
        
        for i in range(8):
            for j in range(8):
                x = i * 12.0 + np.random.uniform(-1, 1)
                y = j * 12.0 + np.random.uniform(-1, 1)
                z = 0.0
                value = 22.0 + 0.02 * x + 0.015 * y + np.random.uniform(-1.5, 1.5)
                samples.append(SamplePoint(x=x, y=y, z=z, value=value))
        
        return samples
    
    def test_ordinary_kriging_basic(self, kriging_service, sample_data):
        """Test basic ordinary kriging."""
        targets = [
            (40, 40, 0),
            (50, 50, 0),
        ]
        
        estimates = kriging_service.ordinary_kriging(
            sample_data,
            targets
        )
        
        assert len(estimates) == 2
        for est in estimates:
            assert isinstance(est, BlockEstimate)
            assert est.estimated_value > 0
            # Kriging should provide variance estimates
            assert hasattr(est, 'estimation_variance')
    
    def test_kriging_with_variogram(self, kriging_service, sample_data):
        """Test kriging with pre-fitted variogram."""
        variogram = kriging_service.auto_fit_variogram(sample_data)
        
        estimates = kriging_service.ordinary_kriging(
            sample_data,
            [(50, 50, 0)],
            variogram_params=variogram
        )
        
        assert len(estimates) == 1
        assert estimates[0].estimated_value > 0


class TestCrossValidation:
    """Tests for cross-validation."""
    
    @pytest.fixture
    def kriging_service(self):
        return KrigingService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data."""
        samples = []
        np.random.seed(42)
        
        for i in range(6):
            for j in range(6):
                x = i * 15.0
                y = j * 15.0
                z = 0.0
                value = 20.0 + np.random.uniform(-3, 3)
                samples.append(SamplePoint(x=x, y=y, z=z, value=value))
        
        return samples
    
    def test_cross_validation_kriging(self, kriging_service, sample_data):
        """Test cross-validation with kriging."""
        rmse = kriging_service.cross_validate(sample_data, method="kriging")
        
        assert rmse >= 0
        assert rmse < 100  # Should be reasonable for our data
    
    def test_cross_validation_idw(self, kriging_service, sample_data):
        """Test cross-validation with IDW."""
        rmse = kriging_service.cross_validate(sample_data, method="idw")
        
        assert rmse >= 0
    
    def test_cross_validation_insufficient_samples(self, kriging_service):
        """Test cross-validation with too few samples."""
        samples = [
            SamplePoint(x=0, y=0, z=0, value=10),
            SamplePoint(x=10, y=10, z=0, value=15),
        ]
        
        rmse = kriging_service.cross_validate(samples)
        
        # Should return infinity for insufficient data
        assert rmse == float('inf')


class TestSingleton:
    """Tests for singleton service access."""
    
    def test_get_kriging_service(self):
        """Test singleton pattern."""
        service1 = get_kriging_service()
        service2 = get_kriging_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
