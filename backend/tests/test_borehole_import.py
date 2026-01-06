"""
Unit Tests for Borehole Import Service - Phase 2 Verification

Tests for:
- Collar file parsing
- Survey file parsing  
- Assay file parsing
- 3D trace calculation
- Data validation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.borehole_import_service import (
    BoreholeImportService,
    CollarRecord,
    SurveyRecord,
    IntervalRecord,
    BoreholeImportResult,
    ValidationError
)


class TestCollarRecord:
    """Tests for CollarRecord dataclass."""
    
    def test_create_collar_record(self):
        """Test creating a collar record."""
        record = CollarRecord(
            hole_id="BH001",
            easting=524150.50,
            northing=7145230.25,
            elevation=1245.5,
            total_depth=85.0
        )
        
        assert record.hole_id == "BH001"
        assert record.easting == 524150.50
        assert record.northing == 7145230.25
        assert record.elevation == 1245.5
        assert record.total_depth == 85.0
        assert record.azimuth == 0.0  # Default
        assert record.dip == -90.0    # Default vertical
    
    def test_collar_with_deviation(self):
        """Test collar with azimuth and dip."""
        record = CollarRecord(
            hole_id="BH001",
            easting=524150.50,
            northing=7145230.25,
            elevation=1245.5,
            total_depth=85.0,
            azimuth=45.0,
            dip=-75.0
        )
        
        assert record.azimuth == 45.0
        assert record.dip == -75.0


class TestSurveyRecord:
    """Tests for SurveyRecord dataclass."""
    
    def test_create_survey_record(self):
        """Test creating a survey record."""
        record = SurveyRecord(
            hole_id="BH001",
            depth=30.0,
            azimuth=5.0,
            dip=-88.0
        )
        
        assert record.hole_id == "BH001"
        assert record.depth == 30.0
        assert record.azimuth == 5.0
        assert record.dip == -88.0


class TestIntervalRecord:
    """Tests for IntervalRecord dataclass."""
    
    def test_create_interval_record(self):
        """Test creating an interval record."""
        record = IntervalRecord(
            hole_id="BH001",
            from_depth=45.2,
            to_depth=48.5,
            seam="Upper"
        )
        
        assert record.hole_id == "BH001"
        assert record.from_depth == 45.2
        assert record.to_depth == 48.5
        assert record.seam == "Upper"
    
    def test_interval_with_quality(self):
        """Test interval with quality data."""
        record = IntervalRecord(
            hole_id="BH001",
            from_depth=45.2,
            to_depth=48.5,
            quality_data={"CV_ARB": 24.5, "Ash_ADB": 12.3}
        )
        
        assert record.quality_data["CV_ARB"] == 24.5
        assert record.quality_data["Ash_ADB"] == 12.3
    
    def test_interval_thickness(self):
        """Test interval thickness calculation."""
        record = IntervalRecord(
            hole_id="BH001",
            from_depth=45.2,
            to_depth=48.5
        )
        
        assert record.thickness == pytest.approx(3.3, rel=0.01)


class TestBoreholeImportService:
    """Tests for BoreholeImportService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = Mock()
        db.flush = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return BoreholeImportService(mock_db)
    
    @pytest.fixture
    def sample_collar_csv(self):
        """Sample collar CSV content."""
        return b"""HoleID,Easting,Northing,Elevation,TotalDepth,Azimuth,Dip
BH001,524150.50,7145230.25,1245.5,85.0,0,90
BH002,524200.75,7145280.10,1248.2,92.5,0,90
BH003,524180.00,7145350.00,1250.1,78.3,0,90
"""
    
    @pytest.fixture
    def sample_survey_csv(self):
        """Sample survey CSV content."""
        return b"""HoleID,Depth,Azimuth,Dip
BH001,0.0,0,90
BH001,30.0,2,88
BH001,60.0,5,85
BH002,0.0,0,90
BH002,45.0,3,87
"""
    
    @pytest.fixture
    def sample_assay_csv(self):
        """Sample assay CSV content."""
        return b"""HoleID,From,To,Seam,CV_ARB,Ash_ADB,Moisture,Sulphur
BH001,45.2,48.5,Upper,24.5,12.3,8.5,0.45
BH001,52.0,54.8,Lower,22.8,15.1,9.2,0.52
BH002,42.8,46.2,Upper,25.1,11.8,8.1,0.42
"""
    
    def test_parse_collar_file(self, service, sample_collar_csv):
        """Test parsing collar CSV file."""
        collars = service.parse_collar_file(sample_collar_csv, "collar.csv")
        
        assert len(collars) == 3
        
        assert collars[0].hole_id == "BH001"
        assert collars[0].easting == 524150.50
        assert collars[0].northing == 7145230.25
        assert collars[0].elevation == 1245.5
        assert collars[0].total_depth == 85.0
    
    def test_parse_survey_file(self, service, sample_survey_csv):
        """Test parsing survey CSV file."""
        surveys = service.parse_survey_file(sample_survey_csv, "survey.csv")
        
        assert len(surveys) == 5
        
        # Check BH001 surveys
        bh001_surveys = [s for s in surveys if s.hole_id == "BH001"]
        assert len(bh001_surveys) == 3
        
        assert bh001_surveys[0].depth == 0.0
        assert bh001_surveys[1].depth == 30.0
        assert bh001_surveys[2].depth == 60.0
    
    def test_parse_assay_file(self, service, sample_assay_csv):
        """Test parsing assay CSV file."""
        intervals = service.parse_assay_file(
            sample_assay_csv, 
            "assay.csv",
            quality_columns=["CV_ARB", "Ash_ADB", "Moisture", "Sulphur"]
        )
        
        assert len(intervals) == 3
        
        assert intervals[0].hole_id == "BH001"
        assert intervals[0].from_depth == 45.2
        assert intervals[0].to_depth == 48.5
        assert intervals[0].seam == "Upper"
        assert intervals[0].quality_data["CV_ARB"] == 24.5


class TestTraceCalculation:
    """Tests for 3D trace calculation."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return BoreholeImportService(mock_db)
    
    def test_vertical_trace(self, service):
        """Test trace calculation for vertical hole."""
        collar = CollarRecord(
            hole_id="BH001",
            easting=1000.0,
            northing=2000.0,
            elevation=500.0,
            total_depth=100.0,
            azimuth=0.0,
            dip=-90.0  # Vertical
        )
        
        surveys = [
            SurveyRecord(hole_id="BH001", depth=0, azimuth=0, dip=-90),
            SurveyRecord(hole_id="BH001", depth=50, azimuth=0, dip=-90),
            SurveyRecord(hole_id="BH001", depth=100, azimuth=0, dip=-90),
        ]
        
        trace = service.calculate_3d_trace(collar, surveys, interval_meters=25.0)
        
        assert len(trace) > 0
        
        # First point should be at collar
        assert trace[0][0] == pytest.approx(1000.0, rel=0.01)  # X
        assert trace[0][1] == pytest.approx(2000.0, rel=0.01)  # Y
        assert trace[0][2] == pytest.approx(500.0, rel=0.01)   # Z
        
        # Vertical hole - X and Y should remain constant
        for point in trace:
            assert point[0] == pytest.approx(1000.0, rel=0.1)
            assert point[1] == pytest.approx(2000.0, rel=0.1)
    
    def test_inclined_trace(self, service):
        """Test trace calculation for inclined hole."""
        collar = CollarRecord(
            hole_id="BH001",
            easting=1000.0,
            northing=2000.0,
            elevation=500.0,
            total_depth=100.0,
            azimuth=90.0,   # East
            dip=-45.0       # 45 degree inclination
        )
        
        surveys = [
            SurveyRecord(hole_id="BH001", depth=0, azimuth=90, dip=-45),
            SurveyRecord(hole_id="BH001", depth=100, azimuth=90, dip=-45),
        ]
        
        trace = service.calculate_3d_trace(collar, surveys, interval_meters=25.0)
        
        assert len(trace) > 0
        
        # Hole should drift east
        last_point = trace[-1]
        assert last_point[0] > 1000.0  # X should increase (east)


class TestDataValidation:
    """Tests for data validation."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return BoreholeImportService(mock_db)
    
    def test_validate_survey_depth(self, service):
        """Test that survey depth must not exceed total depth."""
        collar = CollarRecord(
            hole_id="BH001",
            easting=1000.0,
            northing=2000.0,
            elevation=500.0,
            total_depth=50.0
        )
        
        surveys = [
            SurveyRecord(hole_id="BH001", depth=0, azimuth=0, dip=-90),
            SurveyRecord(hole_id="BH001", depth=60, azimuth=0, dip=-90),  # Exceeds total depth
        ]
        
        errors = service.validate_surveys(collar, surveys)
        
        assert len(errors) > 0
        assert any("depth" in str(e).lower() for e in errors)
    
    def test_validate_interval_depth(self, service):
        """Test that interval must be within total depth."""
        collar = CollarRecord(
            hole_id="BH001",
            easting=1000.0,
            northing=2000.0,
            elevation=500.0,
            total_depth=50.0
        )
        
        intervals = [
            IntervalRecord(hole_id="BH001", from_depth=40.0, to_depth=55.0),  # Exceeds
        ]
        
        errors = service.validate_intervals(collar, intervals)
        
        assert len(errors) > 0
    
    def test_validate_interval_order(self, service):
        """Test that from_depth must be less than to_depth."""
        intervals = [
            IntervalRecord(hole_id="BH001", from_depth=50.0, to_depth=45.0),  # Invalid
        ]
        
        errors = service.validate_interval_order(intervals)
        
        assert len(errors) > 0


class TestImportResult:
    """Tests for BoreholeImportResult."""
    
    def test_success_result(self):
        """Test successful import result."""
        result = BoreholeImportResult(
            success=True,
            collars_imported=10,
            surveys_imported=50,
            intervals_imported=30
        )
        
        assert result.success == True
        assert result.collars_imported == 10
        assert result.surveys_imported == 50
        assert result.intervals_imported == 30
    
    def test_result_with_warnings(self):
        """Test result with warnings."""
        result = BoreholeImportResult(
            success=True,
            collars_imported=10,
            warnings=["Duplicate hole ID found: BH001"]
        )
        
        assert result.success == True
        assert len(result.warnings) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
