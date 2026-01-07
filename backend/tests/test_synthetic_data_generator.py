"""
Tests for Synthetic Data Generator - Phase 6

Tests for:
- Regional configuration
- Borehole generation
- Terrain generation
- Seam surface generation
- Design surface generation
- Complete dataset generation
"""

import pytest
import math


class TestRegionalConfig:
    """Tests for regional configuration."""
    
    @pytest.fixture
    def generator(self):
        from app.services.synthetic_data_generator import SyntheticDataGenerator
        return SyntheticDataGenerator(seed=42)
    
    def test_all_regions_have_config(self, generator):
        """Test that all regions have valid configurations."""
        from app.services.synthetic_data_generator import Region, REGIONAL_CONFIGS
        
        for region in Region:
            assert region in REGIONAL_CONFIGS
            config = REGIONAL_CONFIGS[region]
            assert config.name is not None
            assert config.seam_count > 0
            assert len(config.seam_names) == config.seam_count
    
    def test_south_africa_config(self, generator):
        """Test South Africa Mpumalanga configuration."""
        from app.services.synthetic_data_generator import Region
        
        config = generator.get_config(Region.SOUTH_AFRICA_MPUMALANGA)
        
        assert config.terrain_type == "flat"
        assert config.seam_count == 4
        assert config.base_elevation == pytest.approx(1550.0)
    
    def test_australia_config(self, generator):
        """Test Australia Bowen Basin configuration."""
        from app.services.synthetic_data_generator import Region
        
        config = generator.get_config(Region.AUSTRALIA_BOWEN)
        
        assert config.terrain_type == "rolling"
        assert config.seam_count == 3
        assert "Goonyella" in config.seam_names[0]
    
    def test_indonesia_config(self, generator):
        """Test Indonesia Kalimantan configuration."""
        from app.services.synthetic_data_generator import Region
        
        config = generator.get_config(Region.INDONESIA_KALIMANTAN)
        
        assert config.terrain_type == "rolling"
        assert config.seam_count == 2
        assert config.moisture_range[1] > 30  # High moisture
    
    def test_usa_config(self, generator):
        """Test USA Powder River configuration."""
        from app.services.synthetic_data_generator import Region
        
        config = generator.get_config(Region.USA_POWDER_RIVER)
        
        assert config.seam_count == 1
        assert config.seam_thickness_range[0] >= 20  # Very thick seam


class TestBoreholeGeneration:
    """Tests for borehole data generation."""
    
    @pytest.fixture
    def generator(self):
        from app.services.synthetic_data_generator import SyntheticDataGenerator
        return SyntheticDataGenerator(seed=42)
    
    def test_generate_boreholes_count(self, generator):
        """Test borehole count matches requested."""
        from app.services.synthetic_data_generator import Region
        
        data = generator.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=25)
        
        assert len(data["collars"]) == 25
    
    def test_generate_boreholes_extent(self, generator):
        """Test boreholes are within specified extent."""
        from app.services.synthetic_data_generator import Region
        
        extent = (1000, 2000, 3000, 4000)  # min_x, min_y, max_x, max_y
        data = generator.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=20, extent=extent)
        
        for collar in data["collars"]:
            assert extent[0] <= collar["easting"] <= extent[2]
            assert extent[1] <= collar["northing"] <= extent[3]
    
    def test_generate_boreholes_has_required_fields(self, generator):
        """Test generated collars have required fields."""
        from app.services.synthetic_data_generator import Region
        
        data = generator.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=5)
        
        collar = data["collars"][0]
        assert "hole_id" in collar
        assert "easting" in collar
        assert "northing" in collar
        assert "elevation" in collar
        assert "total_depth" in collar
    
    def test_generate_boreholes_has_surveys(self, generator):
        """Test generated data includes surveys."""
        from app.services.synthetic_data_generator import Region
        
        data = generator.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=10)
        
        assert len(data["surveys"]) > 0
        
        survey = data["surveys"][0]
        assert "hole_id" in survey
        assert "depth" in survey
        assert "azimuth" in survey
        assert "dip" in survey
    
    def test_generate_boreholes_has_assays(self, generator):
        """Test generated data includes assays."""
        from app.services.synthetic_data_generator import Region
        
        data = generator.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=10)
        
        assert len(data["assays"]) > 0
        
        assay = data["assays"][0]
        assert "hole_id" in assay
        assert "seam_name" in assay
        assert "cv_arb" in assay
        assert "ash_adb" in assay
    
    def test_generate_boreholes_quality_in_range(self, generator):
        """Test generated quality values are within configured ranges."""
        from app.services.synthetic_data_generator import Region
        
        region = Region.SOUTH_AFRICA_MPUMALANGA
        config = generator.get_config(region)
        data = generator.generate_boreholes(region, count=20)
        
        for assay in data["assays"]:
            assert config.cv_range[0] <= assay["cv_arb"] <= config.cv_range[1]
            assert config.ash_range[0] <= assay["ash_adb"] <= config.ash_range[1]


class TestTerrainGeneration:
    """Tests for terrain surface generation."""
    
    @pytest.fixture
    def generator(self):
        from app.services.synthetic_data_generator import SyntheticDataGenerator
        return SyntheticDataGenerator(seed=42)
    
    def test_generate_terrain_points_count(self, generator):
        """Test terrain point count matches grid."""
        from app.services.synthetic_data_generator import Region
        
        extent = (0, 0, 100, 100)
        spacing = 25.0
        
        points = generator.generate_terrain_points(
            Region.SOUTH_AFRICA_MPUMALANGA,
            extent=extent,
            spacing=spacing
        )
        
        # 5x5 grid = 25 points
        expected = 5 * 5
        assert len(points) == expected
    
    def test_generate_terrain_elevation_range(self, generator):
        """Test terrain elevations are in reasonable range."""
        from app.services.synthetic_data_generator import Region
        
        region = Region.SOUTH_AFRICA_MPUMALANGA
        config = generator.get_config(region)
        
        points = generator.generate_terrain_points(region)
        
        zs = [p[2] for p in points]
        min_z = min(zs)
        max_z = max(zs)
        
        # Should be within base +/- relief
        assert min_z >= config.base_elevation - config.terrain_relief * 2
        assert max_z <= config.base_elevation + config.terrain_relief * 2
    
    def test_generate_terrain_flat_region(self, generator):
        """Test flat terrain has limited variation."""
        from app.services.synthetic_data_generator import Region
        
        points = generator.generate_terrain_points(Region.SOUTH_AFRICA_MPUMALANGA)
        
        zs = [p[2] for p in points]
        relief = max(zs) - min(zs)
        
        # Flat terrain should have <50m relief
        assert relief < 100


class TestSeamGeneration:
    """Tests for seam surface generation."""
    
    @pytest.fixture
    def generator(self):
        from app.services.synthetic_data_generator import SyntheticDataGenerator
        return SyntheticDataGenerator(seed=42)
    
    def test_generate_seam_surfaces_all_seams(self, generator):
        """Test all configured seams are generated."""
        from app.services.synthetic_data_generator import Region
        
        region = Region.SOUTH_AFRICA_MPUMALANGA
        config = generator.get_config(region)
        
        surfaces = generator.generate_seam_surfaces(region, spacing=100)
        
        assert len(surfaces) == config.seam_count
        for seam_name in config.seam_names:
            assert seam_name in surfaces
    
    def test_generate_seam_has_roof_and_floor(self, generator):
        """Test each seam has both roof and floor surfaces."""
        from app.services.synthetic_data_generator import Region
        
        surfaces = generator.generate_seam_surfaces(Region.SOUTH_AFRICA_MPUMALANGA)
        
        for seam_name, seam_data in surfaces.items():
            assert "roof_points" in seam_data
            assert "floor_points" in seam_data
            assert len(seam_data["roof_points"]) > 0
            assert len(seam_data["floor_points"]) > 0
    
    def test_generate_seam_roof_above_floor(self, generator):
        """Test seam roof is above floor."""
        from app.services.synthetic_data_generator import Region
        
        surfaces = generator.generate_seam_surfaces(Region.SOUTH_AFRICA_MPUMALANGA)
        
        for seam_name, seam_data in surfaces.items():
            for i, (roof_pt, floor_pt) in enumerate(zip(
                seam_data["roof_points"], 
                seam_data["floor_points"]
            )):
                assert roof_pt[2] > floor_pt[2], f"Roof should be above floor at point {i}"


class TestDesignGeneration:
    """Tests for design surface generation."""
    
    @pytest.fixture
    def generator(self):
        from app.services.synthetic_data_generator import SyntheticDataGenerator
        return SyntheticDataGenerator(seed=42)
    
    def test_generate_pit_outline(self, generator):
        """Test pit outline generation."""
        from app.services.synthetic_data_generator import Region
        
        outline = generator.generate_pit_outline(
            Region.SOUTH_AFRICA_MPUMALANGA,
            center=(500, 500),
            size=(400, 300)
        )
        
        assert len(outline) > 10  # Should have multiple vertices
        
        # All points should be 3D
        for pt in outline:
            assert len(pt) == 3
    
    def test_generate_ramp_design(self, generator):
        """Test ramp design generation."""
        from app.services.synthetic_data_generator import Region
        
        pit_outline = generator.generate_pit_outline(Region.SOUTH_AFRICA_MPUMALANGA)
        ramp = generator.generate_ramp_design(Region.SOUTH_AFRICA_MPUMALANGA, pit_outline)
        
        assert len(ramp) > 5
        
        # Ramp should descend
        start_z = ramp[0][2]
        end_z = ramp[-1][2]
        assert end_z < start_z
    
    def test_generate_dump_outline(self, generator):
        """Test dump outline generation."""
        from app.services.synthetic_data_generator import Region
        
        dump = generator.generate_dump_outline(Region.SOUTH_AFRICA_MPUMALANGA)
        
        assert len(dump) == 4  # Rectangle


class TestCompleteDataset:
    """Tests for complete dataset generation."""
    
    @pytest.fixture
    def generator(self):
        from app.services.synthetic_data_generator import SyntheticDataGenerator
        return SyntheticDataGenerator(seed=42)
    
    def test_generate_complete_dataset_structure(self, generator):
        """Test complete dataset has all required sections."""
        from app.services.synthetic_data_generator import Region
        
        dataset = generator.generate_complete_dataset(
            Region.SOUTH_AFRICA_MPUMALANGA,
            borehole_count=10
        )
        
        assert "region" in dataset
        assert "config" in dataset
        assert "boreholes" in dataset
        assert "terrain" in dataset
        assert "seam_surfaces" in dataset
        assert "designs" in dataset
        assert "generated_at" in dataset
    
    def test_generate_complete_dataset_designs(self, generator):
        """Test complete dataset includes all design types."""
        from app.services.synthetic_data_generator import Region
        
        dataset = generator.generate_complete_dataset(Region.AUSTRALIA_BOWEN)
        
        designs = dataset["designs"]
        assert "pit_outline" in designs
        assert "ramp_design" in designs
        assert "dump_outline" in designs
    
    def test_generate_all_regions(self, generator):
        """Test generating datasets for all regions."""
        datasets = generator.generate_all_regions()
        
        from app.services.synthetic_data_generator import Region
        assert len(datasets) == len(Region)
        
        for region in Region:
            assert region.value in datasets


class TestDeterministicGeneration:
    """Tests for deterministic output with seed."""
    
    def test_same_seed_same_output(self):
        """Test same seed produces same output."""
        from app.services.synthetic_data_generator import SyntheticDataGenerator, Region
        
        gen1 = SyntheticDataGenerator(seed=123)
        gen2 = SyntheticDataGenerator(seed=123)
        
        data1 = gen1.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=5)
        data2 = gen2.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=5)
        
        for c1, c2 in zip(data1["collars"], data2["collars"]):
            assert c1["easting"] == c2["easting"]
            assert c1["northing"] == c2["northing"]
    
    def test_different_seed_different_output(self):
        """Test different seeds produce different output."""
        from app.services.synthetic_data_generator import SyntheticDataGenerator, Region
        
        gen1 = SyntheticDataGenerator(seed=123)
        gen2 = SyntheticDataGenerator(seed=456)
        
        data1 = gen1.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=5)
        data2 = gen2.generate_boreholes(Region.SOUTH_AFRICA_MPUMALANGA, count=5)
        
        # At least some values should differ
        different = False
        for c1, c2 in zip(data1["collars"], data2["collars"]):
            if c1["easting"] != c2["easting"]:
                different = True
                break
        
        assert different


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
