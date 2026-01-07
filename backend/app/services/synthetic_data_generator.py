"""
Synthetic Data Generator - Phase 6

Generates realistic coal mine test data for multiple regions:
- South Africa Mpumalanga (Highveld coalfield)
- Australia Bowen Basin (Queensland)
- Indonesia Kalimantan (Tropical)
- USA Powder River Basin (Wyoming)

Each dataset includes:
- Borehole collars, surveys, and assays
- Terrain surface points
- Seam roof/floor surfaces
- Pit, ramp, and dump design outlines
"""

import random
import math
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class Region(str, Enum):
    """Available coal mining regions for synthetic data."""
    SOUTH_AFRICA_MPUMALANGA = "south_africa_mpumalanga"
    AUSTRALIA_BOWEN = "australia_bowen"
    INDONESIA_KALIMANTAN = "indonesia_kalimantan"
    USA_POWDER_RIVER = "usa_powder_river"


@dataclass
class RegionalConfig:
    """Region-specific geological and operational parameters."""
    name: str
    description: str
    
    # Terrain characteristics
    terrain_type: str  # flat, rolling, mountainous
    base_elevation: float  # meters above sea level
    terrain_relief: float  # max elevation variation
    
    # Seam parameters
    seam_count: int
    seam_names: List[str]
    seam_thickness_range: Tuple[float, float]  # meters
    interburden_range: Tuple[float, float]  # meters between seams
    seam_dip_degrees: float
    seam_dip_direction: float  # azimuth
    
    # Quality parameters (typical ranges)
    cv_range: Tuple[float, float]  # MJ/kg ARB
    ash_range: Tuple[float, float]  # % ADB
    moisture_range: Tuple[float, float]  # % AR
    sulphur_range: Tuple[float, float]  # % ADB
    volatile_range: Tuple[float, float]  # % ADB
    
    # Density
    coal_density: float  # t/m3
    overburden_density: float  # t/m3


# Pre-configured regional settings based on real coal operations
REGIONAL_CONFIGS = {
    Region.SOUTH_AFRICA_MPUMALANGA: RegionalConfig(
        name="Mpumalanga Highveld",
        description="South African Highveld coalfield - multiple thin seams, flat terrain",
        terrain_type="flat",
        base_elevation=1550.0,
        terrain_relief=30.0,
        seam_count=4,
        seam_names=["No. 1 Seam", "No. 2 Seam", "No. 4 Seam", "No. 5 Seam"],
        seam_thickness_range=(1.2, 3.5),
        interburden_range=(3.0, 15.0),
        seam_dip_degrees=2.0,
        seam_dip_direction=45.0,
        cv_range=(22.0, 26.0),
        ash_range=(14.0, 22.0),
        moisture_range=(4.0, 8.0),
        sulphur_range=(0.6, 1.5),
        volatile_range=(22.0, 28.0),
        coal_density=1.35,
        overburden_density=1.9
    ),
    Region.AUSTRALIA_BOWEN: RegionalConfig(
        name="Bowen Basin Queensland",
        description="Australian Bowen Basin - thick seams, rolling hills, coking coal",
        terrain_type="rolling",
        base_elevation=220.0,
        terrain_relief=80.0,
        seam_count=3,
        seam_names=["Goonyella Middle", "Goonyella Upper", "Goonyella Lower"],
        seam_thickness_range=(2.0, 6.0),
        interburden_range=(5.0, 25.0),
        seam_dip_degrees=5.0,
        seam_dip_direction=270.0,
        cv_range=(28.0, 32.0),
        ash_range=(8.0, 14.0),
        moisture_range=(2.0, 5.0),
        sulphur_range=(0.3, 0.8),
        volatile_range=(20.0, 26.0),
        coal_density=1.40,
        overburden_density=2.1
    ),
    Region.INDONESIA_KALIMANTAN: RegionalConfig(
        name="Kalimantan Tropical",
        description="Indonesian Kalimantan - thick seams, variable terrain, thermal coal",
        terrain_type="rolling",
        base_elevation=50.0,
        terrain_relief=120.0,
        seam_count=2,
        seam_names=["A Seam", "B Seam"],
        seam_thickness_range=(5.0, 15.0),
        interburden_range=(10.0, 40.0),
        seam_dip_degrees=8.0,
        seam_dip_direction=180.0,
        cv_range=(18.0, 24.0),
        ash_range=(3.0, 8.0),
        moisture_range=(25.0, 40.0),
        sulphur_range=(0.1, 0.5),
        volatile_range=(38.0, 45.0),
        coal_density=1.25,
        overburden_density=1.7
    ),
    Region.USA_POWDER_RIVER: RegionalConfig(
        name="Powder River Basin Wyoming",
        description="USA Powder River Basin - very thick single seam, gentle terrain",
        terrain_type="gentle",
        base_elevation=1200.0,
        terrain_relief=50.0,
        seam_count=1,
        seam_names=["Wyodak-Anderson"],
        seam_thickness_range=(20.0, 30.0),
        interburden_range=(0.0, 0.0),
        seam_dip_degrees=1.0,
        seam_dip_direction=90.0,
        cv_range=(17.0, 20.0),
        ash_range=(5.0, 8.0),
        moisture_range=(28.0, 35.0),
        sulphur_range=(0.2, 0.5),
        volatile_range=(30.0, 35.0),
        coal_density=1.30,
        overburden_density=1.8
    )
}


class SyntheticDataGenerator:
    """
    Generates realistic synthetic data for coal mining operations.
    
    Produces complete datasets including boreholes, terrain, seams, 
    and design surfaces for testing and demonstration.
    """
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.seed = seed
    
    def get_config(self, region: Region) -> RegionalConfig:
        """Get configuration for a region."""
        return REGIONAL_CONFIGS[region]
    
    # =========================================================================
    # BOREHOLE GENERATION
    # =========================================================================
    
    def generate_boreholes(
        self,
        region: Region,
        count: int = 50,
        extent: Tuple[float, float, float, float] = (0, 0, 2000, 2000)
    ) -> Dict[str, Any]:
        """
        Generate borehole data including collars, surveys, and assays.
        
        Args:
            region: Regional configuration to use
            count: Number of boreholes
            extent: (min_x, min_y, max_x, max_y) area to cover
            
        Returns:
            Dict with 'collars', 'surveys', 'assays' lists
        """
        config = self.get_config(region)
        
        min_x, min_y, max_x, max_y = extent
        width = max_x - min_x
        height = max_y - min_y
        
        collars = []
        surveys = []
        assays = []
        
        for i in range(count):
            hole_id = f"BH{i+1:04d}"
            
            # Random position with some clustering for realism
            x = min_x + random.random() * width
            y = min_y + random.random() * height
            
            # Terrain elevation at this point
            z = self._generate_terrain_elevation(x, y, config)
            
            # Create collar
            collar = {
                "hole_id": hole_id,
                "easting": round(x, 2),
                "northing": round(y, 2),
                "elevation": round(z, 2),
                "total_depth": 0.0,  # Will be updated
                "date_drilled": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                "driller": f"Drill Crew {(i % 5) + 1}"
            }
            
            # Generate surveys (mostly vertical, slight deviation)
            azimuth = random.uniform(0, 360)
            dip = -90 + random.uniform(-2, 2)  # Near vertical
            
            depth = 0
            while depth < 200:  # Max depth
                surveys.append({
                    "hole_id": hole_id,
                    "depth": round(depth, 2),
                    "azimuth": round(azimuth + random.uniform(-5, 5), 1),
                    "dip": round(dip + random.uniform(-1, 1), 1)
                })
                depth += random.uniform(20, 40)
            
            # Generate seam intervals and assays
            current_depth = random.uniform(5, 20)  # Overburden
            
            for seam_idx, seam_name in enumerate(config.seam_names):
                # Seam thickness
                thickness = random.uniform(*config.seam_thickness_range)
                
                from_depth = current_depth
                to_depth = from_depth + thickness
                
                # Quality values
                cv = random.uniform(*config.cv_range)
                ash = random.uniform(*config.ash_range)
                moisture = random.uniform(*config.moisture_range)
                sulphur = random.uniform(*config.sulphur_range)
                volatile = random.uniform(*config.volatile_range)
                
                assays.append({
                    "hole_id": hole_id,
                    "from_depth": round(from_depth, 2),
                    "to_depth": round(to_depth, 2),
                    "seam_name": seam_name,
                    "lithology": "COAL",
                    "cv_arb": round(cv, 2),
                    "ash_adb": round(ash, 1),
                    "moisture_ar": round(moisture, 1),
                    "sulphur_adb": round(sulphur, 2),
                    "volatile_adb": round(volatile, 1),
                    "density": round(config.coal_density + random.uniform(-0.1, 0.1), 2)
                })
                
                # Interburden to next seam
                if seam_idx < len(config.seam_names) - 1:
                    interburden = random.uniform(*config.interburden_range)
                    current_depth = to_depth + interburden
                else:
                    current_depth = to_depth
            
            collar["total_depth"] = round(current_depth + random.uniform(5, 15), 2)
            collars.append(collar)
        
        return {
            "collars": collars,
            "surveys": surveys,
            "assays": assays,
            "region": region.value,
            "config": config.name
        }
    
    # =========================================================================
    # TERRAIN GENERATION
    # =========================================================================
    
    def generate_terrain_points(
        self,
        region: Region,
        extent: Tuple[float, float, float, float] = (0, 0, 2000, 2000),
        spacing: float = 50.0
    ) -> List[Tuple[float, float, float]]:
        """Generate terrain surface points on a regular grid."""
        config = self.get_config(region)
        
        min_x, min_y, max_x, max_y = extent
        points = []
        
        x = min_x
        while x <= max_x:
            y = min_y
            while y <= max_y:
                z = self._generate_terrain_elevation(x, y, config)
                points.append((round(x, 2), round(y, 2), round(z, 2)))
                y += spacing
            x += spacing
        
        return points
    
    def _generate_terrain_elevation(
        self, x: float, y: float, config: RegionalConfig
    ) -> float:
        """Generate terrain elevation using Perlin-like noise."""
        # Simple multi-octave noise simulation
        base = config.base_elevation
        relief = config.terrain_relief
        
        # Different noise frequencies for realism
        z = base
        z += relief * 0.5 * math.sin(x * 0.002) * math.cos(y * 0.002)
        z += relief * 0.3 * math.sin(x * 0.005 + 1.5) * math.cos(y * 0.007 + 0.8)
        z += relief * 0.2 * math.sin(x * 0.015) * math.sin(y * 0.012)
        
        # Add some random micro-variation
        z += random.uniform(-relief * 0.05, relief * 0.05)
        
        return z
    
    # =========================================================================
    # SEAM SURFACE GENERATION
    # =========================================================================
    
    def generate_seam_surfaces(
        self,
        region: Region,
        extent: Tuple[float, float, float, float] = (0, 0, 2000, 2000),
        spacing: float = 50.0
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate seam roof and floor surfaces.
        
        Returns dict with seam name keys, each containing:
        - roof_points: List of (x, y, z)
        - floor_points: List of (x, y, z)
        """
        config = self.get_config(region)
        
        min_x, min_y, max_x, max_y = extent
        seam_surfaces = {}
        
        # Initial depth below terrain
        base_depth = random.uniform(15, 30)
        
        for seam_idx, seam_name in enumerate(config.seam_names):
            roof_points = []
            floor_points = []
            
            # Base thickness for this seam
            base_thickness = random.uniform(*config.seam_thickness_range)
            
            x = min_x
            while x <= max_x:
                y = min_y
                while y <= max_y:
                    # Terrain at this point
                    terrain_z = self._generate_terrain_elevation(x, y, config)
                    
                    # Seam dip effect
                    dip_rad = math.radians(config.seam_dip_degrees)
                    dir_rad = math.radians(config.seam_dip_direction)
                    dip_offset = (x * math.cos(dir_rad) + y * math.sin(dir_rad)) * math.tan(dip_rad)
                    
                    # Depth to seam roof
                    depth_to_roof = base_depth + dip_offset
                    for prev_idx in range(seam_idx):
                        depth_to_roof += random.uniform(*config.seam_thickness_range)
                        depth_to_roof += random.uniform(*config.interburden_range)
                    
                    # Add some natural variation
                    depth_to_roof += random.uniform(-2, 2)
                    
                    # Local thickness variation
                    local_thickness = base_thickness + random.uniform(-0.5, 0.5)
                    
                    roof_z = terrain_z - depth_to_roof
                    floor_z = roof_z - local_thickness
                    
                    roof_points.append((round(x, 2), round(y, 2), round(roof_z, 2)))
                    floor_points.append((round(x, 2), round(y, 2), round(floor_z, 2)))
                    
                    y += spacing
                x += spacing
            
            seam_surfaces[seam_name] = {
                "roof_points": roof_points,
                "floor_points": floor_points,
                "average_thickness": base_thickness
            }
            
            # Update base depth for next seam
            base_depth += base_thickness + random.uniform(*config.interburden_range)
        
        return seam_surfaces
    
    # =========================================================================
    # DESIGN SURFACES
    # =========================================================================
    
    def generate_pit_outline(
        self,
        region: Region,
        center: Tuple[float, float] = (1000, 1000),
        size: Tuple[float, float] = (800, 600)
    ) -> List[Tuple[float, float, float]]:
        """Generate a realistic pit outline polygon."""
        config = self.get_config(region)
        
        cx, cy = center
        width, height = size
        
        # Generate irregular pit boundary
        points = []
        num_points = 24
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            
            # Base radius with irregularity
            r_x = width / 2 * (0.8 + 0.4 * random.random())
            r_y = height / 2 * (0.8 + 0.4 * random.random())
            
            x = cx + r_x * math.cos(angle)
            y = cy + r_y * math.sin(angle)
            z = self._generate_terrain_elevation(x, y, config)
            
            points.append((round(x, 2), round(y, 2), round(z, 2)))
        
        return points
    
    def generate_ramp_design(
        self,
        region: Region,
        pit_outline: List[Tuple[float, float, float]],
        ramp_width: float = 30.0,
        gradient_pct: float = 10.0
    ) -> List[Tuple[float, float, float]]:
        """Generate a haul ramp polyline descending into the pit."""
        if not pit_outline:
            return []
        
        # Start point - highest elevation on pit rim
        start_point = max(pit_outline, key=lambda p: p[2])
        
        # End point - approximate pit floor
        min_z = min(p[2] for p in pit_outline) - 50  # 50m below rim
        
        points = [start_point]
        current = list(start_point)
        
        # Spiral down
        angle = 0
        radius = 200
        
        while current[2] > min_z:
            angle += math.radians(30)
            radius -= 5
            
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)
            dz = -gradient_pct * math.sqrt(dx*dx + dy*dy) / 100
            
            current[0] = start_point[0] + dx
            current[1] = start_point[1] + dy
            current[2] = current[2] + dz
            
            points.append((round(current[0], 2), round(current[1], 2), round(current[2], 2)))
        
        return points
    
    def generate_dump_outline(
        self,
        region: Region,
        center: Tuple[float, float] = (2500, 1000),
        size: Tuple[float, float] = (400, 300)
    ) -> List[Tuple[float, float, float]]:
        """Generate a waste dump outline polygon."""
        config = self.get_config(region)
        
        cx, cy = center
        width, height = size
        
        # Rectangular-ish dump shape
        points = []
        corners = [
            (cx - width/2, cy - height/2),
            (cx + width/2, cy - height/2),
            (cx + width/2, cy + height/2),
            (cx - width/2, cy + height/2)
        ]
        
        for corner_x, corner_y in corners:
            z = self._generate_terrain_elevation(corner_x, corner_y, config)
            # Dump surface is elevated above terrain
            z += random.uniform(20, 40)
            points.append((round(corner_x, 2), round(corner_y, 2), round(z, 2)))
        
        return points
    
    # =========================================================================
    # COMPLETE DATASET GENERATION
    # =========================================================================
    
    def generate_complete_dataset(
        self,
        region: Region,
        extent: Tuple[float, float, float, float] = (0, 0, 2000, 2000),
        borehole_count: int = 50
    ) -> Dict[str, Any]:
        """
        Generate a complete dataset for a region.
        
        Returns:
            Dict containing all generated data
        """
        config = self.get_config(region)
        
        # Generate all components
        boreholes = self.generate_boreholes(region, borehole_count, extent)
        terrain_points = self.generate_terrain_points(region, extent)
        seam_surfaces = self.generate_seam_surfaces(region, extent)
        pit_outline = self.generate_pit_outline(region)
        ramp_design = self.generate_ramp_design(region, pit_outline)
        dump_outline = self.generate_dump_outline(region)
        
        return {
            "region": region.value,
            "config": {
                "name": config.name,
                "description": config.description,
                "seam_names": config.seam_names,
                "coal_density": config.coal_density
            },
            "extent": extent,
            "boreholes": boreholes,
            "terrain": {
                "points": terrain_points,
                "point_count": len(terrain_points)
            },
            "seam_surfaces": seam_surfaces,
            "designs": {
                "pit_outline": pit_outline,
                "ramp_design": ramp_design,
                "dump_outline": dump_outline
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_all_regions(self) -> Dict[str, Dict[str, Any]]:
        """Generate datasets for all available regions."""
        datasets = {}
        
        for region in Region:
            datasets[region.value] = self.generate_complete_dataset(region)
        
        return datasets


# Factory function
def get_synthetic_data_generator(seed: Optional[int] = None) -> SyntheticDataGenerator:
    """Get a synthetic data generator instance."""
    return SyntheticDataGenerator(seed)
