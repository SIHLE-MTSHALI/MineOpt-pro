"""
CRS (Coordinate Reference System) Service - Phase 1

Comprehensive coordinate system support for mining applications.
Uses pyproj (BSD license - 100% FREE) for all transformations.

Supported Systems:
- South Africa Lo Grids (EPSG 2046-2055)
- WGS84 Geographic (EPSG 4326)
- UTM Zones (32601-32660, 32701-32760)
- Australia MGA Zones (EPSG 28348-28358)
- Indonesia DGN95/UTM (EPSG 23830-23853)
- USA NAD83 State Plane / UTM
- Custom WKT/Proj4 definitions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Union
from enum import Enum
import math

try:
    from pyproj import CRS, Transformer
    from pyproj.exceptions import CRSError
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    CRS = None
    Transformer = None


class CRSCategory(str, Enum):
    """Categories of coordinate reference systems."""
    GEOGRAPHIC = "geographic"       # Lat/Lon systems
    PROJECTED = "projected"         # Meters/feet based
    LOCAL = "local"                 # Mine grid systems
    CUSTOM = "custom"               # User-defined


@dataclass
class CRSInfo:
    """Information about a coordinate reference system."""
    epsg: int
    name: str
    category: CRSCategory
    units: str
    description: str
    region: str
    bounds: Optional[Tuple[float, float, float, float]] = None  # min_x, min_y, max_x, max_y
    is_south_hemisphere: bool = False
    utm_zone: Optional[int] = None


@dataclass
class TransformResult:
    """Result of a coordinate transformation."""
    success: bool
    source_crs: int
    target_crs: int
    source_points: List[Tuple[float, float, float]]
    transformed_points: List[Tuple[float, float, float]]
    point_count: int
    errors: List[str] = field(default_factory=list)


# Comprehensive CRS definitions for mining regions
SUPPORTED_CRS: Dict[int, CRSInfo] = {
    # WGS84 Geographic
    4326: CRSInfo(
        epsg=4326,
        name="WGS 84",
        category=CRSCategory.GEOGRAPHIC,
        units="degrees",
        description="World Geodetic System 1984 - Global geographic coordinates",
        region="Global",
        bounds=(-180, -90, 180, 90)
    ),
    
    # South Africa - Hartebeesthoek94 Lo Grids (Cape Town Datum)
    2046: CRSInfo(
        epsg=2046,
        name="Hartebeesthoek94 / Lo15",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 15° grid",
        region="South Africa",
        bounds=(13.0, -35.0, 17.0, -22.0),
        is_south_hemisphere=True
    ),
    2047: CRSInfo(
        epsg=2047,
        name="Hartebeesthoek94 / Lo17",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 17° grid",
        region="South Africa",
        bounds=(15.0, -35.0, 19.0, -22.0),
        is_south_hemisphere=True
    ),
    2048: CRSInfo(
        epsg=2048,
        name="Hartebeesthoek94 / Lo19",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 19° grid",
        region="South Africa",
        bounds=(17.0, -35.0, 21.0, -22.0),
        is_south_hemisphere=True
    ),
    2049: CRSInfo(
        epsg=2049,
        name="Hartebeesthoek94 / Lo21",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 21° grid",
        region="South Africa",
        bounds=(19.0, -35.0, 23.0, -22.0),
        is_south_hemisphere=True
    ),
    2050: CRSInfo(
        epsg=2050,
        name="Hartebeesthoek94 / Lo23",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 23° grid",
        region="South Africa",
        bounds=(21.0, -35.0, 25.0, -22.0),
        is_south_hemisphere=True
    ),
    2051: CRSInfo(
        epsg=2051,
        name="Hartebeesthoek94 / Lo25",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 25° grid",
        region="South Africa",
        bounds=(23.0, -35.0, 27.0, -22.0),
        is_south_hemisphere=True
    ),
    2052: CRSInfo(
        epsg=2052,
        name="Hartebeesthoek94 / Lo27",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 27° grid (Mpumalanga coalfields)",
        region="South Africa",
        bounds=(25.0, -35.0, 29.0, -22.0),
        is_south_hemisphere=True
    ),
    2053: CRSInfo(
        epsg=2053,
        name="Hartebeesthoek94 / Lo29",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 29° grid",
        region="South Africa",
        bounds=(27.0, -35.0, 31.0, -22.0),
        is_south_hemisphere=True
    ),
    2054: CRSInfo(
        epsg=2054,
        name="Hartebeesthoek94 / Lo31",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 31° grid",
        region="South Africa",
        bounds=(29.0, -35.0, 33.0, -22.0),
        is_south_hemisphere=True
    ),
    2055: CRSInfo(
        epsg=2055,
        name="Hartebeesthoek94 / Lo33",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="South Africa Lo 33° grid",
        region="South Africa",
        bounds=(31.0, -35.0, 35.0, -22.0),
        is_south_hemisphere=True
    ),
    
    # Australia - MGA Zones (GDA94)
    28349: CRSInfo(
        epsg=28349,
        name="GDA94 / MGA zone 49",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 49",
        region="Australia",
        bounds=(108.0, -80.0, 114.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=49
    ),
    28350: CRSInfo(
        epsg=28350,
        name="GDA94 / MGA zone 50",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 50 (Western Australia)",
        region="Australia",
        bounds=(114.0, -80.0, 120.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=50
    ),
    28351: CRSInfo(
        epsg=28351,
        name="GDA94 / MGA zone 51",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 51",
        region="Australia",
        bounds=(120.0, -80.0, 126.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=51
    ),
    28352: CRSInfo(
        epsg=28352,
        name="GDA94 / MGA zone 52",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 52",
        region="Australia",
        bounds=(126.0, -80.0, 132.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=52
    ),
    28353: CRSInfo(
        epsg=28353,
        name="GDA94 / MGA zone 53",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 53",
        region="Australia",
        bounds=(132.0, -80.0, 138.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=53
    ),
    28354: CRSInfo(
        epsg=28354,
        name="GDA94 / MGA zone 54",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 54",
        region="Australia",
        bounds=(138.0, -80.0, 144.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=54
    ),
    28355: CRSInfo(
        epsg=28355,
        name="GDA94 / MGA zone 55",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 55 (Queensland/NSW)",
        region="Australia",
        bounds=(144.0, -80.0, 150.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=55
    ),
    28356: CRSInfo(
        epsg=28356,
        name="GDA94 / MGA zone 56",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Australia Map Grid zone 56 (Bowen Basin)",
        region="Australia",
        bounds=(150.0, -80.0, 156.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=56
    ),
    
    # Indonesia - DGN95 / UTM zones
    23836: CRSInfo(
        epsg=23836,
        name="DGN95 / UTM zone 46N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 46N (Sumatra)",
        region="Indonesia",
        bounds=(90.0, 0.0, 96.0, 84.0),
        utm_zone=46
    ),
    23837: CRSInfo(
        epsg=23837,
        name="DGN95 / UTM zone 47N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 47N",
        region="Indonesia",
        bounds=(96.0, 0.0, 102.0, 84.0),
        utm_zone=47
    ),
    23838: CRSInfo(
        epsg=23838,
        name="DGN95 / UTM zone 48N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 48N",
        region="Indonesia",
        bounds=(102.0, 0.0, 108.0, 84.0),
        utm_zone=48
    ),
    23839: CRSInfo(
        epsg=23839,
        name="DGN95 / UTM zone 49N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 49N (Kalimantan)",
        region="Indonesia",
        bounds=(108.0, 0.0, 114.0, 84.0),
        utm_zone=49
    ),
    23840: CRSInfo(
        epsg=23840,
        name="DGN95 / UTM zone 50N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 50N (Kalimantan)",
        region="Indonesia",
        bounds=(114.0, 0.0, 120.0, 84.0),
        utm_zone=50
    ),
    23841: CRSInfo(
        epsg=23841,
        name="DGN95 / UTM zone 51N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 51N",
        region="Indonesia",
        bounds=(120.0, 0.0, 126.0, 84.0),
        utm_zone=51
    ),
    
    # Indonesia - Southern hemisphere UTM zones
    23886: CRSInfo(
        epsg=23886,
        name="DGN95 / UTM zone 46S",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 46S",
        region="Indonesia",
        bounds=(90.0, -80.0, 96.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=46
    ),
    23887: CRSInfo(
        epsg=23887,
        name="DGN95 / UTM zone 47S",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 47S",
        region="Indonesia",
        bounds=(96.0, -80.0, 102.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=47
    ),
    23888: CRSInfo(
        epsg=23888,
        name="DGN95 / UTM zone 48S",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 48S (Java)",
        region="Indonesia",
        bounds=(102.0, -80.0, 108.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=48
    ),
    23889: CRSInfo(
        epsg=23889,
        name="DGN95 / UTM zone 49S",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 49S (Kalimantan South)",
        region="Indonesia",
        bounds=(108.0, -80.0, 114.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=49
    ),
    23890: CRSInfo(
        epsg=23890,
        name="DGN95 / UTM zone 50S",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="Indonesia UTM zone 50S (Kalimantan South)",
        region="Indonesia",
        bounds=(114.0, -80.0, 120.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=50
    ),
    
    # USA - NAD83 UTM Zones
    26910: CRSInfo(
        epsg=26910,
        name="NAD83 / UTM zone 10N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 10N (California/Oregon)",
        region="USA",
        bounds=(-126.0, 0.0, -120.0, 84.0),
        utm_zone=10
    ),
    26911: CRSInfo(
        epsg=26911,
        name="NAD83 / UTM zone 11N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 11N (Nevada/Utah)",
        region="USA",
        bounds=(-120.0, 0.0, -114.0, 84.0),
        utm_zone=11
    ),
    26912: CRSInfo(
        epsg=26912,
        name="NAD83 / UTM zone 12N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 12N (Arizona/Utah/Wyoming)",
        region="USA",
        bounds=(-114.0, 0.0, -108.0, 84.0),
        utm_zone=12
    ),
    26913: CRSInfo(
        epsg=26913,
        name="NAD83 / UTM zone 13N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 13N (Colorado/Wyoming/Powder River)",
        region="USA",
        bounds=(-108.0, 0.0, -102.0, 84.0),
        utm_zone=13
    ),
    26914: CRSInfo(
        epsg=26914,
        name="NAD83 / UTM zone 14N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 14N (Texas/Wyoming)",
        region="USA",
        bounds=(-102.0, 0.0, -96.0, 84.0),
        utm_zone=14
    ),
    26915: CRSInfo(
        epsg=26915,
        name="NAD83 / UTM zone 15N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 15N (Midwest)",
        region="USA",
        bounds=(-96.0, 0.0, -90.0, 84.0),
        utm_zone=15
    ),
    26916: CRSInfo(
        epsg=26916,
        name="NAD83 / UTM zone 16N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 16N (Appalachia)",
        region="USA",
        bounds=(-90.0, 0.0, -84.0, 84.0),
        utm_zone=16
    ),
    26917: CRSInfo(
        epsg=26917,
        name="NAD83 / UTM zone 17N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 17N (East Coast)",
        region="USA",
        bounds=(-84.0, 0.0, -78.0, 84.0),
        utm_zone=17
    ),
    26918: CRSInfo(
        epsg=26918,
        name="NAD83 / UTM zone 18N",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="USA UTM zone 18N (Pennsylvania/NY)",
        region="USA",
        bounds=(-78.0, 0.0, -72.0, 84.0),
        utm_zone=18
    ),
    
    # WGS84 UTM Zones - Global (Southern Hemisphere examples)
    32735: CRSInfo(
        epsg=32735,
        name="WGS 84 / UTM zone 35S",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="WGS84 UTM zone 35S (Southern Africa)",
        region="Global",
        bounds=(24.0, -80.0, 30.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=35
    ),
    32736: CRSInfo(
        epsg=32736,
        name="WGS 84 / UTM zone 36S",
        category=CRSCategory.PROJECTED,
        units="meters",
        description="WGS84 UTM zone 36S (Southern Africa)",
        region="Global",
        bounds=(30.0, -80.0, 36.0, 0.0),
        is_south_hemisphere=True,
        utm_zone=36
    ),
}


class CRSService:
    """
    Service for coordinate reference system operations.
    
    Provides:
    - List supported coordinate systems
    - Transform coordinates between systems
    - Validate EPSG codes
    - Auto-detect UTM zones from lat/lon
    - Get CRS metadata
    """
    
    def __init__(self):
        """Initialize CRS service."""
        if not PYPROJ_AVAILABLE:
            raise ImportError(
                "pyproj is required for CRS operations. "
                "Install with: pip install pyproj>=3.4.0"
            )
        self._transformer_cache: Dict[Tuple[int, int], Transformer] = {}
    
    def get_supported_crs(
        self, 
        region: Optional[str] = None,
        category: Optional[CRSCategory] = None
    ) -> List[CRSInfo]:
        """
        Get list of supported coordinate reference systems.
        
        Args:
            region: Filter by region (e.g., "South Africa", "Australia")
            category: Filter by category
            
        Returns:
            List of CRSInfo objects
        """
        result = list(SUPPORTED_CRS.values())
        
        if region:
            result = [crs for crs in result if region.lower() in crs.region.lower()]
        
        if category:
            result = [crs for crs in result if crs.category == category]
        
        return sorted(result, key=lambda x: (x.region, x.epsg))
    
    def get_crs_info(self, epsg: int) -> Optional[CRSInfo]:
        """
        Get information about a specific EPSG code.
        
        Args:
            epsg: EPSG code
            
        Returns:
            CRSInfo or None if not found
        """
        # Check our predefined list first
        if epsg in SUPPORTED_CRS:
            return SUPPORTED_CRS[epsg]
        
        # Try to get info from pyproj for any valid EPSG
        try:
            crs = CRS.from_epsg(epsg)
            
            # Determine category
            if crs.is_geographic:
                category = CRSCategory.GEOGRAPHIC
            elif crs.is_projected:
                category = CRSCategory.PROJECTED
            else:
                category = CRSCategory.CUSTOM
            
            # Get units
            units = "unknown"
            if crs.axis_info:
                units = crs.axis_info[0].unit_name or "unknown"
            
            # Get bounds if available
            bounds = None
            if crs.area_of_use:
                bounds = (
                    crs.area_of_use.west,
                    crs.area_of_use.south,
                    crs.area_of_use.east,
                    crs.area_of_use.north
                )
            
            return CRSInfo(
                epsg=epsg,
                name=crs.name,
                category=category,
                units=units,
                description=crs.name,
                region=crs.area_of_use.name if crs.area_of_use else "Unknown",
                bounds=bounds
            )
        except CRSError:
            return None
    
    def validate_epsg(self, epsg: int) -> Tuple[bool, Optional[str]]:
        """
        Validate if an EPSG code is valid.
        
        Args:
            epsg: EPSG code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            crs = CRS.from_epsg(epsg)
            return True, None
        except CRSError as e:
            return False, f"Invalid EPSG code {epsg}: {str(e)}"
    
    def validate_wkt(self, wkt: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a WKT CRS definition.
        
        Args:
            wkt: Well-Known Text CRS definition
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            crs = CRS.from_wkt(wkt)
            return True, None
        except Exception as e:
            return False, f"Invalid WKT: {str(e)}"
    
    def get_crs_wkt(self, epsg: int) -> Optional[str]:
        """
        Get the WKT representation of an EPSG code.
        
        Args:
            epsg: EPSG code
            
        Returns:
            WKT string or None
        """
        try:
            crs = CRS.from_epsg(epsg)
            return crs.to_wkt()
        except CRSError:
            return None
    
    def _get_transformer(self, from_epsg: int, to_epsg: int) -> Transformer:
        """Get or create a cached transformer."""
        cache_key = (from_epsg, to_epsg)
        
        if cache_key not in self._transformer_cache:
            from_crs = CRS.from_epsg(from_epsg)
            to_crs = CRS.from_epsg(to_epsg)
            self._transformer_cache[cache_key] = Transformer.from_crs(
                from_crs, to_crs, always_xy=True
            )
        
        return self._transformer_cache[cache_key]
    
    def transform_point(
        self,
        x: float,
        y: float,
        z: float,
        from_epsg: int,
        to_epsg: int
    ) -> Tuple[float, float, float]:
        """
        Transform a single point between coordinate systems.
        
        Args:
            x, y, z: Source coordinates
            from_epsg: Source EPSG code
            to_epsg: Target EPSG code
            
        Returns:
            Tuple of (x, y, z) in target CRS
        """
        transformer = self._get_transformer(from_epsg, to_epsg)
        tx, ty = transformer.transform(x, y)
        return (tx, ty, z)  # Z is preserved (vertical datum not transformed)
    
    def transform_points(
        self,
        points: List[Tuple[float, float, float]],
        from_epsg: int,
        to_epsg: int
    ) -> TransformResult:
        """
        Transform multiple points between coordinate systems.
        
        Args:
            points: List of (x, y, z) tuples
            from_epsg: Source EPSG code
            to_epsg: Target EPSG code
            
        Returns:
            TransformResult with transformed coordinates
        """
        errors = []
        transformed = []
        
        try:
            transformer = self._get_transformer(from_epsg, to_epsg)
            
            for i, (x, y, z) in enumerate(points):
                try:
                    tx, ty = transformer.transform(x, y)
                    transformed.append((tx, ty, z))
                except Exception as e:
                    errors.append(f"Point {i}: {str(e)}")
                    transformed.append((float('nan'), float('nan'), z))
            
            return TransformResult(
                success=len(errors) == 0,
                source_crs=from_epsg,
                target_crs=to_epsg,
                source_points=points,
                transformed_points=transformed,
                point_count=len(points),
                errors=errors
            )
        except CRSError as e:
            return TransformResult(
                success=False,
                source_crs=from_epsg,
                target_crs=to_epsg,
                source_points=points,
                transformed_points=[],
                point_count=len(points),
                errors=[f"CRS error: {str(e)}"]
            )
    
    def detect_utm_zone(self, longitude: float, latitude: float) -> int:
        """
        Detect the appropriate UTM zone EPSG code for a lat/lon coordinate.
        
        Args:
            longitude: Longitude in degrees (-180 to 180)
            latitude: Latitude in degrees (-90 to 90)
            
        Returns:
            EPSG code for the UTM zone
        """
        # Calculate UTM zone number
        zone = int((longitude + 180) / 6) + 1
        
        # Handle special cases
        if latitude >= 56.0 and latitude < 64.0:
            if longitude >= 3.0 and longitude < 12.0:
                zone = 32
        
        # Svalbard special zones
        if latitude >= 72.0 and latitude < 84.0:
            if longitude >= 0.0 and longitude < 9.0:
                zone = 31
            elif longitude >= 9.0 and longitude < 21.0:
                zone = 33
            elif longitude >= 21.0 and longitude < 33.0:
                zone = 35
            elif longitude >= 33.0 and longitude < 42.0:
                zone = 37
        
        # Determine hemisphere and construct EPSG code
        if latitude >= 0:
            # Northern hemisphere: 326xx
            return 32600 + zone
        else:
            # Southern hemisphere: 327xx
            return 32700 + zone
    
    def detect_sa_lo_zone(self, longitude: float) -> int:
        """
        Detect the appropriate South African Lo zone EPSG code.
        
        Args:
            longitude: Longitude in degrees
            
        Returns:
            EPSG code for the SA Lo zone
        """
        # SA Lo zones are at odd meridians: 15, 17, 19, etc.
        # Find the nearest odd meridian
        central_meridian = int(longitude)
        if central_meridian % 2 == 0:
            # Round to nearest odd
            if longitude - central_meridian >= 0.5:
                central_meridian += 1
            else:
                central_meridian -= 1
        
        # Map central meridian to EPSG
        # Lo15 = 2046, Lo17 = 2047, etc.
        lo_zone_map = {
            15: 2046, 17: 2047, 19: 2048, 21: 2049, 23: 2050,
            25: 2051, 27: 2052, 29: 2053, 31: 2054, 33: 2055
        }
        
        return lo_zone_map.get(central_meridian, 2052)  # Default to Lo27 (Mpumalanga)
    
    def detect_best_crs(
        self, 
        longitude: float, 
        latitude: float,
        region: Optional[str] = None
    ) -> int:
        """
        Detect the best CRS for a given location.
        
        Args:
            longitude: Longitude in degrees
            latitude: Latitude in degrees
            region: Optional region hint (e.g., "South Africa")
            
        Returns:
            Best EPSG code for the location
        """
        if region:
            region_lower = region.lower()
            
            if "south africa" in region_lower or "sa" == region_lower:
                return self.detect_sa_lo_zone(longitude)
            
            if "australia" in region_lower:
                # MGA zones
                zone = int((longitude + 180) / 6) + 1
                if 49 <= zone <= 56:
                    return 28300 + zone  # MGA zones
            
            if "indonesia" in region_lower:
                zone = int((longitude + 180) / 6) + 1
                if latitude >= 0:
                    return 23800 + zone  # DGN95 North
                else:
                    return 23850 + zone  # DGN95 South
            
            if "usa" in region_lower or "united states" in region_lower:
                zone = int((longitude + 180) / 6) + 1
                return 26900 + zone  # NAD83 UTM
        
        # Default to WGS84 UTM
        return self.detect_utm_zone(longitude, latitude)
    
    def get_regions(self) -> List[str]:
        """Get list of supported regions."""
        regions = set(crs.region for crs in SUPPORTED_CRS.values())
        return sorted(list(regions))
    
    def get_crs_for_region(self, region: str) -> List[CRSInfo]:
        """Get all CRS options for a specific region."""
        return [
            crs for crs in SUPPORTED_CRS.values() 
            if region.lower() in crs.region.lower()
        ]


# Factory function
_crs_service_instance: Optional[CRSService] = None

def get_crs_service() -> CRSService:
    """Get the CRS service singleton instance."""
    global _crs_service_instance
    if _crs_service_instance is None:
        _crs_service_instance = CRSService()
    return _crs_service_instance
