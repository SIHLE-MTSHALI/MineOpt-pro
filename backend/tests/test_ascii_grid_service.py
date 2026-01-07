"""
Tests for ASCII Grid Service - Phase 1 File Format Enhancement

Tests for:
- XYZ file parsing
- ASC file parsing
- Export to XYZ
- Export to ASC
- Grid/point conversions
"""

import pytest
import tempfile
import os


class TestXYZParsing:
    """Tests for XYZ point cloud parsing."""
    
    @pytest.fixture
    def ascii_service(self):
        """Create ASCII grid service instance."""
        from app.services.ascii_grid_service import ASCIIGridService
        return ASCIIGridService()
    
    @pytest.fixture
    def xyz_content_space(self):
        """Sample XYZ content with space delimiter."""
        return """0.0 0.0 100.0
100.0 0.0 105.0
100.0 100.0 110.0
0.0 100.0 102.0
50.0 50.0 120.0"""
    
    @pytest.fixture
    def xyz_content_comma(self):
        """Sample XYZ content with comma delimiter."""
        return """0.0,0.0,100.0
100.0,0.0,105.0
100.0,100.0,110.0
0.0,100.0,102.0
50.0,50.0,120.0"""
    
    @pytest.fixture
    def xyz_content_with_header(self):
        """Sample XYZ content with header row."""
        return """X,Y,Z
0.0,0.0,100.0
100.0,0.0,105.0"""
    
    @pytest.fixture
    def xyz_content_with_value(self):
        """Sample XYZ content with 4th value column."""
        return """0.0 0.0 100.0 25.5
100.0 0.0 105.0 26.0
100.0 100.0 110.0 24.0"""
    
    def test_parse_xyz_space_delimited(self, ascii_service, xyz_content_space):
        """Test parsing space-delimited XYZ content."""
        result = ascii_service.parse_xyz_string(xyz_content_space)
        
        assert result.success == True
        assert result.point_count == 5
        assert len(result.points) == 5
        assert result.errors == []
    
    def test_parse_xyz_comma_delimited(self, ascii_service, xyz_content_comma):
        """Test parsing comma-delimited XYZ content."""
        result = ascii_service.parse_xyz_string(xyz_content_comma)
        
        assert result.success == True
        assert result.point_count == 5
    
    def test_parse_xyz_with_header(self, ascii_service, xyz_content_with_header):
        """Test parsing XYZ with header row."""
        result = ascii_service.parse_xyz_string(xyz_content_with_header)
        
        assert result.success == True
        assert result.point_count == 2
        assert len(result.warnings) > 0  # Should warn about header
    
    def test_parse_xyz_with_value_column(self, ascii_service, xyz_content_with_value):
        """Test parsing XYZ with 4th value column."""
        result = ascii_service.parse_xyz_string(xyz_content_with_value)
        
        assert result.success == True
        assert result.has_value_column == True
        assert result.points[0].value == pytest.approx(25.5)
    
    def test_parse_xyz_extents(self, ascii_service, xyz_content_space):
        """Test extent calculation."""
        result = ascii_service.parse_xyz_string(xyz_content_space)
        
        assert result.extent_min == (0.0, 0.0, 100.0)
        assert result.extent_max == (100.0, 100.0, 120.0)
    
    def test_parse_xyz_empty_content(self, ascii_service):
        """Test parsing empty content fails."""
        result = ascii_service.parse_xyz_string("")
        
        assert result.success == False
        assert len(result.errors) > 0
    
    def test_parse_xyz_invalid_content(self, ascii_service):
        """Test parsing invalid content."""
        result = ascii_service.parse_xyz_string("not valid xyz data")
        
        assert result.success == False


class TestASCParsing:
    """Tests for ESRI ASCII Grid parsing."""
    
    @pytest.fixture
    def ascii_service(self):
        from app.services.ascii_grid_service import ASCIIGridService
        return ASCIIGridService()
    
    @pytest.fixture
    def asc_content(self):
        """Sample ASC grid content."""
        return """ncols         5
nrows         5
xllcorner     0.0
yllcorner     0.0
cellsize      10.0
NODATA_value  -9999
100 101 102 103 104
105 106 107 108 109
110 111 112 113 114
115 116 117 118 119
120 121 122 123 124"""
    
    @pytest.fixture
    def asc_content_with_nodata(self):
        """ASC content with nodata values."""
        return """ncols         3
nrows         3
xllcorner     0.0
yllcorner     0.0
cellsize      10.0
NODATA_value  -9999
100 -9999 102
103 104 105
-9999 107 108"""
    
    def test_parse_asc_basic(self, ascii_service, asc_content):
        """Test basic ASC parsing."""
        result = ascii_service.parse_asc_bytes(asc_content.encode())
        
        assert result.success == True
        assert result.grid is not None
        assert result.grid.ncols == 5
        assert result.grid.nrows == 5
        assert result.grid.cellsize == 10.0
    
    def test_parse_asc_grid_values(self, ascii_service, asc_content):
        """Test ASC grid data values."""
        result = ascii_service.parse_asc_bytes(asc_content.encode())
        
        # Check first row
        assert result.grid.data[0][0] == 100
        assert result.grid.data[0][4] == 104
        
        # Check last row
        assert result.grid.data[4][0] == 120
        assert result.grid.data[4][4] == 124
    
    def test_parse_asc_extents(self, ascii_service, asc_content):
        """Test ASC extent calculation."""
        result = ascii_service.parse_asc_bytes(asc_content.encode())
        
        assert result.grid.xllcorner == 0.0
        assert result.grid.yllcorner == 0.0
        assert result.grid.xmax == 50.0  # 5 * 10
        assert result.grid.ymax == 50.0
    
    def test_parse_asc_with_nodata(self, ascii_service, asc_content_with_nodata):
        """Test ASC with nodata values."""
        result = ascii_service.parse_asc_bytes(asc_content_with_nodata.encode())
        
        assert result.success == True
        assert result.grid.get_value(0, 1) is None  # -9999 nodata
        assert result.grid.get_value(0, 0) == 100
    
    def test_parse_asc_to_points(self, ascii_service, asc_content):
        """Test converting ASC grid to points."""
        result = ascii_service.parse_asc_bytes(asc_content.encode())
        
        points = result.grid.to_points()
        
        assert len(points) == 25  # 5x5 grid
        
        # Check point coordinates (center of cells)
        assert points[0].x == 5.0  # First cell center
        assert points[0].y == 45.0  # Y is flipped


class TestXYZExport:
    """Tests for XYZ export."""
    
    @pytest.fixture
    def ascii_service(self):
        from app.services.ascii_grid_service import ASCIIGridService
        return ASCIIGridService()
    
    @pytest.fixture
    def sample_points(self):
        from app.services.ascii_grid_service import XYZPoint
        return [
            XYZPoint(x=0.0, y=0.0, z=100.0),
            XYZPoint(x=100.0, y=0.0, z=105.0),
            XYZPoint(x=50.0, y=50.0, z=120.0, value=25.0),
        ]
    
    def test_export_xyz_basic(self, ascii_service, sample_points):
        """Test basic XYZ export."""
        content = ascii_service.export_xyz(sample_points)
        
        assert content is not None
        lines = content.strip().split('\n')
        assert len(lines) == 3
        
        # Check first line
        parts = lines[0].split()
        assert float(parts[0]) == 0.0
        assert float(parts[1]) == 0.0
        assert float(parts[2]) == 100.0
    
    def test_export_xyz_with_header(self, ascii_service, sample_points):
        """Test XYZ export with header."""
        content = ascii_service.export_xyz(sample_points, include_header=True)
        
        lines = content.strip().split('\n')
        assert lines[0] == "X Y Z"
        assert len(lines) == 4  # Header + 3 points
    
    def test_export_xyz_comma_delimiter(self, ascii_service, sample_points):
        """Test XYZ export with comma delimiter."""
        content = ascii_service.export_xyz(sample_points, delimiter=",")
        
        lines = content.strip().split('\n')
        assert "," in lines[0]
    
    def test_export_xyz_with_value(self, ascii_service, sample_points):
        """Test XYZ export including value column."""
        content = ascii_service.export_xyz(sample_points, include_value=True)
        
        lines = content.strip().split('\n')
        # Third point has value
        parts = lines[2].split()
        assert len(parts) == 4
        assert float(parts[3]) == 25.0
    
    def test_export_xyz_to_file(self, ascii_service, sample_points):
        """Test XYZ export to file."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            filepath = f.name
        
        try:
            ascii_service.export_xyz(sample_points, file_path=filepath)
            
            assert os.path.exists(filepath)
            with open(filepath) as f:
                content = f.read()
            assert len(content) > 0
        finally:
            os.unlink(filepath)


class TestASCExport:
    """Tests for ASC grid export."""
    
    @pytest.fixture
    def ascii_service(self):
        from app.services.ascii_grid_service import ASCIIGridService
        return ASCIIGridService()
    
    @pytest.fixture
    def sample_grid(self):
        from app.services.ascii_grid_service import GridData
        return GridData(
            ncols=3,
            nrows=3,
            xllcorner=0.0,
            yllcorner=0.0,
            cellsize=10.0,
            nodata_value=-9999,
            data=[
                [100, 101, 102],
                [103, 104, 105],
                [106, 107, 108]
            ]
        )
    
    def test_export_asc_basic(self, ascii_service, sample_grid):
        """Test basic ASC export."""
        content = ascii_service.export_asc(sample_grid)
        
        assert content is not None
        assert "ncols" in content
        assert "nrows" in content
        assert "cellsize" in content
        
        lines = content.strip().split('\n')
        assert len(lines) == 9  # 6 header + 3 data rows
    
    def test_export_asc_header_values(self, ascii_service, sample_grid):
        """Test ASC export header values."""
        content = ascii_service.export_asc(sample_grid)
        
        assert "ncols         3" in content
        assert "nrows         3" in content
        assert "cellsize      10.0" in content


class TestGridPointConversion:
    """Tests for grid-to-point and point-to-grid conversion."""
    
    @pytest.fixture
    def ascii_service(self):
        from app.services.ascii_grid_service import ASCIIGridService
        return ASCIIGridService()
    
    @pytest.fixture
    def sample_points(self):
        from app.services.ascii_grid_service import XYZPoint
        return [
            XYZPoint(x=5.0, y=5.0, z=100.0),
            XYZPoint(x=15.0, y=5.0, z=105.0),
            XYZPoint(x=5.0, y=15.0, z=110.0),
            XYZPoint(x=15.0, y=15.0, z=115.0),
        ]
    
    def test_points_to_grid(self, ascii_service, sample_points):
        """Test converting points to grid."""
        grid = ascii_service.points_to_grid(sample_points, cellsize=10.0)
        
        assert grid is not None
        assert grid.cellsize == 10.0
        assert grid.ncols >= 2
        assert grid.nrows >= 2
    
    def test_grid_to_points(self, ascii_service, sample_points):
        """Test round-trip grid to points conversion."""
        grid = ascii_service.points_to_grid(sample_points, cellsize=10.0)
        points = ascii_service.grid_to_points(grid)
        
        # Should get some points back (may not be exactly same due to grid sampling)
        assert len(points) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
