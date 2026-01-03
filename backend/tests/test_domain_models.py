"""
Domain Model Tests - Phase 11 Testing & QA

Unit tests for SQLAlchemy domain models to ensure
proper relationships, constraints, and data integrity.
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# Import all models
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.database import Base
from app.domain.models_core import User, Role, Site
from app.domain.models_calendar import Calendar, Period
from app.domain.models_resource import (
    MaterialType, QualityField, Activity, ActivityArea,
    Resource, ResourcePeriodParameters
)
from app.domain.models_flow import (
    FlowNetwork, FlowNode, FlowArc, StockpileConfig
)
from app.domain.models_scheduling import ScheduleVersion, Task


# Test Database Setup
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
# Site Model Tests
# =============================================================================

class TestSiteModel:
    """Tests for Site model."""
    
    def test_create_site(self, session):
        """Test creating a new site."""
        site = Site(
            site_id="site-001",
            name="Test Mine",
            location="South Africa",
            timezone="Africa/Johannesburg"
        )
        session.add(site)
        session.commit()
        
        retrieved = session.query(Site).filter_by(site_id="site-001").first()
        assert retrieved is not None
        assert retrieved.name == "Test Mine"
        assert retrieved.timezone == "Africa/Johannesburg"
    
    def test_site_unique_id(self, session):
        """Test that site_id must be unique."""
        site1 = Site(site_id="site-unique", name="Site 1")
        site2 = Site(site_id="site-unique", name="Site 2")
        
        session.add(site1)
        session.commit()
        
        session.add(site2)
        with pytest.raises(IntegrityError):
            session.commit()


# =============================================================================
# Calendar Model Tests
# =============================================================================

class TestCalendarModel:
    """Tests for Calendar and Period models."""
    
    def test_create_calendar(self, session):
        """Test creating a calendar with periods."""
        # First create a site
        site = Site(site_id="site-cal", name="Calendar Test Site")
        session.add(site)
        session.commit()
        
        calendar = Calendar(
            calendar_id="cal-001",
            name="Weekly Schedule",
            site_id=site.site_id
        )
        session.add(calendar)
        session.commit()
        
        assert calendar.calendar_id == "cal-001"
    
    def test_create_periods(self, session):
        """Test creating periods within a calendar."""
        site = Site(site_id="site-per", name="Period Test Site")
        session.add(site)
        session.commit()
        
        calendar = Calendar(
            calendar_id="cal-per",
            name="Test Calendar",
            site_id=site.site_id
        )
        session.add(calendar)
        session.commit()
        
        # Create day shift and night shift
        ds = Period(
            period_id="p-ds-1",
            calendar_id=calendar.calendar_id,
            sequence_number=1,
            start_datetime=datetime(2024, 1, 1, 6, 0),
            end_datetime=datetime(2024, 1, 1, 18, 0),
            period_type="DayShift",
            duration_hours=12.0
        )
        ns = Period(
            period_id="p-ns-1",
            calendar_id=calendar.calendar_id,
            sequence_number=2,
            start_datetime=datetime(2024, 1, 1, 18, 0),
            end_datetime=datetime(2024, 1, 2, 6, 0),
            period_type="NightShift",
            duration_hours=12.0
        )
        session.add_all([ds, ns])
        session.commit()
        
        periods = session.query(Period)\
            .filter_by(calendar_id=calendar.calendar_id)\
            .order_by(Period.sequence_number)\
            .all()
        
        assert len(periods) == 2
        assert periods[0].period_type == "DayShift"
        assert periods[1].period_type == "NightShift"


# =============================================================================
# Resource Model Tests
# =============================================================================

class TestResourceModel:
    """Tests for Resource model."""
    
    def test_create_resource(self, session):
        """Test creating a resource."""
        site = Site(site_id="site-res", name="Resource Test Site")
        session.add(site)
        session.commit()
        
        resource = Resource(
            resource_id="ex-001",
            name="Excavator 1",
            resource_type="Excavator",
            site_id=site.site_id,
            default_rate_per_hour=2000.0,
            rate_unit="tonnes"
        )
        session.add(resource)
        session.commit()
        
        retrieved = session.query(Resource).filter_by(resource_id="ex-001").first()
        assert retrieved is not None
        assert retrieved.name == "Excavator 1"
        assert retrieved.default_rate_per_hour == 2000.0
    
    def test_resource_activities(self, session):
        """Test resource with assigned activities."""
        site = Site(site_id="site-act", name="Activity Test Site")
        session.add(site)
        session.commit()
        
        activity = Activity(
            activity_id="act-loading",
            name="Loading",
            activity_type="Primary",
            site_id=site.site_id
        )
        session.add(activity)
        session.commit()
        
        resource = Resource(
            resource_id="ex-002",
            name="Excavator 2",
            resource_type="Excavator",
            site_id=site.site_id
        )
        session.add(resource)
        session.commit()
        
        assert resource.resource_id == "ex-002"


# =============================================================================
# Flow Network Model Tests
# =============================================================================

class TestFlowNetworkModel:
    """Tests for FlowNetwork, FlowNode, and FlowArc models."""
    
    def test_create_flow_network(self, session):
        """Test creating a flow network with nodes and arcs."""
        site = Site(site_id="site-flow", name="Flow Test Site")
        session.add(site)
        session.commit()
        
        network = FlowNetwork(
            network_id="net-001",
            name="Main Flow Network",
            site_id=site.site_id,
            is_default=True
        )
        session.add(network)
        session.commit()
        
        # Create nodes
        pit = FlowNode(
            node_id="pit-a",
            network_id=network.network_id,
            name="Pit A",
            node_type="SourcePit"
        )
        stockpile = FlowNode(
            node_id="rom-1",
            network_id=network.network_id,
            name="ROM Stockpile 1",
            node_type="Stockpile"
        )
        session.add_all([pit, stockpile])
        session.commit()
        
        # Create arc
        arc = FlowArc(
            arc_id="arc-001",
            network_id=network.network_id,
            source_node_id=pit.node_id,
            destination_node_id=stockpile.node_id,
            arc_name="Pit A to ROM 1"
        )
        session.add(arc)
        session.commit()
        
        # Verify
        nodes = session.query(FlowNode)\
            .filter_by(network_id=network.network_id)\
            .all()
        arcs = session.query(FlowArc)\
            .filter_by(network_id=network.network_id)\
            .all()
        
        assert len(nodes) == 2
        assert len(arcs) == 1
        assert arcs[0].source_node_id == "pit-a"
        assert arcs[0].destination_node_id == "rom-1"


# =============================================================================
# Schedule Model Tests
# =============================================================================

class TestScheduleModel:
    """Tests for ScheduleVersion and Task models."""
    
    def test_create_schedule_version(self, session):
        """Test creating a schedule version."""
        site = Site(site_id="site-sched", name="Schedule Test Site")
        session.add(site)
        session.commit()
        
        schedule = ScheduleVersion(
            version_id="sched-001",
            name="Weekly Plan",
            description="Week 1 production schedule",
            status="Draft",
            site_id=site.site_id
        )
        session.add(schedule)
        session.commit()
        
        retrieved = session.query(ScheduleVersion)\
            .filter_by(version_id="sched-001").first()
        
        assert retrieved is not None
        assert retrieved.name == "Weekly Plan"
        assert retrieved.status == "Draft"
    
    def test_create_task(self, session):
        """Test creating tasks within a schedule."""
        site = Site(site_id="site-task", name="Task Test Site")
        session.add(site)
        session.commit()
        
        schedule = ScheduleVersion(
            version_id="sched-task",
            name="Task Test Schedule",
            status="Draft",
            site_id=site.site_id
        )
        session.add(schedule)
        session.commit()
        
        task = Task(
            task_id="task-001",
            schedule_version_id=schedule.version_id,
            period_id="p-001",
            activity_name="Loading",
            quantity_tonnes=5000.0,
            duration_hours=2.5,
            start_offset_hours=0.0
        )
        session.add(task)
        session.commit()
        
        tasks = session.query(Task)\
            .filter_by(schedule_version_id=schedule.version_id)\
            .all()
        
        assert len(tasks) == 1
        assert tasks[0].quantity_tonnes == 5000.0


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
