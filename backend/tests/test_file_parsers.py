"""
Unit Tests for Phase 1 File Parsers

Tests for:
- DXF Service
- Surpac Parser
- Tabular Parser
"""

import pytest
import tempfile
import os
from pathlib import Path


# ============================================================================
# DXF Service Tests
# ============================================================================

class TestDXFService:
    """Tests for DXF file parsing and export."""
    
    @pytest.fixture
    def dxf_service(self):
        """Get DXF service (skip if ezdxf not installed)."""
        try:
            from app.services.dxf_service import get_dxf_service
            return get_dxf_service()
        except ImportError:
            pytest.skip("ezdxf not installed")
    
    @pytest.fixture
    def sample_dxf_content(self):
        """Generate minimal valid DXF content."""
        # Minimal DXF R12 format
        return """0
SECTION
2
HEADER
0
ENDSEC
0
SECTION
2
ENTITIES
0
POINT
8
0
10
100.0
20
200.0
30
50.0
0
LINE
8
0
10
0.0
20
0.0
30
0.0
11
100.0
21
100.0
31
0.0
0
ENDSEC
0
EOF
"""
    
    def test_parse_bytes(self, dxf_service, sample_dxf_content):
        """Test parsing DXF from bytes."""
        result = dxf_service.parse_bytes(
            sample_dxf_content.encode('utf-8'),
            "test.dxf"
        )
        
        assert result.success
        assert result.entity_count >= 2  # At least point and line
    
    def test_parse_extracts_points(self, dxf_service, sample_dxf_content):
        """Test that POINT entities are extracted."""
        result = dxf_service.parse_bytes(
            sample_dxf_content.encode('utf-8'),
            "test.dxf"
        )
        
        assert result.point_count >= 1
        
        # Find the point entity
        from app.services.dxf_service import DXFEntityType
        points = dxf_service.get_entities_by_type(result, DXFEntityType.POINT)
        assert len(points) >= 1
        
        # Check coordinates
        point = points[0]
        assert len(point.points) == 1
        assert point.points[0].x == 100.0
        assert point.points[0].y == 200.0
        assert point.points[0].z == 50.0
    
    def test_create_and_export_document(self, dxf_service):
        """Test creating a new DXF document and exporting."""
        from app.services.dxf_service import DXFPoint
        
        doc = dxf_service.create_new_document("R2018")
        
        # Add a layer
        dxf_service.add_layer(doc, "TEST_LAYER", color=3)
        
        # Add a point
        dxf_service.add_point(doc, DXFPoint(x=50, y=100, z=25), layer="TEST_LAYER")
        
        # Add a line
        dxf_service.add_line(
            doc,
            DXFPoint(x=0, y=0, z=0),
            DXFPoint(x=100, y=100, z=0),
            layer="TEST_LAYER"
        )
        
        # Export to bytes
        result_bytes = dxf_service.export_to_bytes(doc)
        
        assert len(result_bytes) > 0
        assert b"ENTITIES" in result_bytes
    
    def test_export_activity_areas(self, dxf_service):
        """Test exporting activity areas to DXF."""
        areas = [
            {
                "name": "Block A",
                "activity_type": "Coal Mining",
                "geometry": {
                    "vertices": [
                        [0, 0, 0],
                        [100, 0, 0],
                        [100, 100, 0],
                        [0, 100, 0]
                    ]
                }
            },
            {
                "name": "Block B",
                "activity_type": "Waste Mining",
                "geometry": {
                    "vertices": [
                        [100, 0, 0],
                        [200, 0, 0],
                        [200, 100, 0],
                        [100, 100, 0]
                    ]
                }
            }
        ]
        
        result_bytes = dxf_service.export_activity_areas(areas)
        
        assert result_bytes is not None
        assert len(result_bytes) > 0
    
    def test_calculate_extents(self, dxf_service, sample_dxf_content):
        """Test extent calculation."""
        result = dxf_service.parse_bytes(
            sample_dxf_content.encode('utf-8'),
            "test.dxf"
        )
        
        if result.success and result.extent_min and result.extent_max:
            assert result.extent_min.x <= result.extent_max.x
            assert result.extent_min.y <= result.extent_max.y


# ============================================================================
# Surpac Parser Tests
# ============================================================================

class TestSurpacParser:
    """Tests for Surpac .str file parsing."""
    
    @pytest.fixture
    def surpac_parser(self):
        from app.services.surpac_parser import get_surpac_parser
        return get_surpac_parser()
    
    @pytest.fixture
    def sample_str_content(self):
        """Sample Surpac string file content."""
        return """MINEOPT, 2026-01-07, Test Export
0, 0, 0, 0,
1, 1000.0, 500.0, 100.0, PIT_BOUNDARY
1, 1100.0, 500.0, 100.0, PIT_BOUNDARY
1, 1100.0, 600.0, 100.0, PIT_BOUNDARY
1, 1000.0, 600.0, 100.0, PIT_BOUNDARY
1, 1000.0, 500.0, 100.0, PIT_BOUNDARY
0, 0, 0, 0,
2, 800.0, 400.0, 95.0, COAL_BLOCK
2, 900.0, 400.0, 95.0, COAL_BLOCK
2, 900.0, 500.0, 95.0, COAL_BLOCK
2, 800.0, 500.0, 95.0, COAL_BLOCK
0, 0, 0, 0,
0, 0, 0, 0, END
"""
    
    def test_parse_string(self, surpac_parser, sample_str_content):
        """Test parsing Surpac string content."""
        result = surpac_parser.parse_string(sample_str_content, "test.str")
        
        assert result.success
        assert result.string_count == 2
        assert result.point_count == 9
    
    def test_parse_header(self, surpac_parser, sample_str_content):
        """Test header parsing."""
        result = surpac_parser.parse_string(sample_str_content, "test.str")
        
        assert result.header is not None
        assert result.header.location_code == "MINEOPT"
    
    def test_parse_strings(self, surpac_parser, sample_str_content):
        """Test string extraction."""
        result = surpac_parser.parse_string(sample_str_content, "test.str")
        
        # String 1 should have 5 points (closed polygon)
        string1 = next(s for s in result.strings if s.string_number == 1)
        assert string1.point_count == 5
        assert string1.is_closed  # First and last points are same
        
        # String 2 should have 4 points
        string2 = next(s for s in result.strings if s.string_number == 2)
        assert string2.point_count == 4
    
    def test_parse_descriptors(self, surpac_parser, sample_str_content):
        """Test descriptor extraction."""
        result = surpac_parser.parse_string(sample_str_content, "test.str")
        
        string1 = next(s for s in result.strings if s.string_number == 1)
        first_desc = string1.get_first_descriptor(0)
        assert first_desc == "PIT_BOUNDARY"
    
    def test_parse_coordinates(self, surpac_parser, sample_str_content):
        """Test coordinate parsing."""
        result = surpac_parser.parse_string(sample_str_content, "test.str")
        
        string1 = next(s for s in result.strings if s.string_number == 1)
        first_point = string1.points[0]
        
        assert first_point.northing == 1000.0
        assert first_point.easting == 500.0
        assert first_point.rl == 100.0
        
        # Check x/y/z aliases
        assert first_point.x == 500.0  # easting
        assert first_point.y == 1000.0  # northing
        assert first_point.z == 100.0  # rl
    
    def test_export_to_string(self, surpac_parser):
        """Test exporting to .str format."""
        from app.services.surpac_parser import SurpacString, SurpacPoint
        
        strings = [
            SurpacString(
                string_number=1,
                points=[
                    SurpacPoint(1, 1000, 500, 100, ["BOUNDARY"]),
                    SurpacPoint(1, 1100, 500, 100, ["BOUNDARY"]),
                    SurpacPoint(1, 1100, 600, 100, ["BOUNDARY"]),
                ]
            )
        ]
        
        output = surpac_parser.export_to_string(strings)
        
        assert "MINEOPT" in output
        assert "1, 1000.000, 500.000, 100.000" in output
        assert "END" in output
    
    def test_convert_to_activity_geometry(self, surpac_parser, sample_str_content):
        """Test conversion to activity area geometry."""
        result = surpac_parser.parse_string(sample_str_content, "test.str")
        string1 = next(s for s in result.strings if s.string_number == 1)
        
        geometry = surpac_parser.to_activity_area_geometry(string1)
        
        assert "vertices" in geometry
        assert len(geometry["vertices"]) == 5
        assert geometry["is_closed"] == True
        assert geometry["string_number"] == 1
    
    def test_binary_format_rejected(self, surpac_parser):
        """Test that binary format is rejected with clear error."""
        binary_content = b'\x00\x01\x02\x03\x04\x05'
        result = surpac_parser.parse_bytes(binary_content, "binary.str")
        
        assert not result.success
        assert any("Binary" in e for e in result.errors)


# ============================================================================
# Tabular Parser Tests
# ============================================================================

class TestTabularParser:
    """Tests for CSV/TXT parsing."""
    
    @pytest.fixture
    def tabular_parser(self):
        from app.services.tabular_parser import get_tabular_parser
        return get_tabular_parser()
    
    @pytest.fixture
    def sample_collar_csv(self):
        """Sample Vulcan-style collar CSV."""
        return """HoleID,Easting,Northing,Elevation,TotalDepth
BH001,524150.50,7145230.25,1245.5,85.0
BH002,524200.75,7145280.10,1248.2,92.5
BH003,524180.00,7145350.00,1250.1,78.3
"""
    
    @pytest.fixture
    def sample_assay_csv(self):
        """Sample assay CSV with coal quality data."""
        return """HoleID,From,To,Seam,CV_ARB,Ash_ADB,Moisture,Sulphur
BH001,45.2,48.5,Upper,24.5,12.3,8.5,0.45
BH001,52.0,54.8,Lower,22.8,15.1,9.2,0.52
BH002,42.8,46.2,Upper,25.1,11.8,8.1,0.42
"""
    
    def test_parse_csv(self, tabular_parser, sample_collar_csv):
        """Test basic CSV parsing."""
        result = tabular_parser.parse_string(sample_collar_csv, "collar.csv")
        
        assert result.success
        assert result.row_count == 3
        assert result.column_count == 5
    
    def test_infer_delimiter(self, tabular_parser):
        """Test delimiter auto-detection."""
        csv_content = "a,b,c\n1,2,3"
        tab_content = "a\tb\tc\n1\t2\t3"
        
        csv_result = tabular_parser.parse_string(csv_content, "test.csv")
        tab_result = tabular_parser.parse_string(tab_content, "test.txt")
        
        assert csv_result.delimiter == ","
        assert tab_result.delimiter == "\t"
    
    def test_infer_column_types(self, tabular_parser, sample_collar_csv):
        """Test column type inference."""
        from app.services.tabular_parser import ColumnType
        
        result = tabular_parser.parse_string(sample_collar_csv, "collar.csv")
        
        # HoleID should be string
        hole_col = next(c for c in result.columns if c.name == "HoleID")
        assert hole_col.inferred_type == ColumnType.STRING
        
        # Easting should be float
        east_col = next(c for c in result.columns if c.name == "Easting")
        assert east_col.inferred_type == ColumnType.FLOAT
    
    def test_infer_purpose_collar(self, tabular_parser, sample_collar_csv):
        """Test detecting collar file purpose."""
        from app.services.tabular_parser import BoreholeBoreholePurpose
        
        result = tabular_parser.parse_string(sample_collar_csv, "collar.csv")
        
        assert result.inferred_purpose == BoreholeBoreholePurpose.COLLAR
    
    def test_infer_purpose_assay(self, tabular_parser, sample_assay_csv):
        """Test detecting assay file purpose."""
        from app.services.tabular_parser import BoreholeBoreholePurpose
        
        result = tabular_parser.parse_string(sample_assay_csv, "assay.csv")
        
        assert result.inferred_purpose == BoreholeBoreholePurpose.ASSAY
    
    def test_suggest_column_mappings(self, tabular_parser, sample_collar_csv):
        """Test column mapping suggestions."""
        result = tabular_parser.parse_string(sample_collar_csv, "collar.csv")
        
        # Standard columns should map to themselves
        hole_col = next(c for c in result.columns if c.name == "HoleID")
        assert hole_col.suggested_mapping == "HoleID"
    
    def test_apply_mapping(self, tabular_parser, sample_collar_csv):
        """Test applying column mappings."""
        result = tabular_parser.parse_string(sample_collar_csv, "collar.csv")
        
        mappings = {
            "HoleID": "hole_id",
            "Easting": "x",
            "Northing": "y",
            "Elevation": "z"
        }
        
        output = tabular_parser.apply_mapping(result, mappings)
        
        assert len(output) == 3
        assert output[0]["hole_id"] == "BH001"
        assert output[0]["x"] == 524150.50
    
    def test_export_to_csv(self, tabular_parser):
        """Test exporting data to CSV."""
        data = [
            {"HoleID": "BH001", "Easting": 100.0, "Northing": 200.0},
            {"HoleID": "BH002", "Easting": 150.0, "Northing": 250.0}
        ]
        
        csv_output = tabular_parser.export_to_csv(data)
        
        assert "HoleID,Easting,Northing" in csv_output
        assert "BH001" in csv_output
        assert "100.0" in csv_output
    
    def test_templates_available(self, tabular_parser):
        """Test that import templates are available."""
        templates = tabular_parser.list_templates()
        
        assert "vulcan_collar" in templates
        assert "vulcan_survey" in templates
        assert "vulcan_assay" in templates
        assert "minex_collar" in templates
    
    def test_get_template(self, tabular_parser):
        """Test retrieving a specific template."""
        template = tabular_parser.get_template("vulcan_collar")
        
        assert template is not None
        assert "HoleID" in template.required_columns
        assert "Easting" in template.required_columns
    
    def test_handle_empty_values(self, tabular_parser):
        """Test handling empty/null values."""
        csv_with_nulls = """HoleID,Depth,Value
BH001,10.0,
BH002,,50.0
"""
        result = tabular_parser.parse_string(csv_with_nulls, "test.csv")
        
        assert result.success
        assert result.row_count == 2
        
        # Check null counts
        depth_col = next(c for c in result.columns if c.name == "Depth")
        assert depth_col.null_count == 1
    
    def test_no_header_mode(self, tabular_parser):
        """Test parsing without header row."""
        csv_no_header = """BH001,100.0,200.0,50.0
BH002,150.0,250.0,55.0
"""
        result = tabular_parser.parse_string(
            csv_no_header, 
            "test.csv",
            has_header=False
        )
        
        assert result.success
        assert result.row_count == 2
        assert result.columns[0].name == "Column_1"


# ============================================================================
# Integration Tests
# ============================================================================

class TestFileParserIntegration:
    """Integration tests for file parsers."""
    
    def test_roundtrip_surpac(self):
        """Test parsing and re-exporting Surpac file."""
        from app.services.surpac_parser import get_surpac_parser
        
        parser = get_surpac_parser()
        
        original_content = """MINEOPT, 2026-01-07, Roundtrip Test
0, 0, 0, 0,
1, 1000.0, 500.0, 100.0, TEST
1, 1100.0, 500.0, 100.0, TEST
0, 0, 0, 0,
0, 0, 0, 0, END
"""
        
        # Parse
        result = parser.parse_string(original_content, "test.str")
        assert result.success
        
        # Re-export
        exported = parser.export_to_string(result.strings)
        
        # Parse again
        result2 = parser.parse_string(exported, "exported.str")
        assert result2.success
        assert result2.string_count == result.string_count
        assert result2.point_count == result.point_count
    
    def test_csv_to_borehole_format(self):
        """Test converting CSV to standardized borehole format."""
        from app.services.tabular_parser import get_tabular_parser
        
        parser = get_tabular_parser()
        
        # Minex-style input with different column names
        csv_content = """BH_NAME,EAST,NORTH,COLLAR_RL,DEPTH
BH001,100,200,50,80
BH002,150,250,55,90
"""
        
        result = parser.parse_string(csv_content, "minex_collar.csv")
        assert result.success
        
        # Apply standard mappings
        collars = parser.to_borehole_collars(result)
        
        assert len(collars) == 2
