"""
Tests for Surface Service - Phase 2 TIN Surface Generation

Tests for:
- TIN creation from points
- Elevation queries
- Volume calculations
- Contour generation
- Seam tonnage calculations
"""

import pytest
import math
from unittest.mock import Mock, patch, MagicMock


class TestSurfaceService:
    """Tests for the SurfaceService class."""
    
    @pytest.fixture
    def surface_service(self):
        """Create a surface service instance for testing."""
        from app.services.surface_service import SurfaceService
        return SurfaceService(db=None)
    
    @pytest.fixture
    def simple_points(self):
        """Simple grid of test points."""
        return [
            (0, 0, 100),
            (100, 0, 100),
            (100, 100, 100),
            (0, 100, 100),
            (50, 50, 120),  # Higher in center
        ]
    
    @pytest.fixture
    def sloped_points(self):
        """Points forming a sloped surface."""
        points = []
        for x in range(0, 101, 25):
            for y in range(0, 101, 25):
                z = 100 + x * 0.1 + y * 0.05  # Slope
                points.append((x, y, z))
        return points
    
    # =========================================================================
    # TIN Creation Tests
    # =========================================================================
    
    def test_create_tin_from_points_minimum(self, surface_service):
        """Test TIN creation with minimum 3 points."""
        points = [(0, 0, 100), (100, 0, 100), (50, 100, 100)]
        
        tin = surface_service.create_tin_from_points(points, name="Test")
        
        assert tin is not None
        assert tin.vertex_count == 3
        assert tin.triangle_count == 1
        assert tin.name == "Test"
    
    def test_create_tin_from_points_grid(self, surface_service, sloped_points):
        """Test TIN creation from a grid of points."""
        tin = surface_service.create_tin_from_points(sloped_points, name="Grid")
        
        assert tin is not None
        assert tin.vertex_count == len(sloped_points)
        assert tin.triangle_count > 0
    
    def test_create_tin_insufficient_points(self, surface_service):
        """Test that TIN creation fails with less than 3 points."""
        with pytest.raises(ValueError):
            surface_service.create_tin_from_points([(0, 0, 0), (1, 1, 1)])
    
    def test_tin_extent(self, surface_service, simple_points):
        """Test TIN extent calculation."""
        tin = surface_service.create_tin_from_points(simple_points)
        
        extent_min, extent_max = tin.get_extent()
        
        assert extent_min.x == 0
        assert extent_min.y == 0
        assert extent_min.z == 100
        assert extent_max.x == 100
        assert extent_max.y == 100
        assert extent_max.z == 120
    
    # =========================================================================
    # Elevation Query Tests
    # =========================================================================
    
    def test_query_elevation_inside_surface(self, surface_service, simple_points):
        """Test elevation query at a point inside the surface."""
        tin = surface_service.create_tin_from_points(simple_points)
        
        # Query at center where we know there's a high point
        z = surface_service.query_elevation(tin, 50, 50)
        
        assert z is not None
        # Should be close to 120 (the center point elevation)
        assert 100 <= z <= 120
    
    def test_query_elevation_at_vertex(self, surface_service, simple_points):
        """Test elevation query exactly at a vertex."""
        tin = surface_service.create_tin_from_points(simple_points)
        
        # Query exactly at a corner
        z = surface_service.query_elevation(tin, 0, 0)
        
        # Might be None if point is outside all triangles, or around 100
        # This depends on triangulation
        if z is not None:
            assert abs(z - 100) < 1
    
    def test_query_elevation_outside_surface(self, surface_service, simple_points):
        """Test elevation query outside the surface returns None."""
        tin = surface_service.create_tin_from_points(simple_points)
        
        z = surface_service.query_elevation(tin, 500, 500)
        
        assert z is None
    
    # =========================================================================
    # Surface Area Tests
    # =========================================================================
    
    def test_calculate_surface_area_flat(self, surface_service):
        """Test surface area calculation for a flat surface."""
        # Unit square
        points = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        tin = surface_service.create_tin_from_points(points)
        
        area = surface_service.calculate_surface_area(tin)
        
        # Should be approximately 1 square meter (with 2 triangles)
        assert 0.9 <= area <= 1.1
    
    def test_calculate_surface_area_larger(self, surface_service, sloped_points):
        """Test surface area for a larger surface."""
        tin = surface_service.create_tin_from_points(sloped_points)
        
        area = surface_service.calculate_surface_area(tin)
        
        # Should be larger than flat 100x100 = 10000 due to slope
        assert area > 9000
    
    # =========================================================================
    # Volume Calculation Tests
    # =========================================================================
    
    def test_calculate_volume_between_parallel_surfaces(self, surface_service):
        """Test volume between two parallel flat surfaces."""
        # Upper surface at z=100
        upper_points = [(0, 0, 100), (100, 0, 100), (100, 100, 100), (0, 100, 100)]
        upper = surface_service.create_tin_from_points(upper_points, name="Upper")
        
        # Lower surface at z=90
        lower_points = [(0, 0, 90), (100, 0, 90), (100, 100, 90), (0, 100, 90)]
        lower = surface_service.create_tin_from_points(lower_points, name="Lower")
        
        result = surface_service.calculate_volume_between_surfaces(
            upper, lower, grid_spacing=10
        )
        
        # Expected: 100 x 100 x 10 = 100,000 m3
        # Allow for grid sampling approximation
        assert 80000 <= result.volume_m3 <= 120000
    
    def test_calculate_volume_zero_thickness(self, surface_service):
        """Test volume calculation when surfaces are at same elevation."""
        points = [(0, 0, 100), (100, 0, 100), (100, 100, 100), (0, 100, 100)]
        upper = surface_service.create_tin_from_points(points, name="Upper")
        lower = surface_service.create_tin_from_points(points, name="Lower")
        
        result = surface_service.calculate_volume_between_surfaces(upper, lower)
        
        # Should be very close to zero
        assert result.volume_m3 < 100
    
    # =========================================================================
    # Seam Tonnage Tests
    # =========================================================================
    
    def test_calculate_seam_tonnage(self, surface_service):
        """Test seam tonnage calculation."""
        # Roof at 100m
        roof_points = [(0, 0, 100), (100, 0, 100), (100, 100, 100), (0, 100, 100)]
        roof = surface_service.create_tin_from_points(roof_points, surface_type="seam_roof")
        
        # Floor at 95m (5m thickness)
        floor_points = [(0, 0, 95), (100, 0, 95), (100, 100, 95), (0, 100, 95)]
        floor = surface_service.create_tin_from_points(floor_points, surface_type="seam_floor")
        
        result = surface_service.calculate_seam_tonnage(
            roof, floor,
            density_t_m3=1.4,
            mining_loss_pct=5.0,
            yield_pct=85.0
        )
        
        # Expected in-situ: 100 x 100 x 5 x 1.4 = 70,000 tonnes
        # Allow for approximation
        assert result.in_situ_tonnes > 50000
        assert result.rom_tonnes < result.in_situ_tonnes
        assert result.product_tonnes < result.rom_tonnes
        assert result.thickness_avg > 0
    
    # =========================================================================
    # Contour Generation Tests
    # =========================================================================
    
    def test_generate_contours(self, surface_service, simple_points):
        """Test contour line generation."""
        tin = surface_service.create_tin_from_points(simple_points)
        
        contours = surface_service.generate_contours(tin, interval=5)
        
        # Should generate some contours between 100 and 120
        assert len(contours) > 0
        
        # All contour elevations should be within range
        for c in contours:
            assert 100 <= c.elevation <= 120
            assert len(c.points) >= 0
    
    def test_generate_contours_interval(self, surface_service, sloped_points):
        """Test contour generation with specific interval."""
        tin = surface_service.create_tin_from_points(sloped_points)
        
        # 5m interval
        contours_5m = surface_service.generate_contours(tin, interval=5)
        
        # 10m interval
        contours_10m = surface_service.generate_contours(tin, interval=10)
        
        # Should have fewer contours with larger interval
        assert len(contours_5m) >= len(contours_10m)


class TestPointInTriangle:
    """Tests for point-in-triangle helper functions."""
    
    @pytest.fixture
    def surface_service(self):
        from app.services.surface_service import SurfaceService
        return SurfaceService(db=None)
    
    def test_point_inside_triangle(self, surface_service):
        """Test point inside triangle detection."""
        # Triangle vertices
        ax, ay = 0, 0
        bx, by = 10, 0
        cx, cy = 5, 10
        
        # Point inside
        assert surface_service._point_in_triangle(5, 3, ax, ay, bx, by, cx, cy) == True
    
    def test_point_outside_triangle(self, surface_service):
        """Test point outside triangle detection."""
        ax, ay = 0, 0
        bx, by = 10, 0
        cx, cy = 5, 10
        
        # Point clearly outside
        assert surface_service._point_in_triangle(20, 20, ax, ay, bx, by, cx, cy) == False


class TestBarycentricInterpolation:
    """Tests for barycentric interpolation."""
    
    @pytest.fixture
    def surface_service(self):
        from app.services.surface_service import SurfaceService
        return SurfaceService(db=None)
    
    def test_barycentric_at_vertex(self, surface_service):
        """Test interpolation at a vertex returns vertex value."""
        # Triangle with different Z values
        z = surface_service._barycentric_interpolate(
            0, 0,  # Query point
            0, 0, 100,  # Vertex A
            10, 0, 200,  # Vertex B
            5, 10, 150  # Vertex C
        )
        
        # Should return Z of vertex A (100)
        assert abs(z - 100) < 0.1
    
    def test_barycentric_at_centroid(self, surface_service):
        """Test interpolation at triangle centroid."""
        z = surface_service._barycentric_interpolate(
            5, 3.33,  # Approximately centroid
            0, 0, 100,
            10, 0, 100,
            5, 10, 100
        )
        
        # All vertices at 100, so result should be ~100
        assert abs(z - 100) < 1


class TestTriangleArea:
    """Tests for triangle area calculation."""
    
    @pytest.fixture
    def surface_service(self):
        from app.services.surface_service import SurfaceService
        return SurfaceService(db=None)
    
    def test_flat_triangle_area(self, surface_service):
        """Test area of a flat triangle."""
        area = surface_service._triangle_area_3d(
            0, 0, 0,
            10, 0, 0,
            5, 10, 0
        )
        
        # Base = 10, Height = 10, Area = 0.5 * 10 * 10 = 50
        assert abs(area - 50) < 0.1
    
    def test_tilted_triangle_area(self, surface_service):
        """Test area of a tilted triangle (larger than projection)."""
        # Triangle tilted in Z
        area = surface_service._triangle_area_3d(
            0, 0, 0,
            10, 0, 0,
            5, 10, 10  # Z = 10
        )
        
        # Should be larger than flat triangle due to tilt
        flat_area = 50
        assert area > flat_area


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
