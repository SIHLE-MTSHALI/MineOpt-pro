"""
Security and Quality Simulation Tests

Tests for Work Packages 9-12:
- Monte Carlo quality simulation
- Wash plant enhancements
- Security/session management
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


# =============================================================================
# Quality Simulation Tests (WP9)
# =============================================================================

class TestQualitySimulator:
    """Tests for Monte Carlo quality simulation."""
    
    def test_quality_distribution_sample_normal(self):
        """Test normal distribution sampling."""
        from app.services.quality_simulator import QualityDistribution
        
        dist = QualityDistribution(
            field_name="CV",
            mean=25.0,
            std_dev=0.5,
            distribution_type="normal"
        )
        
        samples = dist.sample(n_samples=1000)
        
        assert len(samples) == 1000
        assert abs(samples.mean() - 25.0) < 0.2  # Within tolerance
        assert samples.std() > 0.4  # Has variance
    
    def test_quality_distribution_sample_triangular(self):
        """Test triangular distribution sampling."""
        from app.services.quality_simulator import QualityDistribution
        
        dist = QualityDistribution(
            field_name="Ash",
            mean=15.0,
            min_val=10.0,
            max_val=20.0,
            distribution_type="triangular"
        )
        
        samples = dist.sample(n_samples=1000)
        
        assert len(samples) == 1000
        assert samples.min() >= 10.0
        assert samples.max() <= 20.0
    
    def test_simulator_blend_calculates_weighted_average(self):
        """Test blended quality is tonnage-weighted average."""
        from app.services.quality_simulator import (
            QualitySimulator, ParcelQualityModel, QualityDistribution
        )
        
        # Create two parcels with known qualities
        parcels = [
            ParcelQualityModel(
                parcel_id="p1",
                source_reference="",
                quantity_tonnes=100,
                quality_distributions={
                    "CV": QualityDistribution("CV", 20.0, 0.0)  # Zero std for predictable results
                }
            ),
            ParcelQualityModel(
                parcel_id="p2",
                source_reference="",
                quantity_tonnes=100,
                quality_distributions={
                    "CV": QualityDistribution("CV", 30.0, 0.0)
                }
            )
        ]
        
        simulator = QualitySimulator(n_simulations=100, random_seed=42)
        result = simulator.simulate_blend(parcels)
        
        # 50/50 blend should be 25.0
        assert abs(result.quality_stats["CV"]["mean"] - 25.0) < 0.1
    
    def test_simulator_spec_compliance(self):
        """Test specification compliance probability calculation."""
        from app.services.quality_simulator import (
            QualitySimulator, ParcelQualityModel, QualityDistribution, QualitySpec
        )
        
        # Create parcel that barely meets spec
        parcels = [
            ParcelQualityModel(
                parcel_id="p1",
                source_reference="",
                quantity_tonnes=100,
                quality_distributions={
                    "Ash": QualityDistribution("Ash", 14.0, 1.0)  # Mean 14, std 1
                }
            )
        ]
        
        specs = [
            QualitySpec(field_name="Ash", max_value=15.0, is_hard_constraint=True)
        ]
        
        simulator = QualitySimulator(n_simulations=1000, random_seed=42)
        result = simulator.simulate_blend(parcels, specs)
        
        # About 84% should meet spec (1 std above mean)
        assert 0.7 < result.spec_compliance.get("Ash", 0) < 0.95
        assert result.overall_compliance > 0.7
    
    def test_wash_plant_simulation_reduces_yield(self):
        """Test wash plant simulation reduces tonnage."""
        from app.services.quality_simulator import (
            QualitySimulator, ParcelQualityModel, QualityDistribution
        )
        
        parcels = [
            ParcelQualityModel(
                parcel_id="p1",
                source_reference="",
                quantity_tonnes=1000,
                quality_distributions={
                    "CV": QualityDistribution("CV", 22.0, 0.5),
                    "Ash": QualityDistribution("Ash", 18.0, 0.8)
                }
            )
        ]
        
        simulator = QualitySimulator(n_simulations=500, random_seed=42)
        result = simulator.simulate_with_wash_plant(
            parcels,
            yield_mean=0.85,
            yield_std=0.02
        )
        
        # Should have yield stats
        assert "yield" in result.quality_stats
        assert abs(result.quality_stats["yield"]["mean"] - 0.85) < 0.01
        
        # Should have output tonnes
        assert "output_tonnes" in result.quality_stats
        assert result.quality_stats["output_tonnes"]["mean"] < 1000  # Less than input
    
    def test_sensitivity_analysis_identifies_contributors(self):
        """Test sensitivity analysis identifies variance contributors."""
        from app.services.quality_simulator import (
            QualitySimulator, ParcelQualityModel, QualityDistribution
        )
        
        # One parcel with high variance, one with low
        parcels = [
            ParcelQualityModel(
                parcel_id="high_variance",
                source_reference="",
                quantity_tonnes=100,
                quality_distributions={
                    "CV": QualityDistribution("CV", 22.0, 2.0)  # High std
                }
            ),
            ParcelQualityModel(
                parcel_id="low_variance",
                source_reference="",
                quantity_tonnes=100,
                quality_distributions={
                    "CV": QualityDistribution("CV", 22.0, 0.1)  # Low std
                }
            )
        ]
        
        simulator = QualitySimulator(n_simulations=500, random_seed=42)
        result = simulator.simulate_blend(parcels)
        
        # High variance source should have higher sensitivity
        assert "high_variance" in result.sensitivity
        assert result.sensitivity["high_variance"] > result.sensitivity.get("low_variance", 0)


# =============================================================================
# Wash Plant Enhancement Tests (WP10)
# =============================================================================

class TestWashPlantEnhancements:
    """Tests for multi-stage wash plant processing."""
    
    def test_yield_adjustment_applies_corrections(self):
        """Test yield adjustment applies all correction factors."""
        from app.services.wash_plant_service import WashPlantService
        
        service = WashPlantService()
        
        # Test with full adjustments
        adjusted = service.apply_yield_adjustment(
            theoretical_yield=0.90,
            misplacement_model={"near_gravity_factor": 0.02, "fines_factor": 0.01},
            efficiency_factor=0.95,
            historical_correction=0.98
        )
        
        # Expected: 0.90 * 0.95 * (1 - 0.03) * 0.98 ≈ 0.813
        assert 0.80 < adjusted < 0.85
    
    def test_yield_adjustment_clamps_result(self):
        """Test yield adjustment clamps to 0-1 range."""
        from app.services.wash_plant_service import WashPlantService
        
        service = WashPlantService()
        
        # Very low yield
        adjusted = service.apply_yield_adjustment(
            theoretical_yield=0.1,
            efficiency_factor=0.5,
            historical_correction=0.1
        )
        assert adjusted >= 0.0
        
        # Very high yield (edge case)
        adjusted = service.apply_yield_adjustment(
            theoretical_yield=1.0,
            efficiency_factor=1.0,
            historical_correction=1.0
        )
        assert adjusted <= 1.0
    
    def test_blend_qualities_weighted_correctly(self):
        """Test quality blending calculation."""
        from app.services.wash_plant_service import WashPlantService
        
        service = WashPlantService()
        
        q1 = {"CV": 20.0, "Ash": 15.0}
        q2 = {"CV": 30.0, "Ash": 10.0}
        
        blended = service._blend_qualities(q1, 100, q2, 100)
        
        assert abs(blended["CV"] - 25.0) < 0.01
        assert abs(blended["Ash"] - 12.5) < 0.01
    
    def test_blend_qualities_handles_zero_tonnes(self):
        """Test blend handles zero tonnage edge case."""
        from app.services.wash_plant_service import WashPlantService
        
        service = WashPlantService()
        
        blended = service._blend_qualities({}, 0, {}, 0)
        
        assert blended == {}


# =============================================================================
# Security Tests (WP12)
# =============================================================================

class TestSessionManager:
    """Tests for session management."""
    
    def test_create_session_success(self):
        """Test session creation."""
        from app.services.security import SessionManager
        
        manager = SessionManager(max_sessions_per_user=3)
        
        session = manager.create_session("user1", "127.0.0.1", "Chrome")
        
        assert session.user_id == "user1"
        assert session.ip_address == "127.0.0.1"
        assert session.is_active
    
    def test_session_limit_enforced(self):
        """Test concurrent session limit."""
        from app.services.security import SessionManager
        
        manager = SessionManager(max_sessions_per_user=2)
        
        # Create 3 sessions
        s1 = manager.create_session("user1", "1.1.1.1", "Browser1")
        s2 = manager.create_session("user1", "2.2.2.2", "Browser2")
        s3 = manager.create_session("user1", "3.3.3.3", "Browser3")
        
        # Should only have 2 active
        active = manager.get_user_sessions("user1")
        assert len(active) == 2
        
        # Oldest should be expired
        assert manager.validate_session(s1.session_id) is None
    
    def test_invalidate_session(self):
        """Test session invalidation."""
        from app.services.security import SessionManager
        
        manager = SessionManager()
        
        session = manager.create_session("user1", "127.0.0.1", "Chrome")
        assert manager.validate_session(session.session_id) is not None
        
        manager.invalidate_session(session.session_id)
        assert manager.validate_session(session.session_id) is None
    
    def test_invalidate_all_user_sessions(self):
        """Test force logout all sessions."""
        from app.services.security import SessionManager
        
        manager = SessionManager()
        
        manager.create_session("user1", "1.1.1.1", "B1")
        manager.create_session("user1", "2.2.2.2", "B2")
        
        assert len(manager.get_user_sessions("user1")) == 2
        
        manager.invalidate_user_sessions("user1")
        
        assert len(manager.get_user_sessions("user1")) == 0


class TestAuditLogger:
    """Tests for audit logging."""
    
    def test_log_entry_created(self):
        """Test audit entry creation."""
        from app.services.security import AuditLogger
        
        logger = AuditLogger()
        
        logger.log(
            user_id="user1",
            username="testuser",
            action="create",
            resource_type="schedule",
            resource_id="sched1",
            site_id="site1"
        )
        
        entries = logger.get_entries(user_id="user1")
        
        assert len(entries) == 1
        assert entries[0]["action"] == "create"
        assert entries[0]["resource_type"] == "schedule"
    
    def test_log_auth_event(self):
        """Test authentication event logging."""
        from app.services.security import AuditLogger
        
        logger = AuditLogger()
        
        logger.log_auth_event(
            event_type="login",
            username="testuser",
            success=True,
            ip_address="127.0.0.1"
        )
        
        entries = logger.get_entries(action="login")
        
        assert len(entries) == 1
        assert entries[0]["details"]["success"] is True
    
    def test_log_filtering(self):
        """Test log entry filtering."""
        from app.services.security import AuditLogger
        
        logger = AuditLogger()
        
        # Add mixed entries
        logger.log("user1", "u1", "create", "schedule", "s1", "site1")
        logger.log("user2", "u2", "update", "schedule", "s2", "site2")
        logger.log("user1", "u1", "delete", "task", "t1", "site1")
        
        # Filter by user
        entries = logger.get_entries(user_id="user1")
        assert len(entries) == 2
        
        # Filter by site
        entries = logger.get_entries(site_id="site2")
        assert len(entries) == 1
        
        # Filter by action
        entries = logger.get_entries(action="update")
        assert len(entries) == 1
    
    def test_log_max_entries(self):
        """Test log trimming."""
        from app.services.security import AuditLogger
        
        logger = AuditLogger(max_entries=100)
        
        # Add more than max
        for i in range(150):
            logger.log(f"user{i}", f"u{i}", "read", "resource", f"r{i}")
        
        entries = logger.get_entries(limit=1000)
        assert len(entries) <= 100


class TestSiteAccessChecker:
    """Tests for site access control."""
    
    def test_wildcard_access(self):
        """Test wildcard site access."""
        from app.services.security import SiteAccessChecker
        
        checker = SiteAccessChecker()
        checker._cache["admin"] = ["*"]
        
        assert checker.can_access_site("admin", "site1")
        assert checker.can_access_site("admin", "any_site")
    
    def test_specific_site_access(self):
        """Test specific site access."""
        from app.services.security import SiteAccessChecker
        
        checker = SiteAccessChecker()
        checker._cache["user1"] = ["site1", "site2"]
        
        assert checker.can_access_site("user1", "site1")
        assert checker.can_access_site("user1", "site2")
        assert not checker.can_access_site("user1", "site3")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
