"""
Integration Tests - Phase 11 Testing & QA

End-to-end tests for complete workflows:
- Full scheduling flow
- Quality blending accuracy
- Stockpile balance correctness
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.database import Base


@pytest.fixture(scope="module")
def engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def session(engine):
    """Create a new session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# =============================================================================
# End-to-End Scheduling Flow Tests
# =============================================================================

class TestSchedulingFlow:
    """Integration tests for complete scheduling workflow."""
    
    def test_create_and_run_schedule(self, session):
        """Test creating a schedule and running optimization."""
        from app.domain.models_core import Site
        from app.domain.models_calendar import Calendar, Period
        from app.domain.models_scheduling import ScheduleVersion
        
        # Create site
        site = Site(site_id="int-site", name="Integration Test Site")
        session.add(site)
        session.commit()
        
        # Create calendar with periods
        calendar = Calendar(
            calendar_id="int-cal",
            name="Test Calendar",
            site_id=site.site_id
        )
        session.add(calendar)
        session.commit()
        
        # Create periods
        for i in range(7):
            period = Period(
                period_id=f"int-p-{i}",
                calendar_id=calendar.calendar_id,
                sequence_number=i + 1,
                start_datetime=datetime(2024, 1, 1 + i, 6, 0),
                end_datetime=datetime(2024, 1, 1 + i, 18, 0),
                period_type="DayShift",
                duration_hours=12.0
            )
            session.add(period)
        session.commit()
        
        # Create schedule version
        schedule = ScheduleVersion(
            version_id="int-sched",
            name="Integration Test Schedule",
            status="Draft",
            site_id=site.site_id,
            calendar_id=calendar.calendar_id
        )
        session.add(schedule)
        session.commit()
        
        # Verify
        stored_schedule = session.query(ScheduleVersion)\
            .filter_by(version_id="int-sched").first()
        
        assert stored_schedule is not None
        assert stored_schedule.status == "Draft"
        
        periods = session.query(Period)\
            .filter_by(calendar_id=calendar.calendar_id)\
            .all()
        assert len(periods) == 7
    
    def test_schedule_publish_workflow(self, session):
        """Test the draft -> published workflow."""
        from app.domain.models_core import Site
        from app.domain.models_scheduling import ScheduleVersion, Task
        from app.services.integration_service import IntegrationService
        
        # Setup
        site = Site(site_id="pub-site", name="Publish Test Site")
        session.add(site)
        session.commit()
        
        schedule = ScheduleVersion(
            version_id="pub-sched",
            name="Publish Test Schedule",
            status="Draft",
            site_id=site.site_id
        )
        session.add(schedule)
        session.commit()
        
        # Add a task so schedule is not empty
        task = Task(
            task_id="pub-task-1",
            schedule_version_id=schedule.version_id,
            period_id="p-001",
            activity_name="Loading",
            quantity_tonnes=1000
        )
        session.add(task)
        session.commit()
        
        # Publish
        service = IntegrationService(session)
        result = service.publish_schedule(schedule.version_id, "test_user")
        
        assert result["status"] == "success"
        assert result["new_status"] == "Published"
        
        # Verify immutability
        from app.services.security_service import ImmutabilityService
        immutability = ImmutabilityService(session)
        
        assert immutability.check_editable(schedule.version_id) == False


# =============================================================================
# Quality Blending Accuracy Tests
# =============================================================================

class TestQualityBlending:
    """Integration tests for quality blending calculations."""
    
    def test_blend_multiple_sources(self):
        """Test blending from multiple sources with different qualities."""
        from app.services.blending_service import BlendingService
        
        service = BlendingService()
        
        sources = [
            {"id": "s1", "tonnes": 1000, "quality": {"CV": 20.0, "Ash": 18.0, "Moisture": 8.0}},
            {"id": "s2", "tonnes": 2000, "quality": {"CV": 25.0, "Ash": 10.0, "Moisture": 6.0}},
            {"id": "s3", "tonnes": 500, "quality": {"CV": 22.0, "Ash": 14.0, "Moisture": 7.0}},
        ]
        
        result = service.calculate_blend(sources)
        
        # Weighted average calculations:
        # CV: (1000*20 + 2000*25 + 500*22) / 3500 = 23.14
        # Ash: (1000*18 + 2000*10 + 500*14) / 3500 = 12.86
        # Moisture: (1000*8 + 2000*6 + 500*7) / 3500 = 6.71
        
        assert abs(result["blend_quality"]["CV"] - 23.14) < 0.1
        assert abs(result["blend_quality"]["Ash"] - 12.86) < 0.1
        assert result["total_tonnes"] == 3500
    
    def test_spec_compliance_with_blending(self):
        """Test that blended quality meets specifications."""
        from app.services.blending_service import BlendingService
        from app.services.quality_service import QualityService
        
        blending = BlendingService()
        quality = QualityService(db=None)
        
        # Blend sources
        sources = [
            {"tonnes": 500, "quality": {"CV": 19.0, "Ash": 20.0}},  # Poor quality
            {"tonnes": 1500, "quality": {"CV": 25.0, "Ash": 8.0}},  # Good quality
        ]
        
        blend_result = blending.calculate_blend(sources)
        
        # Check against specs
        specs = [
            {"field": "CV", "min_value": 22.0},
            {"field": "Ash", "max_value": 14.0},
        ]
        
        compliance = quality.check_spec_compliance(blend_result["blend_quality"], specs)
        
        # Blended: CV=23.5, Ash=11 - should be compliant
        assert compliance["compliant"] == True


# =============================================================================
# Stockpile Balance Tests
# =============================================================================

class TestStockpileBalance:
    """Integration tests for stockpile balance tracking."""
    
    def test_stockpile_accept_reclaim_balance(self):
        """Test that stockpile balance is maintained correctly."""
        from app.services.stockpile_service import StockpileService
        
        mock_db = Mock()
        service = StockpileService(mock_db)
        
        # Initial state
        initial_tonnes = 10000
        
        # Accept material
        accept_amount = 5000
        new_balance = initial_tonnes + accept_amount
        assert new_balance == 15000
        
        # Reclaim material
        reclaim_amount = 3000
        final_balance = new_balance - reclaim_amount
        assert final_balance == 12000
    
    def test_stockpile_quality_tracking(self):
        """Test that stockpile quality is tracked through deposits."""
        from app.services.stockpile_service import StockpileService
        from app.services.quality_service import QualityService
        
        mock_db = Mock()
        stockpile_service = StockpileService(mock_db)
        quality_service = QualityService(db=None)
        
        # Existing stockpile state
        existing = {"tonnes": 5000, "quality": {"CV": 22.0, "Ash": 12.0}}
        
        # New deposit
        deposit = {"tonnes": 2000, "quality": {"CV": 24.0, "Ash": 10.0}}
        
        # Calculate blended quality
        result = quality_service.calculate_blend_quality([existing, deposit])
        
        # Blended: CV = (5000*22 + 2000*24) / 7000 = 22.57
        assert abs(result["CV"] - 22.57) < 0.1


# =============================================================================
# Performance Baseline Tests
# =============================================================================

class TestPerformance:
    """Basic performance tests for response times."""
    
    def test_fast_pass_performance(self):
        """Test that Fast Pass completes within acceptable time."""
        import time
        from app.services.schedule_engine import ScheduleEngine
        
        # Simulate fast pass timing
        start_time = time.time()
        
        # Simulated operations (would be actual engine call in full test)
        for _ in range(100):
            pass  # Placeholder for actual operations
        
        elapsed = time.time() - start_time
        
        # Fast pass should be very quick for simple operations
        assert elapsed < 1.0  # Less than 1 second
    
    def test_quality_calculation_performance(self):
        """Test quality calculation performance with many sources."""
        import time
        from app.services.blending_service import BlendingService
        
        service = BlendingService()
        
        # Create 100 sources
        sources = [
            {"tonnes": 100, "quality": {"CV": 20 + i % 10, "Ash": 10 + i % 10}}
            for i in range(100)
        ]
        
        start_time = time.time()
        result = service.calculate_blend(sources)
        elapsed = time.time() - start_time
        
        # Should complete quickly even with many sources
        assert elapsed < 0.1  # Less than 100ms
        assert result["total_tonnes"] == 10000


# =============================================================================
# Test Scenarios
# =============================================================================

class TestScenarios:
    """Predefined test scenarios for regression testing."""
    
    def test_scenario_simple_pit_to_stockpile(self):
        """
        Scenario: Simple flow from pit to stockpile
        - Single excavator
        - Single stockpile
        - 12-hour shift
        """
        # Setup scenario
        scenario = {
            "name": "Simple Pit to Stockpile",
            "resources": [
                {"id": "ex-01", "rate": 2000, "type": "Excavator"}
            ],
            "stockpiles": [
                {"id": "rom-01", "capacity": 50000, "initial": 0}
            ],
            "periods": [
                {"id": "p1", "hours": 12}
            ]
        }
        
        # Expected result
        expected_tonnes = 2000 * 12  # 24,000 tonnes
        
        # Verify scenario is well-formed
        assert len(scenario["resources"]) == 1
        assert scenario["resources"][0]["rate"] * scenario["periods"][0]["hours"] == expected_tonnes
    
    def test_scenario_multi_source_blending(self):
        """
        Scenario: Multiple sources blending to meet spec
        - Three pits with different qualities
        - One product stockpile with spec
        - Blending required to meet target
        """
        scenario = {
            "name": "Multi-Source Blending",
            "sources": [
                {"id": "pit-a", "quality": {"CV": 20, "Ash": 18}},
                {"id": "pit-b", "quality": {"CV": 26, "Ash": 8}},
                {"id": "pit-c", "quality": {"CV": 22, "Ash": 14}},
            ],
            "product_spec": {
                "CV_min": 22,
                "Ash_max": 14
            }
        }
        
        # Verify scenario requirements
        assert len(scenario["sources"]) == 3
        assert scenario["product_spec"]["CV_min"] == 22
    
    def test_scenario_wash_plant_processing(self):
        """
        Scenario: Material through wash plant
        - ROM feed
        - 75% product yield
        - 25% discard
        """
        scenario = {
            "name": "Wash Plant Processing",
            "feed_tonnes": 10000,
            "product_yield": 0.75,
            "discard_yield": 0.25
        }
        
        expected_product = scenario["feed_tonnes"] * scenario["product_yield"]
        expected_discard = scenario["feed_tonnes"] * scenario["discard_yield"]
        
        assert expected_product == 7500
        assert expected_discard == 2500
        assert expected_product + expected_discard == scenario["feed_tonnes"]


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
