"""
CAD String Service Tests - Phase 11

Comprehensive tests for CAD string operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid
from datetime import datetime

# Mock the database models
import sys
sys.modules['app.domain.models_surface'] = Mock()
sys.modules['app.database'] = Mock()


class TestCADStringService:
    """Tests for CADStringService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def sample_string(self):
        """Create sample CAD string data."""
        return {
            'string_id': str(uuid.uuid4()),
            'site_id': 'test-site',
            'name': 'Test String',
            'string_type': 'boundary',
            'vertex_data': [[0, 0, 100], [100, 0, 100], [100, 100, 100], [0, 100, 100]],
            'is_closed': True,
            'layer': 'DEFAULT',
            'color': '#ff0000',
            'line_weight': 1.0,
            'created_at': datetime.utcnow()
        }
    
    # =========================================================================
    # CRUD Tests
    # =========================================================================
    
    def test_create_string(self, mock_db, sample_string):
        """Test creating a new CAD string."""
        from app.services.cad_string_service import CADStringService
        
        service = CADStringService(mock_db)
        
        result = service.create_string(
            site_id=sample_string['site_id'],
            name=sample_string['name'],
            vertices=[(0, 0, 100), (100, 0, 100), (100, 100, 100)],
            string_type='boundary',
            is_closed=True
        )
        
        assert mock_db.add.called
        assert mock_db.commit.called
    
    def test_get_string_not_found(self, mock_db):
        """Test getting a non-existent string."""
        from app.services.cad_string_service import CADStringService
        
        service = CADStringService(mock_db)
        result = service.get_string('nonexistent-id')
        
        assert result is None
    
    def test_list_strings_by_site(self, mock_db):
        """Test listing strings by site."""
        from app.services.cad_string_service import CADStringService
        
        service = CADStringService(mock_db)
        result = service.list_strings('test-site')
        
        assert isinstance(result, list)
    
    def test_delete_string(self, mock_db, sample_string):
        """Test deleting a string."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.delete_string(sample_string['string_id'])
        
        assert result is True
        assert mock_db.delete.called
        assert mock_db.commit.called
    
    # =========================================================================
    # Vertex Operation Tests
    # =========================================================================
    
    def test_insert_vertex(self, mock_db):
        """Test inserting a vertex."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [100, 0, 0], [100, 100, 0]]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.insert_vertex('test-id', 1, (50, 0, 0))
        
        assert result is True
        assert len(mock_string.vertex_data) == 4
    
    def test_delete_vertex(self, mock_db):
        """Test deleting a vertex."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [50, 0, 0], [100, 0, 0]]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.delete_vertex('test-id', 1)
        
        assert result is True
        assert len(mock_string.vertex_data) == 2
    
    def test_move_vertex(self, mock_db):
        """Test moving a vertex."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [100, 0, 0], [100, 100, 0]]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.move_vertex('test-id', 1, 150, 0, 0)
        
        assert result is True
        assert mock_string.vertex_data[1] == [150, 0, 0]
    
    # =========================================================================
    # Geometry Operation Tests
    # =========================================================================
    
    def test_calculate_length(self, mock_db):
        """Test length calculation."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [100, 0, 0]]  # 100m line
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.calculate_length('test-id')
        
        assert result == pytest.approx(100.0)
    
    def test_calculate_length_3d(self, mock_db):
        """Test 3D length calculation."""
        from app.services.cad_string_service import CADStringService
        
        # 3D diagonal line
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [100, 100, 100]]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.calculate_length('test-id')
        
        expected = (100**2 + 100**2 + 100**2) ** 0.5  # ~173.2
        assert result == pytest.approx(expected, rel=0.01)
    
    def test_calculate_area_closed(self, mock_db):
        """Test area calculation for closed polygon."""
        from app.services.cad_string_service import CADStringService
        
        # 100m x 100m square
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 100, 0]]
        mock_string.is_closed = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.calculate_area('test-id')
        
        assert result == pytest.approx(10000.0)  # 100 * 100
    
    def test_reverse_string(self, mock_db):
        """Test reversing string vertices."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [50, 0, 0], [100, 0, 0]]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.reverse_string('test-id')
        
        assert result is True
        assert mock_string.vertex_data[0] == [100, 0, 0]
        assert mock_string.vertex_data[2] == [0, 0, 0]
    
    def test_close_string(self, mock_db):
        """Test closing an open string."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.is_closed = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.close_string('test-id')
        
        assert result is True
        assert mock_string.is_closed is True
    
    # =========================================================================
    # Analysis Tests
    # =========================================================================
    
    def test_calculate_gradient(self, mock_db):
        """Test gradient calculation."""
        from app.services.cad_string_service import CADStringService
        
        # 10% grade: 100m horizontal, 10m vertical
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [100, 0, 10]]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.calculate_gradient('test-id')
        
        assert 'min_gradient' in result
        assert 'max_gradient' in result
        assert 'avg_gradient' in result
        assert result['avg_gradient'] == pytest.approx(10.0, rel=0.1)


class TestCADStringGeometry:
    """Tests for advanced geometry operations."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_split_string(self, mock_db):
        """Test splitting a string."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [50, 0, 0], [100, 0, 0], [150, 0, 0]]
        mock_string.site_id = 'test-site'
        mock_string.name = 'Test'
        mock_string.string_type = 'boundary'
        mock_string.layer = 'DEFAULT'
        mock_string.is_closed = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        str1, str2 = service.split_string('test-id', 2)
        
        # Should create two new strings
        assert mock_db.add.called
    
    def test_smooth_string(self, mock_db):
        """Test smoothing a string."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [50, 10, 0], [100, 0, 0]]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.smooth_string('test-id', iterations=1)
        
        assert result is True
    
    def test_simplify_string(self, mock_db):
        """Test simplifying a string."""
        from app.services.cad_string_service import CADStringService
        
        # Dense points that should be simplified
        mock_string = Mock()
        mock_string.vertex_data = [
            [0, 0, 0], [10, 0.1, 0], [20, 0, 0], [30, 0.1, 0],
            [40, 0, 0], [50, 0.1, 0], [60, 0, 0]
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.simplify_string('test-id', tolerance=1.0)
        
        assert result is True
        # Should have fewer vertices after simplification


class TestCADStringTypes:
    """Tests for string type handling."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_get_string_types(self, mock_db):
        """Test getting available string types."""
        from app.services.cad_string_service import CADStringService
        
        service = CADStringService(mock_db)
        types = service.get_string_types()
        
        assert isinstance(types, list)
        assert len(types) > 0
        
        # Check structure
        for t in types:
            assert 'value' in t
            assert 'name' in t
    
    def test_export_to_dxf_entities(self, mock_db):
        """Test DXF export data generation."""
        from app.services.cad_string_service import CADStringService
        
        mock_string = Mock()
        mock_string.vertex_data = [[0, 0, 0], [100, 0, 0], [100, 100, 0]]
        mock_string.is_closed = False
        mock_string.layer = 'BOUNDARY'
        mock_string.color = '#ff0000'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_string
        
        service = CADStringService(mock_db)
        result = service.export_to_dxf_entities('test-id')
        
        assert result is not None
        assert 'vertices' in result or 'points' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
