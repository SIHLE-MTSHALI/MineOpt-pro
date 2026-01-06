"""
Unit Tests for Block Model Service - Phase 3 Verification

Tests for:
- Block model creation
- Grid generation
- Grade estimation integration
- Activity area creation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.block_model_service import (
    BlockModelService,
    BlockModelConfig,
    EstimationConfig,
    BlockModelResult,
    get_block_model_service
)
from app.services.kriging_service import VariogramModel


class TestBlockModelConfig:
    """Tests for BlockModelConfig."""
    
    def test_create_config(self):
        """Test creating a block model config."""
        config = BlockModelConfig(
            name="Test Model",
            site_id="site-001",
            block_size_x=10.0,
            block_size_y=10.0,
            block_size_z=5.0
        )
        
        assert config.name == "Test Model"
        assert config.site_id == "site-001"
        assert config.block_size_x == 10.0
        assert config.block_size_y == 10.0
        assert config.block_size_z == 5.0
        assert config.padding == 50.0  # Default
    
    def test_config_with_origin(self):
        """Test config with explicit origin."""
        config = BlockModelConfig(
            name="Test",
            site_id="site-001",
            origin_x=1000.0,
            origin_y=2000.0,
            origin_z=100.0,
            count_x=20,
            count_y=20,
            count_z=10
        )
        
        assert config.origin_x == 1000.0
        assert config.origin_y == 2000.0
        assert config.origin_z == 100.0
        assert config.count_x == 20


class TestEstimationConfig:
    """Tests for EstimationConfig."""
    
    def test_default_config(self):
        """Test default estimation config."""
        config = EstimationConfig(quality_field="CV_ARB")
        
        assert config.quality_field == "CV_ARB"
        assert config.method == "kriging"
        assert config.variogram_model == VariogramModel.SPHERICAL
        assert config.auto_fit_variogram == True
        assert config.max_samples == 20
        assert config.min_samples == 3
    
    def test_idw_config(self):
        """Test IDW estimation config."""
        config = EstimationConfig(
            quality_field="Ash",
            method="idw",
            idw_power=3.0
        )
        
        assert config.method == "idw"
        assert config.idw_power == 3.0


class TestBlockModelResult:
    """Tests for BlockModelResult."""
    
    def test_success_result(self):
        """Test successful result."""
        result = BlockModelResult(
            success=True,
            model_id="model-001",
            blocks_created=1000
        )
        
        assert result.success == True
        assert result.model_id == "model-001"
        assert result.blocks_created == 1000
        assert result.errors == []
    
    def test_failure_result(self):
        """Test failure result."""
        result = BlockModelResult(
            success=False,
            errors=["Not enough samples"]
        )
        
        assert result.success == False
        assert "Not enough samples" in result.errors


class TestBlockModelService:
    """Tests for BlockModelService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return BlockModelService(mock_db)
    
    def test_create_block_model_requires_origin(self, service):
        """Test that origin is required if not auto-calculated."""
        config = BlockModelConfig(
            name="Test",
            site_id="site-001"
            # No origin or collar_ids
        )
        
        result = service.create_block_model(config)
        
        assert result.success == False
        assert len(result.errors) > 0
    
    def test_create_block_model_with_origin(self, service, mock_db):
        """Test creating block model with explicit origin."""
        config = BlockModelConfig(
            name="Test Model",
            site_id="site-001",
            origin_x=0.0,
            origin_y=0.0,
            origin_z=0.0,
            count_x=5,
            count_y=5,
            count_z=3,
            block_size_x=10.0,
            block_size_y=10.0,
            block_size_z=5.0
        )
        
        # Mock the add/flush behavior
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        result = service.create_block_model(config)
        
        assert result.success == True
        assert result.blocks_created == 5 * 5 * 3  # 75 blocks
    
    def test_get_model(self, service, mock_db):
        """Test getting a model by ID."""
        mock_model = Mock()
        mock_model.model_id = "model-001"
        mock_model.name = "Test Model"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_model
        
        model = service.get_model("model-001")
        
        assert model is not None
        assert model.model_id == "model-001"
    
    def test_get_model_not_found(self, service, mock_db):
        """Test getting non-existent model."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        model = service.get_model("nonexistent")
        
        assert model is None


class TestBlockGeneration:
    """Tests for block generation logic."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = Mock()
        db.flush = Mock()
        db.commit = Mock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return BlockModelService(mock_db)
    
    def test_generate_correct_block_count(self, service, mock_db):
        """Test that correct number of blocks are generated."""
        config = BlockModelConfig(
            name="Test",
            site_id="site-001",
            origin_x=0.0,
            origin_y=0.0,
            origin_z=0.0,
            count_x=3,
            count_y=4,
            count_z=2,
            block_size_x=10.0,
            block_size_y=10.0,
            block_size_z=5.0
        )
        
        result = service.create_block_model(config)
        
        expected_blocks = 3 * 4 * 2  # 24
        assert result.blocks_created == expected_blocks


class TestBlockVisualization:
    """Tests for visualization data retrieval."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session with blocks."""
        db = MagicMock()
        
        # Create mock blocks
        mock_blocks = []
        for i in range(3):
            for j in range(3):
                block = Mock()
                block.block_id = f"block-{i}-{j}"
                block.i = i
                block.j = j
                block.k = 0
                block.centroid_x = i * 10.0 + 5
                block.centroid_y = j * 10.0 + 5
                block.centroid_z = 2.5
                block.primary_value = 22.0 + i + j * 0.5
                block.primary_field = "CV"
                block.quality_vector = {"CV": 22.0 + i + j * 0.5}
                block.estimation_variance = 1.5
                block.material_type_id = None
                block.is_mineable = True
                mock_blocks.append(block)
        
        db.query.return_value.filter.return_value.all.return_value = mock_blocks
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return BlockModelService(mock_db)
    
    def test_get_blocks_for_visualization(self, service):
        """Test getting visualization data."""
        blocks = service.get_blocks_for_visualization("model-001")
        
        assert len(blocks) == 9  # 3x3 grid
        
        for block in blocks:
            assert "block_id" in block
            assert "x" in block
            assert "y" in block
            assert "z" in block
            assert "value" in block
    
    def test_get_blocks_with_quality_field(self, service):
        """Test getting blocks with specific quality field."""
        blocks = service.get_blocks_for_visualization("model-001", quality_field="CV")
        
        assert len(blocks) == 9
        # Values should come from quality_vector["CV"]
        for block in blocks:
            assert block["value"] is not None


class TestActivityAreaCreation:
    """Tests for creating activity areas from blocks."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        
        # Mock model
        mock_model = Mock()
        mock_model.model_id = "model-001"
        mock_model.site_id = "site-001"
        mock_model.block_size_x = 10.0
        mock_model.block_size_y = 10.0
        mock_model.block_size_z = 5.0
        
        # Create mock blocks with varied values
        mock_blocks = []
        for i in range(3):
            for j in range(3):
                block = Mock()
                block.block_id = f"block-{i}-{j}"
                block.i = i
                block.j = j
                block.k = 0
                block.centroid_x = i * 10.0 + 5
                block.centroid_y = j * 10.0 + 5
                block.centroid_z = 2.5
                # Vary values so some pass threshold
                block.primary_value = 20.0 + i * 2 + j
                block.is_mineable = True
                block.tonnes = 1000.0
                mock_blocks.append(block)
        
        # Set up query mocks
        db.query.return_value.filter.return_value.first.return_value = mock_model
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            b for b in mock_blocks if b.primary_value >= 24.0
        ]
        
        db.add = Mock()
        db.flush = Mock()  
        db.commit = Mock()
        
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return BlockModelService(mock_db)
    
    def test_create_activity_areas_basic(self, service):
        """Test creating activity areas from blocks."""
        area_ids = service.create_activity_areas_from_blocks(
            model_id="model-001",
            min_value=24.0,
            activity_type="Coal Mining"
        )
        
        # Should create at least one area (one per level with qualifying blocks)
        assert isinstance(area_ids, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
