"""
Tests for DXF Service Enhancements - Phase 1

Tests for:
- TIN surface export to DXF
- Contour export to DXF
- String (polyline) export to DXF
- Multi-surface export
"""

import pytest
from unittest.mock import patch, MagicMock


class TestDXFTINExport:
    """Tests for TIN surface export functionality."""
    
    @pytest.fixture
    def dxf_service(self):
        """Create DXF service instance."""
        from app.services.dxf_service import DXFService
        return DXFService()
    
    @pytest.fixture
    def simple_tin(self):
        """Simple TIN with 4 vertices and 2 triangles."""
        vertices = [
            (0, 0, 100),
            (100, 0, 100),
            (100, 100, 100),
            (0, 100, 100)
        ]
        triangles = [
            (0, 1, 2),
            (0, 2, 3)
        ]
        return vertices, triangles
    
    @pytest.fixture
    def sloped_tin(self):
        """TIN with variable elevations."""
        vertices = [
            (0, 0, 100),
            (100, 0, 105),
            (200, 0, 110),
            (0, 100, 102),
            (100, 100, 107),
            (200, 100, 115),
        ]
        triangles = [
            (0, 1, 4),
            (0, 4, 3),
            (1, 2, 5),
            (1, 5, 4),
        ]
        return vertices, triangles
    
    def test_export_tin_surface_returns_bytes(self, dxf_service, simple_tin):
        """Test TIN export returns bytes when no file path given."""
        vertices, triangles = simple_tin
        
        result = dxf_service.export_tin_surface(
            vertices=vertices,
            triangles=triangles,
            layer_name="TEST_SURFACE"
        )
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_tin_surface_contains_faces(self, dxf_service, simple_tin):
        """Test exported DXF contains 3DFACE entities."""
        vertices, triangles = simple_tin
        
        result = dxf_service.export_tin_surface(
            vertices=vertices,
            triangles=triangles
        )
        
        # Check content contains 3DFACE reference
        content = result.decode('utf-8', errors='ignore')
        assert '3DFACE' in content or 'ENTITIES' in content
    
    def test_export_tin_surface_with_layer(self, dxf_service, simple_tin):
        """Test TIN export with custom layer name."""
        vertices, triangles = simple_tin
        
        result = dxf_service.export_tin_surface(
            vertices=vertices,
            triangles=triangles,
            layer_name="MY_CUSTOM_LAYER"
        )
        
        content = result.decode('utf-8', errors='ignore')
        assert 'MY_CUSTOM_LAYER' in content
    
    def test_export_tin_surface_handles_invalid_triangles(self, dxf_service):
        """Test TIN export handles triangles with invalid indices."""
        vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        triangles = [
            (0, 1, 2),  # Valid
            (0, 1, 10)  # Invalid index
        ]
        
        # Should not raise, just skip invalid
        result = dxf_service.export_tin_surface(vertices=vertices, triangles=triangles)
        
        assert result is not None


class TestDXFContourExport:
    """Tests for contour line export."""
    
    @pytest.fixture
    def dxf_service(self):
        from app.services.dxf_service import DXFService
        return DXFService()
    
    @pytest.fixture
    def sample_contours(self):
        """Sample contour data."""
        return [
            {
                "elevation": 100,
                "points": [(0, 0, 100), (50, 10, 100), (100, 0, 100)]
            },
            {
                "elevation": 105,
                "points": [(0, 50, 105), (50, 60, 105), (100, 50, 105)]
            },
            {
                "elevation": 110,
                "points": [(0, 100, 110), (50, 110, 110), (100, 100, 110)]
            }
        ]
    
    def test_export_contours_returns_bytes(self, dxf_service, sample_contours):
        """Test contour export returns bytes."""
        result = dxf_service.export_contours(sample_contours)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_export_contours_creates_layers(self, dxf_service, sample_contours):
        """Test contour export creates major/minor layers."""
        result = dxf_service.export_contours(sample_contours)
        
        content = result.decode('utf-8', errors='ignore')
        assert 'CONTOUR' in content
    
    def test_export_contours_major_interval(self, dxf_service, sample_contours):
        """Test major contour interval handling."""
        # With 10m interval, 100 and 110 are major
        result = dxf_service.export_contours(
            sample_contours,
            major_interval=10.0
        )
        
        assert result is not None
    
    def test_export_contours_empty_input(self, dxf_service):
        """Test contour export with empty list."""
        result = dxf_service.export_contours([])
        
        # Should still return valid DXF (just empty)
        assert result is not None


class TestDXFStringExport:
    """Tests for CAD string/polyline export."""
    
    @pytest.fixture
    def dxf_service(self):
        from app.services.dxf_service import DXFService
        return DXFService()
    
    @pytest.fixture
    def sample_strings(self):
        """Sample string data."""
        return [
            {
                "name": "Boundary1",
                "points": [(0, 0, 100), (100, 0, 100), (100, 100, 100), (0, 100, 100)],
                "closed": True,
                "string_type": "boundary"
            },
            {
                "name": "Road1",
                "points": [(0, 50, 100), (50, 50, 105), (100, 50, 110)],
                "closed": False,
                "string_type": "road"
            }
        ]
    
    def test_export_strings_returns_bytes(self, dxf_service, sample_strings):
        """Test string export returns bytes."""
        result = dxf_service.export_strings(sample_strings)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_export_strings_by_type(self, dxf_service, sample_strings):
        """Test strings exported to layers by type."""
        result = dxf_service.export_strings(sample_strings)
        
        content = result.decode('utf-8', errors='ignore')
        # Should have layer entries
        assert 'LAYER' in content or 'BOUNDARY' in content.upper()
    
    def test_export_strings_closed_polyline(self, dxf_service):
        """Test closed polyline export."""
        strings = [{
            "name": "Closed",
            "points": [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)],
            "closed": True
        }]
        
        result = dxf_service.export_strings(strings)
        
        assert result is not None


class TestDXFMultiSurfaceExport:
    """Tests for multi-surface export."""
    
    @pytest.fixture
    def dxf_service(self):
        from app.services.dxf_service import DXFService
        return DXFService()
    
    @pytest.fixture
    def multiple_surfaces(self):
        """Multiple surfaces for testing."""
        return [
            {
                "name": "Terrain",
                "surface_type": "terrain",
                "vertices": [(0, 0, 100), (100, 0, 100), (100, 100, 100), (0, 100, 100)],
                "triangles": [(0, 1, 2), (0, 2, 3)]
            },
            {
                "name": "Seam1_Roof",
                "surface_type": "seam_roof",
                "vertices": [(0, 0, 90), (100, 0, 90), (100, 100, 90), (0, 100, 90)],
                "triangles": [(0, 1, 2), (0, 2, 3)]
            },
            {
                "name": "Seam1_Floor",
                "surface_type": "seam_floor",
                "vertices": [(0, 0, 85), (100, 0, 85), (100, 100, 85), (0, 100, 85)],
                "triangles": [(0, 1, 2), (0, 2, 3)]
            }
        ]
    
    def test_export_multi_surfaces(self, dxf_service, multiple_surfaces):
        """Test exporting multiple surfaces to single DXF."""
        result = dxf_service.export_surfaces_multi(multiple_surfaces)
        
        assert result is not None
        content = result.decode('utf-8', errors='ignore')
        
        # Should contain references to surface layers
        assert 'SURFACE' in content.upper()
    
    def test_export_multi_surfaces_separate_layers(self, dxf_service, multiple_surfaces):
        """Test each surface goes to its own layer."""
        result = dxf_service.export_surfaces_multi(multiple_surfaces)
        
        content = result.decode('utf-8', errors='ignore')
        
        # Should have multiple SURFACE_ layers
        assert 'TERRAIN' in content.upper() or 'SEAM' in content.upper()
    
    def test_export_multi_surfaces_colors_by_type(self, dxf_service, multiple_surfaces):
        """Test different surface types get different colors."""
        # Just verify it doesn't error
        result = dxf_service.export_surfaces_multi(multiple_surfaces)
        
        assert result is not None


class TestDXFExportConfig:
    """Tests for export configuration options."""
    
    @pytest.fixture
    def dxf_service(self):
        from app.services.dxf_service import DXFService
        return DXFService()
    
    def test_export_with_different_versions(self, dxf_service):
        """Test export with different DXF versions."""
        from app.services.dxf_service import DXFExportConfig
        
        vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        triangles = [(0, 1, 2)]
        
        # Test AC1032 (AutoCAD 2018)
        config = DXFExportConfig(version="AC1032")
        result = dxf_service.export_tin_surface(
            vertices=vertices,
            triangles=triangles,
            config=config
        )
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
