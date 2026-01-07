"""
Test CRS Service - Phase 1 Tests

Comprehensive tests for coordinate reference system service.
Tests transformations, validation, auto-detection, and edge cases.
"""

import pytest
import math
from typing import List, Tuple

# Import the service
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crs_service import (
    CRSService, CRSInfo, CRSCategory, TransformResult,
    SUPPORTED_CRS, get_crs_service
)


class TestCRSServiceBasics:
    """Basic CRS service tests."""
    
    def test_service_initialization(self):
        """Test that CRS service initializes correctly."""
        service = get_crs_service()
        assert service is not None
    
    def test_get_supported_crs(self):
        """Test getting list of supported CRS."""
        service = get_crs_service()
        systems = service.get_supported_crs()
        
        assert len(systems) > 0
        assert all(isinstance(s, CRSInfo) for s in systems)
    
    def test_supported_crs_has_mining_regions(self):
        """Test that key mining regions are covered."""
        service = get_crs_service()
        regions = service.get_regions()
        
        assert "South Africa" in regions
        assert "Australia" in regions
        assert "Indonesia" in regions
        assert "USA" in regions
    
    def test_filter_by_region(self):
        """Test filtering CRS by region."""
        service = get_crs_service()
        
        sa_systems = service.get_supported_crs(region="South Africa")
        assert len(sa_systems) > 0
        assert all("South Africa" in s.region for s in sa_systems)
        
        au_systems = service.get_supported_crs(region="Australia")
        assert len(au_systems) > 0
        assert all("Australia" in s.region for s in au_systems)
    
    def test_filter_by_category(self):
        """Test filtering CRS by category."""
        service = get_crs_service()
        
        geographic = service.get_supported_crs(category=CRSCategory.GEOGRAPHIC)
        assert len(geographic) > 0
        assert all(s.category == CRSCategory.GEOGRAPHIC for s in geographic)
        
        projected = service.get_supported_crs(category=CRSCategory.PROJECTED)
        assert len(projected) > 0
        assert all(s.category == CRSCategory.PROJECTED for s in projected)


class TestCRSValidation:
    """CRS validation tests."""
    
    def test_validate_valid_epsg(self):
        """Test validating a valid EPSG code."""
        service = get_crs_service()
        
        valid, error = service.validate_epsg(4326)  # WGS84
        assert valid is True
        assert error is None
        
        valid, error = service.validate_epsg(2052)  # SA Lo27
        assert valid is True
        assert error is None
    
    def test_validate_invalid_epsg(self):
        """Test validating an invalid EPSG code."""
        service = get_crs_service()
        
        valid, error = service.validate_epsg(0)
        assert valid is False
        assert error is not None
        
        valid, error = service.validate_epsg(999999)
        assert valid is False
        assert error is not None
    
    def test_get_crs_info(self):
        """Test getting CRS information."""
        service = get_crs_service()
        
        info = service.get_crs_info(4326)
        assert info is not None
        assert info.epsg == 4326
        assert info.name == "WGS 84"
        assert info.category == CRSCategory.GEOGRAPHIC
        
        info = service.get_crs_info(2052)
        assert info is not None
        assert info.epsg == 2052
        assert "Lo27" in info.name
    
    def test_get_crs_wkt(self):
        """Test getting WKT representation."""
        service = get_crs_service()
        
        wkt = service.get_crs_wkt(4326)
        assert wkt is not None
        assert "WGS 84" in wkt or "WGS84" in wkt.replace(" ", "")


class TestCoordinateTransforms:
    """Coordinate transformation tests."""
    
    def test_transform_single_point(self):
        """Test transforming a single point."""
        service = get_crs_service()
        
        # Transform from WGS84 to UTM Zone 35S (for SA coordinates)
        lon, lat, z = 28.0, -26.0, 100.0  # Johannesburg area
        tx, ty, tz = service.transform_point(lon, lat, z, 4326, 32735)
        
        # Should be valid UTM coordinates
        assert tx is not None
        assert ty is not None
        assert tz == z  # Z preserved
        assert 100000 < tx < 900000  # Valid UTM easting range
        assert 1000000 < ty < 10000000  # Valid UTM northing range (southern)
    
    def test_transform_points_batch(self):
        """Test transforming multiple points."""
        service = get_crs_service()
        
        points = [
            (28.0, -26.0, 100.0),
            (28.5, -26.5, 200.0),
            (29.0, -27.0, 300.0),
        ]
        
        result = service.transform_points(points, 4326, 32735)
        
        assert isinstance(result, TransformResult)
        assert result.success is True
        assert result.point_count == 3
        assert len(result.transformed_points) == 3
        assert len(result.errors) == 0
    
    def test_transform_sa_lo_grid(self):
        """Test transformation to South African Lo grid."""
        service = get_crs_service()
        
        # Mpumalanga coalfield area (Lo27)
        lon, lat, z = 29.5, -26.5, 1500.0
        tx, ty, tz = service.transform_point(lon, lat, z, 4326, 2052)
        
        # Check valid Lo27 coordinates
        assert tx is not None
        assert ty is not None
        # Y (northing) should be negative for southern hemisphere
        # but Lo grids use positive south
    
    def test_transform_roundtrip(self):
        """Test that transform -> inverse transform returns original."""
        service = get_crs_service()
        
        original = (29.5, -26.5, 1500.0)
        
        # Transform WGS84 -> Lo27
        tx, ty, tz = service.transform_point(*original, 4326, 2052)
        
        # Transform Lo27 -> WGS84
        rx, ry, rz = service.transform_point(tx, ty, tz, 2052, 4326)
        
        # Should be close to original (some precision loss expected)
        assert abs(rx - original[0]) < 0.00001
        assert abs(ry - original[1]) < 0.00001
        assert rz == original[2]
    
    def test_transform_australia_mga(self):
        """Test transformation to Australian MGA zones."""
        service = get_crs_service()
        
        # Bowen Basin area (MGA Zone 56)
        lon, lat, z = 148.5, -22.5, 250.0
        tx, ty, tz = service.transform_point(lon, lat, z, 4326, 28356)
        
        assert tx is not None
        assert ty is not None
        # Valid MGA easting
        assert 100000 < tx < 900000


class TestUTMDetection:
    """UTM zone detection tests."""
    
    def test_detect_utm_northern_hemisphere(self):
        """Test UTM zone detection for northern hemisphere."""
        service = get_crs_service()
        
        # USA Texas (Zone 14N)
        epsg = service.detect_utm_zone(-100.0, 30.0)
        assert 32600 < epsg < 32700
        
        # Europe (Zone 32N)
        epsg = service.detect_utm_zone(9.0, 50.0)
        assert 32600 < epsg < 32700
    
    def test_detect_utm_southern_hemisphere(self):
        """Test UTM zone detection for southern hemisphere."""
        service = get_crs_service()
        
        # South Africa (Zone 35S)
        epsg = service.detect_utm_zone(28.0, -26.0)
        assert 32700 < epsg < 32800
        
        # Australia (Zone 56S)
        epsg = service.detect_utm_zone(150.0, -30.0)
        assert 32700 < epsg < 32800
    
    def test_detect_sa_lo_zone(self):
        """Test South African Lo zone detection."""
        service = get_crs_service()
        
        # Lo27 (Mpumalanga)
        epsg = service.detect_sa_lo_zone(27.0)
        assert epsg == 2052
        
        # Lo29
        epsg = service.detect_sa_lo_zone(29.0)
        assert epsg == 2053
        
        # Lo25
        epsg = service.detect_sa_lo_zone(25.0)
        assert epsg == 2051
    
    def test_detect_best_crs_with_region_hint(self):
        """Test best CRS detection with region hint."""
        service = get_crs_service()
        
        # South Africa hint
        epsg = service.detect_best_crs(27.0, -26.0, region="South Africa")
        assert epsg in [2051, 2052, 2053]  # Lo grids
        
        # Australia hint
        epsg = service.detect_best_crs(150.0, -30.0, region="Australia")
        assert 28348 <= epsg <= 28358  # MGA zones


class TestEdgeCases:
    """Edge case tests."""
    
    def test_transform_at_zero(self):
        """Test transformation at origin."""
        service = get_crs_service()
        
        tx, ty, tz = service.transform_point(0, 0, 0, 4326, 32631)
        assert tx is not None
        assert ty is not None
    
    def test_transform_extreme_coordinates(self):
        """Test transformation at extreme coordinates."""
        service = get_crs_service()
        
        # Near pole
        result = service.transform_points([(0, 85, 0)], 4326, 32631)
        assert result.success is True
    
    def test_crs_info_unknown_epsg(self):
        """Test getting info for unknown but valid-ish EPSG."""
        service = get_crs_service()
        
        # 32632 is valid WGS84 UTM Zone 32N
        info = service.get_crs_info(32632)
        assert info is not None
        assert info.epsg == 32632
    
    def test_predefined_crs_count(self):
        """Test that predefined CRS dictionary has expected count."""
        # Should have at least 40 predefined CRS
        assert len(SUPPORTED_CRS) >= 40


class TestCRSCategories:
    """CRS category tests."""
    
    def test_wgs84_is_geographic(self):
        """Test that WGS84 is categorized as geographic."""
        service = get_crs_service()
        info = service.get_crs_info(4326)
        assert info.category == CRSCategory.GEOGRAPHIC
    
    def test_lo_grids_are_projected(self):
        """Test that SA Lo grids are categorized as projected."""
        service = get_crs_service()
        
        for epsg in [2046, 2047, 2048, 2049, 2050, 2051, 2052, 2053, 2054, 2055]:
            info = service.get_crs_info(epsg)
            assert info.category == CRSCategory.PROJECTED
    
    def test_mga_zones_are_projected(self):
        """Test that Australian MGA zones are projected."""
        service = get_crs_service()
        
        for epsg in [28349, 28350, 28351, 28352, 28353, 28354, 28355, 28356]:
            info = service.get_crs_info(epsg)
            assert info.category == CRSCategory.PROJECTED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
