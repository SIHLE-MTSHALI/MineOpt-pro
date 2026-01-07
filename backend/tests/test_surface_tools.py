"""
Surface Tools Service Tests - Phase 11

Comprehensive tests for surface manipulation operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple


# Mock TINSurface data class for testing
@dataclass
class MockTINSurface:
    """Mock TIN surface for testing."""
    name: str = "Test Surface"
    surface_type: str = "terrain"
    vertices: List[Tuple[float, float, float]] = None
    triangles: List[Tuple[int, int, int]] = None
    
    def __post_init__(self):
        if self.vertices is None:
            self.vertices = []
        if self.triangles is None:
            self.triangles = []


class TestSurfaceTransformations:
    """Tests for surface transformation operations."""
    
    @pytest.fixture
    def sample_surface(self):
        """Create sample TIN surface."""
        return MockTINSurface(
            name="Test",
            vertices=[
                (0, 0, 100),
                (100, 0, 100),
                (100, 100, 100),
                (0, 100, 100),
                (50, 50, 110)
            ],
            triangles=[
                (0, 1, 4),
                (1, 2, 4),
                (2, 3, 4),
                (3, 0, 4)
            ]
        )
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_translate_surface(self, mock_db, sample_surface):
        """Test translating a surface."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        result = service.translate_surface(sample_surface, dx=50, dy=50, dz=10)
        
        assert result is not None
        # Check first vertex moved
        assert result.vertices[0][0] == 50  # 0 + 50
        assert result.vertices[0][1] == 50  # 0 + 50
        assert result.vertices[0][2] == 110  # 100 + 10
    
    def test_rotate_surface(self, mock_db, sample_surface):
        """Test rotating a surface around center."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        result = service.rotate_surface(
            sample_surface, 
            angle_degrees=90, 
            center_x=50, 
            center_y=50
        )
        
        assert result is not None
        assert len(result.vertices) == len(sample_surface.vertices)
    
    def test_scale_surface(self, mock_db, sample_surface):
        """Test scaling a surface."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        result = service.scale_surface(
            sample_surface,
            factor_xy=2.0,
            factor_z=1.5,
            center_x=50,
            center_y=50
        )
        
        assert result is not None
    
    def test_mirror_surface_x(self, mock_db, sample_surface):
        """Test mirroring a surface across X axis."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        result = service.mirror_surface(sample_surface, axis='x', axis_value=50)
        
        assert result is not None
        # Vertex at (0, 0, 100) should become (100, 0, 100)
        assert any(abs(v[0] - 100) < 0.01 and abs(v[1]) < 0.01 for v in result.vertices)


class TestSurfaceRefinement:
    """Tests for surface refinement operations."""
    
    @pytest.fixture
    def sample_surface(self):
        return MockTINSurface(
            vertices=[(0, 0, 0), (100, 0, 10), (100, 100, 5), (0, 100, 0), (50, 50, 20)],
            triangles=[(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
        )
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_smooth_surface(self, mock_db, sample_surface):
        """Test Laplacian smoothing."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        result = service.smooth_surface(
            sample_surface,
            iterations=1,
            factor=0.5
        )
        
        assert result is not None
        # Smoothing should reduce the high point
        center_idx = 4
        assert result.vertices[center_idx][2] < sample_surface.vertices[center_idx][2]
    
    def test_simplify_surface(self, mock_db, sample_surface):
        """Test surface simplification."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        
        # Add more vertices to simplify
        dense_surface = MockTINSurface(
            vertices=[(x, y, x*0.1 + y*0.1) for x in range(11) for y in range(11)],
            triangles=[]  # Would be generated
        )
        
        result = service.simplify_surface(dense_surface, target_vertex_count=25)
        
        assert result is not None
        assert len(result.vertices) <= 25
    
    def test_densify_surface(self, mock_db, sample_surface):
        """Test surface densification."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        initial_count = len(sample_surface.vertices)
        
        result = service.densify_surface(sample_surface, max_triangle_area=500)
        
        assert result is not None
        # Should have more vertices after densification
        assert len(result.vertices) >= initial_count


class TestSurfaceAnalysis:
    """Tests for surface analysis operations."""
    
    @pytest.fixture
    def sloped_surface(self):
        """Surface with known slope."""
        # 45° slope surface
        return MockTINSurface(
            vertices=[
                (0, 0, 0),
                (100, 0, 100),
                (100, 100, 100),
                (0, 100, 0)
            ],
            triangles=[(0, 1, 2), (0, 2, 3)]
        )
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_calculate_slope_at_point(self, mock_db, sloped_surface):
        """Test slope calculation at a point."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        slope, aspect = service.calculate_slope_at_point(sloped_surface, x=50, y=50)
        
        assert slope is not None
        assert aspect is not None
        assert 0 <= slope <= 90  # Degrees
        assert 0 <= aspect < 360
    
    def test_generate_slope_map(self, mock_db, sloped_surface):
        """Test slope map generation."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        result = service.calculate_slope_map(sloped_surface, grid_spacing=25)
        
        assert result is not None
        assert 'points' in result
        assert len(result['points']) > 0
        
        for point in result['points']:
            assert 'x' in point
            assert 'y' in point
            assert 'slope' in point
    
    def test_generate_elevation_profile(self, mock_db, sloped_surface):
        """Test elevation profile generation."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        result = service.generate_profile(
            sloped_surface,
            start=(0, 50),
            end=(100, 50),
            interval=10
        )
        
        assert result is not None
        assert 'points' in result
        assert len(result['points']) >= 2
        
        # First point should be lower than last (upward slope)
        assert result['points'][0]['z'] < result['points'][-1]['z']


class TestSurfaceInterpolation:
    """Tests for surface interpolation operations."""
    
    @pytest.fixture
    def terrain_surface(self):
        """Create terrain-like surface."""
        return MockTINSurface(
            vertices=[
                (0, 0, 100), (50, 0, 105), (100, 0, 100),
                (0, 50, 105), (50, 50, 120), (100, 50, 105),
                (0, 100, 100), (50, 100, 105), (100, 100, 100)
            ],
            triangles=[
                (0, 1, 3), (1, 4, 3), (1, 2, 4), (2, 5, 4),
                (3, 4, 6), (4, 7, 6), (4, 5, 7), (5, 8, 7)
            ]
        )
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_sample_elevation_at_point(self, mock_db, terrain_surface):
        """Test elevation sampling at a point."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        
        # Sample at center point (should be ~120)
        elevation = service.sample_elevation(terrain_surface, x=50, y=50)
        
        assert elevation is not None
        assert 110 < elevation < 130
    
    def test_drape_points_to_surface(self, mock_db, terrain_surface):
        """Test draping points onto surface."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        
        points = [(25, 25), (50, 50), (75, 75)]
        result = service.drape_points(terrain_surface, points)
        
        assert result is not None
        assert len(result) == 3
        
        for pt in result:
            assert len(pt) == 3  # x, y, z
    
    def test_sample_along_line(self, mock_db, terrain_surface):
        """Test sampling elevations along a line."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        
        result = service.sample_along_line(
            terrain_surface,
            start=(0, 50),
            end=(100, 50),
            interval=10
        )
        
        assert result is not None
        assert len(result) >= 2


class TestSurfaceGeometry:
    """Tests for surface geometry operations."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def sample_surface(self):
        return MockTINSurface(
            vertices=[
                (0, 0, 100), (100, 0, 100), (100, 100, 100),
                (0, 100, 100), (50, 50, 110)
            ],
            triangles=[(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
        )
    
    def test_clip_surface_to_boundary(self, mock_db, sample_surface):
        """Test clipping surface to boundary polygon."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        
        # Clip to smaller boundary
        boundary = [(25, 25), (75, 25), (75, 75), (25, 75)]
        result = service.clip_to_boundary(sample_surface, boundary)
        
        assert result is not None
    
    def test_merge_surfaces(self, mock_db, sample_surface):
        """Test merging multiple surfaces."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        service = SurfaceToolsService(mock_db)
        
        # Create second surface adjacent to first
        surface2 = MockTINSurface(
            vertices=[
                (100, 0, 100), (200, 0, 100), (200, 100, 100),
                (100, 100, 100), (150, 50, 110)
            ],
            triangles=[(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
        )
        
        result = service.merge_surfaces([sample_surface, surface2])
        
        assert result is not None
        # Merged surface should have more vertices
        assert len(result.vertices) >= len(sample_surface.vertices)


class TestIsopachCalculation:
    """Tests for isopach (thickness) calculations."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    def test_calculate_isopach(self, mock_db):
        """Test isopach thickness calculation between surfaces."""
        from app.services.surface_tools_service import SurfaceToolsService
        
        # Upper surface (floor)
        upper = MockTINSurface(
            vertices=[(0, 0, 100), (100, 0, 100), (100, 100, 100), (0, 100, 100)],
            triangles=[(0, 1, 2), (0, 2, 3)]
        )
        
        # Lower surface (roof)
        lower = MockTINSurface(
            vertices=[(0, 0, 90), (100, 0, 90), (100, 100, 90), (0, 100, 90)],
            triangles=[(0, 1, 2), (0, 2, 3)]
        )
        
        service = SurfaceToolsService(mock_db)
        result = service.calculate_isopach(upper, lower, grid_spacing=25)
        
        assert result is not None
        assert 'points' in result
        
        # Thickness should be ~10m throughout
        for pt in result['points']:
            assert 9 < pt['thickness'] < 11


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
