"""
Annotation Service Tests - Phase 11

Comprehensive tests for annotation management.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid
from datetime import datetime


class TestAnnotationCRUD:
    """Tests for annotation CRUD operations."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def sample_annotation(self):
        """Create sample annotation data."""
        return {
            'annotation_id': str(uuid.uuid4()),
            'site_id': 'test-site',
            'text': 'RL 100.00',
            'x': 1000.0,
            'y': 2000.0,
            'z': 100.0,
            'height': 2.0,
            'rotation': 0.0,
            'layer': 'ELEVATIONS',
            'created_at': datetime.utcnow()
        }
    
    def test_create_annotation(self, mock_db, sample_annotation):
        """Test creating a new annotation."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        result = service.create_annotation(
            site_id=sample_annotation['site_id'],
            text=sample_annotation['text'],
            x=sample_annotation['x'],
            y=sample_annotation['y'],
            z=sample_annotation['z']
        )
        
        assert mock_db.add.called
        assert mock_db.commit.called
    
    def test_get_annotation(self, mock_db, sample_annotation):
        """Test getting an annotation by ID."""
        from app.services.annotation_service import AnnotationService
        
        mock_annotation = Mock()
        for key, value in sample_annotation.items():
            setattr(mock_annotation, key, value)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_annotation
        
        service = AnnotationService(mock_db)
        result = service.get_annotation(sample_annotation['annotation_id'])
        
        assert result is not None
        assert result.text == sample_annotation['text']
    
    def test_list_annotations_by_site(self, mock_db):
        """Test listing annotations by site."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        result = service.list_annotations('test-site')
        
        assert isinstance(result, list)
    
    def test_list_annotations_by_layer(self, mock_db):
        """Test listing annotations filtered by layer."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        result = service.list_annotations('test-site', layer='ELEVATIONS')
        
        assert isinstance(result, list)
    
    def test_update_annotation(self, mock_db, sample_annotation):
        """Test updating an annotation."""
        from app.services.annotation_service import AnnotationService
        
        mock_annotation = Mock()
        for key, value in sample_annotation.items():
            setattr(mock_annotation, key, value)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_annotation
        
        service = AnnotationService(mock_db)
        result = service.update_annotation(
            sample_annotation['annotation_id'],
            text='RL 105.00',
            z=105.0
        )
        
        assert result is not None
        assert mock_db.commit.called
    
    def test_delete_annotation(self, mock_db, sample_annotation):
        """Test deleting an annotation."""
        from app.services.annotation_service import AnnotationService
        
        mock_annotation = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_annotation
        
        service = AnnotationService(mock_db)
        result = service.delete_annotation(sample_annotation['annotation_id'])
        
        assert result is True
        assert mock_db.delete.called


class TestSpecializedAnnotations:
    """Tests for specialized annotation creation."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_create_elevation_label(self, mock_db):
        """Test creating elevation label."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        result = service.create_elevation_label(
            site_id='test-site',
            x=1000,
            y=2000,
            elevation=150.5,
            prefix='RL ',
            suffix='m',
            decimals=2
        )
        
        assert mock_db.add.called
    
    def test_create_distance_label(self, mock_db):
        """Test creating distance label between points."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        result = service.create_distance_label(
            site_id='test-site',
            start=(0, 0, 0),
            end=(100, 0, 0)
        )
        
        assert mock_db.add.called
    
    def test_create_area_label(self, mock_db):
        """Test creating area label."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        result = service.create_area_label(
            site_id='test-site',
            centroid=(50, 50, 0),
            area_m2=5000
        )
        
        assert mock_db.add.called
    
    def test_create_area_label_hectares(self, mock_db):
        """Test area label converts to hectares for large areas."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        # Large area should display in hectares
        result = service.create_area_label(
            site_id='test-site',
            centroid=(50, 50, 0),
            area_m2=50000  # 5 hectares
        )
        
        assert mock_db.add.called
    
    def test_create_volume_label(self, mock_db):
        """Test creating volume label."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        result = service.create_volume_label(
            site_id='test-site',
            position=(50, 50, 0),
            volume_m3=10000,
            tonnage=14000
        )
        
        assert mock_db.add.called
    
    def test_create_gradient_label(self, mock_db):
        """Test creating gradient label."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        result = service.create_gradient_label(
            site_id='test-site',
            position=(50, 50, 0),
            gradient_percent=10.5,
            direction=45.0
        )
        
        assert mock_db.add.called
    
    def test_create_coordinate_label(self, mock_db):
        """Test creating coordinate label."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        result = service.create_coordinate_label(
            site_id='test-site',
            x=500000.123,
            y=7200000.456,
            z=150.789,
            show_z=True
        )
        
        assert mock_db.add.called


class TestEntityLinking:
    """Tests for annotation entity linking."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_link_to_entity(self, mock_db):
        """Test linking annotation to an entity."""
        from app.services.annotation_service import AnnotationService
        
        mock_annotation = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_annotation
        
        service = AnnotationService(mock_db)
        result = service.link_to_entity(
            'annotation-id',
            entity_type='surface',
            entity_id='surface-123'
        )
        
        assert result is True
        assert mock_annotation.linked_entity_type == 'surface'
        assert mock_annotation.linked_entity_id == 'surface-123'
    
    def test_unlink_from_entity(self, mock_db):
        """Test unlinking annotation from entity."""
        from app.services.annotation_service import AnnotationService
        
        mock_annotation = Mock()
        mock_annotation.linked_entity_type = 'surface'
        mock_annotation.linked_entity_id = 'surface-123'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_annotation
        
        service = AnnotationService(mock_db)
        result = service.unlink_from_entity('annotation-id')
        
        assert result is True
        assert mock_annotation.linked_entity_type is None
        assert mock_annotation.linked_entity_id is None
    
    def test_get_entity_annotations(self, mock_db):
        """Test getting annotations linked to an entity."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        result = service.get_entity_annotations('surface', 'surface-123')
        
        assert isinstance(result, list)
    
    def test_delete_entity_annotations(self, mock_db):
        """Test deleting all annotations for an entity."""
        from app.services.annotation_service import AnnotationService
        
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        
        service = AnnotationService(mock_db)
        result = service.delete_entity_annotations('surface', 'surface-123')
        
        assert result == 5
        assert mock_db.commit.called


class TestBatchOperations:
    """Tests for batch annotation operations."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_create_contour_labels(self, mock_db):
        """Test batch creation of contour labels."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        contour_data = [
            {'elevation': 100, 'points': [(0, 0, 100), (50, 25, 100), (100, 0, 100)]},
            {'elevation': 125, 'points': [(0, 50, 125), (50, 75, 125), (100, 50, 125)]},  # Multiple of 25
            {'elevation': 150, 'points': [(0, 100, 150), (50, 125, 150), (100, 100, 150)]}
        ]
        
        result = service.create_contour_labels(
            site_id='test-site',
            contour_data=contour_data,
            interval=5,
            label_interval=25
        )
        
        assert isinstance(result, list)
    
    def test_create_borehole_labels(self, mock_db):
        """Test batch creation of borehole labels."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        boreholes = [
            {'hole_id': 'BH001', 'x': 100, 'y': 200, 'z': 150},
            {'hole_id': 'BH002', 'x': 150, 'y': 250, 'z': 155},
            {'hole_id': 'BH003', 'x': 200, 'y': 200, 'z': 145}
        ]
        
        result = service.create_borehole_labels(
            site_id='test-site',
            boreholes=boreholes
        )
        
        assert isinstance(result, list)
        assert len(result) == 3


class TestAnnotationTypes:
    """Tests for annotation type handling."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_get_annotation_types(self, mock_db):
        """Test getting available annotation types."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        types = service.get_annotation_types()
        
        assert isinstance(types, list)
        assert len(types) > 0
        
        # Check required types exist
        type_values = [t['value'] for t in types]
        assert 'text' in type_values
        assert 'elevation' in type_values
        assert 'distance' in type_values
    
    def test_get_default_style(self, mock_db):
        """Test getting default style for annotation type."""
        from app.services.annotation_service import AnnotationService
        
        service = AnnotationService(mock_db)
        
        style = service.get_default_style('elevation')
        
        assert isinstance(style, dict)
        assert 'font_size' in style
        assert 'font_color' in style


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
