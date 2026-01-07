"""
Surface Service - Phase 2 TIN Surface Generation

Service for creating and manipulating TIN (Triangulated Irregular Network) surfaces.
Uses scipy.spatial.Delaunay for triangulation (BSD license - FREE).

Features:
- Generate TIN from point data
- Create seam surfaces from borehole data
- Query elevation at any XY point
- Generate contour lines
- Calculate volume between surfaces
- Calculate cut/fill, seam tonnage, ramp/dump volumes
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
import uuid
import datetime
import math

# Use scipy for Delaunay triangulation (BSD license - FREE)
try:
    import numpy as np
    from scipy.spatial import Delaunay
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    np = None

from .dxf_service import get_dxf_service, DXFPoint
from .ascii_grid_service import get_ascii_grid_service, XYZPoint


@dataclass
class Point3D:
    """A 3D point."""
    x: float
    y: float
    z: float
    
    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class Triangle:
    """A triangle defined by vertex indices."""
    i: int
    j: int
    k: int
    
    def as_tuple(self) -> Tuple[int, int, int]:
        return (self.i, self.j, self.k)


@dataclass
class TINSurface:
    """An in-memory TIN surface representation."""
    name: str
    vertices: List[Point3D]
    triangles: List[Triangle]
    surface_type: str = "terrain"
    seam_name: Optional[str] = None
    
    @property
    def vertex_count(self) -> int:
        return len(self.vertices)
    
    @property
    def triangle_count(self) -> int:
        return len(self.triangles)
    
    def get_extent(self) -> Tuple[Point3D, Point3D]:
        """Get bounding box as (min_point, max_point)."""
        if not self.vertices:
            return (Point3D(0, 0, 0), Point3D(0, 0, 0))
        
        xs = [v.x for v in self.vertices]
        ys = [v.y for v in self.vertices]
        zs = [v.z for v in self.vertices]
        
        return (
            Point3D(min(xs), min(ys), min(zs)),
            Point3D(max(xs), max(ys), max(zs))
        )
    
    def to_vertex_list(self) -> List[Tuple[float, float, float]]:
        """Get vertices as list of tuples."""
        return [v.as_tuple() for v in self.vertices]
    
    def to_triangle_list(self) -> List[Tuple[int, int, int]]:
        """Get triangles as list of tuples."""
        return [t.as_tuple() for t in self.triangles]


@dataclass
class VolumeResult:
    """Result of volume calculation."""
    volume_m3: float
    tonnage: float = 0.0  # volume * density
    cut_volume: float = 0.0
    fill_volume: float = 0.0
    net_volume: float = 0.0
    area_m2: float = 0.0
    density_used: float = 0.0
    swell_factor: float = 1.0


@dataclass
class SeamTonnage:
    """Coal seam tonnage calculation result."""
    in_situ_tonnes: float
    rom_tonnes: float  # After mining losses
    product_tonnes: float  # After yield
    seam_name: str
    roof_surface: str
    floor_surface: str
    thickness_avg: float
    thickness_min: float
    thickness_max: float
    area_m2: float
    volume_m3: float
    density_t_m3: float
    mining_loss_pct: float
    yield_pct: float


@dataclass
class Contour:
    """A contour line at a specific elevation."""
    elevation: float
    points: List[Tuple[float, float, float]]
    is_closed: bool = False


class SurfaceService:
    """
    Service for TIN surface generation and manipulation.
    
    Uses scipy.spatial.Delaunay for triangulation (BSD license - FREE).
    All methods work with free/open-source libraries only.
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check that required libraries are available."""
        if not SCIPY_AVAILABLE:
            raise ImportError(
                "numpy and scipy are required for surface generation. "
                "Install with: pip install numpy scipy"
            )
    
    # =========================================================================
    # TIN GENERATION
    # =========================================================================
    
    def create_tin_from_points(
        self,
        points: List[Tuple[float, float, float]],
        name: str = "Surface",
        surface_type: str = "terrain"
    ) -> TINSurface:
        """
        Create a TIN surface from 3D points using Delaunay triangulation.
        
        Args:
            points: List of (x, y, z) coordinates
            name: Surface name
            surface_type: Type of surface
            
        Returns:
            TINSurface object with triangulated geometry
        """
        if len(points) < 3:
            raise ValueError("At least 3 points required for triangulation")
        
        # Convert to numpy array for scipy
        pts_array = np.array(points)
        
        # 2D Delaunay triangulation (on XY plane)
        # This creates a 2.5D surface (regular in XY, elevation varies)
        pts_2d = pts_array[:, :2]  # Just X, Y
        
        tri = Delaunay(pts_2d)
        
        # Build vertices
        vertices = [Point3D(x=p[0], y=p[1], z=p[2]) for p in points]
        
        # Build triangles from Delaunay simplices
        triangles = [Triangle(i=int(s[0]), j=int(s[1]), k=int(s[2])) 
                     for s in tri.simplices]
        
        return TINSurface(
            name=name,
            vertices=vertices,
            triangles=triangles,
            surface_type=surface_type
        )
    
    def create_tin_from_xyz_points(
        self,
        xyz_points: List[XYZPoint],
        name: str = "Surface",
        surface_type: str = "terrain"
    ) -> TINSurface:
        """Create TIN from XYZPoint objects."""
        points = [(p.x, p.y, p.z) for p in xyz_points]
        return self.create_tin_from_points(points, name, surface_type)
    
    def create_tin_from_boreholes(
        self,
        collar_data: List[Dict],
        seam_name: Optional[str] = None,
        surface_type: str = "terrain",
        use_collar_elevations: bool = True,
        interval_data: Optional[List[Dict]] = None
    ) -> TINSurface:
        """
        Create TIN surface from borehole data.
        
        For terrain: uses collar elevations
        For seam surfaces: uses interval from/to depths
        
        Args:
            collar_data: List of collar dicts with easting, northing, elevation
            seam_name: Seam name for filtering intervals
            surface_type: 'terrain', 'seam_roof', or 'seam_floor'
            use_collar_elevations: If True, create terrain from collars
            interval_data: Interval data for seam surfaces
            
        Returns:
            TINSurface
        """
        points = []
        
        if use_collar_elevations and surface_type == "terrain":
            # Create terrain surface from collar elevations
            for collar in collar_data:
                x = collar.get("easting", collar.get("x", 0))
                y = collar.get("northing", collar.get("y", 0))
                z = collar.get("elevation", collar.get("z", 0))
                points.append((x, y, z))
        
        elif interval_data and seam_name:
            # Create seam surface from interval data
            # Build collar lookup
            collar_lookup = {}
            for collar in collar_data:
                hole_id = collar.get("hole_id", collar.get("id"))
                collar_lookup[hole_id] = {
                    "x": collar.get("easting", collar.get("x", 0)),
                    "y": collar.get("northing", collar.get("y", 0)),
                    "z": collar.get("elevation", collar.get("z", 0)),
                    "azimuth": collar.get("azimuth", 0),
                    "dip": collar.get("dip", -90)
                }
            
            # Find seam intervals
            for interval in interval_data:
                hole_id = interval.get("hole_id")
                interval_seam = interval.get("seam_name", "")
                
                if seam_name.lower() not in interval_seam.lower():
                    continue
                
                if hole_id not in collar_lookup:
                    continue
                
                collar = collar_lookup[hole_id]
                
                # Simple vertical projection (for near-vertical holes)
                # For inclined holes, would need proper 3D trace calculation
                if surface_type == "seam_roof":
                    depth = interval.get("from_depth", 0)
                else:  # seam_floor
                    depth = interval.get("to_depth", 0)
                
                x = collar["x"]
                y = collar["y"]
                z = collar["z"] - depth  # Subtract depth from collar elevation
                
                points.append((x, y, z))
        
        if len(points) < 3:
            raise ValueError(f"Not enough points ({len(points)}) to create surface")
        
        tin = self.create_tin_from_points(points, name=f"{seam_name or 'Surface'}", 
                                          surface_type=surface_type)
        tin.seam_name = seam_name
        return tin
    
    # =========================================================================
    # SURFACE QUERIES
    # =========================================================================
    
    def query_elevation(
        self,
        surface: TINSurface,
        x: float,
        y: float
    ) -> Optional[float]:
        """
        Query the elevation at a specific XY location on the surface.
        
        Uses barycentric interpolation within the containing triangle.
        
        Args:
            surface: The TIN surface
            x, y: Query coordinates
            
        Returns:
            Interpolated elevation, or None if point outside surface
        """
        # Find containing triangle
        for tri in surface.triangles:
            v0 = surface.vertices[tri.i]
            v1 = surface.vertices[tri.j]
            v2 = surface.vertices[tri.k]
            
            # Check if point is inside triangle (2D)
            if self._point_in_triangle(x, y, v0.x, v0.y, v1.x, v1.y, v2.x, v2.y):
                # Barycentric interpolation
                z = self._barycentric_interpolate(
                    x, y,
                    v0.x, v0.y, v0.z,
                    v1.x, v1.y, v1.z,
                    v2.x, v2.y, v2.z
                )
                return z
        
        return None
    
    def _point_in_triangle(
        self, px, py, 
        ax, ay, bx, by, cx, cy
    ) -> bool:
        """Check if point (px, py) is inside triangle ABC."""
        def sign(p1x, p1y, p2x, p2y, p3x, p3y):
            return (p1x - p3x) * (p2y - p3y) - (p2x - p3x) * (p1y - p3y)
        
        d1 = sign(px, py, ax, ay, bx, by)
        d2 = sign(px, py, bx, by, cx, cy)
        d3 = sign(px, py, cx, cy, ax, ay)
        
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        
        return not (has_neg and has_pos)
    
    def _barycentric_interpolate(
        self, px, py,
        ax, ay, az,
        bx, by, bz,
        cx, cy, cz
    ) -> float:
        """Interpolate Z using barycentric coordinates."""
        denom = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        
        if abs(denom) < 1e-10:
            return (az + bz + cz) / 3  # Degenerate triangle
        
        w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / denom
        w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / denom
        w2 = 1 - w0 - w1
        
        return w0 * az + w1 * bz + w2 * cz
    
    # =========================================================================
    # SURFACE STATISTICS
    # =========================================================================
    
    def calculate_surface_area(self, surface: TINSurface) -> float:
        """Calculate total surface area in m²."""
        total_area = 0.0
        
        for tri in surface.triangles:
            v0 = surface.vertices[tri.i]
            v1 = surface.vertices[tri.j]
            v2 = surface.vertices[tri.k]
            
            # Triangle area using cross product
            area = self._triangle_area_3d(
                v0.x, v0.y, v0.z,
                v1.x, v1.y, v1.z,
                v2.x, v2.y, v2.z
            )
            total_area += area
        
        return total_area
    
    def _triangle_area_3d(
        self,
        ax, ay, az,
        bx, by, bz,
        cx, cy, cz
    ) -> float:
        """Calculate 3D triangle area using cross product."""
        # Vectors AB and AC
        abx, aby, abz = bx - ax, by - ay, bz - az
        acx, acy, acz = cx - ax, cy - ay, cz - az
        
        # Cross product AB x AC
        cx = aby * acz - abz * acy
        cy = abz * acx - abx * acz
        cz = abx * acy - aby * acx
        
        # Area = 0.5 * |cross product|
        return 0.5 * math.sqrt(cx*cx + cy*cy + cz*cz)
    
    # =========================================================================
    # VOLUME CALCULATIONS
    # =========================================================================
    
    def calculate_volume_between_surfaces(
        self,
        upper: TINSurface,
        lower: TINSurface,
        grid_spacing: float = 5.0,
        boundary: Optional[List[Tuple[float, float]]] = None
    ) -> VolumeResult:
        """
        Calculate volume between two surfaces using grid sampling.
        
        Args:
            upper: Upper surface (e.g., terrain or seam roof)
            lower: Lower surface (e.g., seam floor)
            grid_spacing: Spacing for volume calculation grid (meters)
            boundary: Optional boundary polygon [(x, y), ...]
            
        Returns:
            VolumeResult with cut/fill volumes
        """
        # Determine calculation extent
        upper_min, upper_max = upper.get_extent()
        lower_min, lower_max = lower.get_extent()
        
        min_x = max(upper_min.x, lower_min.x)
        max_x = min(upper_max.x, lower_max.x)
        min_y = max(upper_min.y, lower_min.y)
        max_y = min(upper_max.y, lower_max.y)
        
        if min_x >= max_x or min_y >= max_y:
            return VolumeResult(volume_m3=0.0)
        
        # Create calculation grid
        nx = int((max_x - min_x) / grid_spacing) + 1
        ny = int((max_y - min_y) / grid_spacing) + 1
        
        total_volume = 0.0
        cut_volume = 0.0
        fill_volume = 0.0
        valid_cells = 0
        
        cell_area = grid_spacing * grid_spacing
        
        for i in range(nx):
            for j in range(ny):
                x = min_x + i * grid_spacing
                y = min_y + j * grid_spacing
                
                # Check if inside boundary
                if boundary and not self._point_in_polygon(x, y, boundary):
                    continue
                
                # Query elevations
                z_upper = self.query_elevation(upper, x, y)
                z_lower = self.query_elevation(lower, x, y)
                
                if z_upper is not None and z_lower is not None:
                    thickness = z_upper - z_lower
                    cell_volume = thickness * cell_area
                    
                    total_volume += abs(cell_volume)
                    
                    if thickness > 0:
                        cut_volume += cell_volume
                    else:
                        fill_volume += abs(cell_volume)
                    
                    valid_cells += 1
        
        return VolumeResult(
            volume_m3=total_volume,
            cut_volume=cut_volume,
            fill_volume=fill_volume,
            net_volume=cut_volume - fill_volume,
            area_m2=valid_cells * cell_area
        )
    
    def calculate_seam_tonnage(
        self,
        roof: TINSurface,
        floor: TINSurface,
        density_t_m3: float = 1.4,
        mining_loss_pct: float = 5.0,
        yield_pct: float = 85.0,
        grid_spacing: float = 5.0,
        boundary: Optional[List[Tuple[float, float]]] = None
    ) -> SeamTonnage:
        """
        Calculate coal seam tonnage between roof and floor surfaces.
        
        Args:
            roof: Seam roof surface
            floor: Seam floor surface
            density_t_m3: Coal density in tonnes per m³
            mining_loss_pct: Mining loss percentage
            yield_pct: Wash plant yield percentage
            grid_spacing: Grid spacing for calculation
            boundary: Optional mining boundary
            
        Returns:
            SeamTonnage with in-situ, ROM, and product tonnes
        """
        # Calculate volume
        vol_result = self.calculate_volume_between_surfaces(
            roof, floor, grid_spacing, boundary
        )
        
        # Calculate thicknesses
        thicknesses = []
        roof_min, roof_max = roof.get_extent()
        floor_min, floor_max = floor.get_extent()
        
        min_x = max(roof_min.x, floor_min.x)
        max_x = min(roof_max.x, floor_max.x)
        min_y = max(roof_min.y, floor_min.y)
        max_y = min(roof_max.y, floor_max.y)
        
        for i in range(int((max_x - min_x) / grid_spacing) + 1):
            for j in range(int((max_y - min_y) / grid_spacing) + 1):
                x = min_x + i * grid_spacing
                y = min_y + j * grid_spacing
                
                z_roof = self.query_elevation(roof, x, y)
                z_floor = self.query_elevation(floor, x, y)
                
                if z_roof is not None and z_floor is not None:
                    thicknesses.append(z_roof - z_floor)
        
        # Calculate tonnages
        in_situ_tonnes = vol_result.cut_volume * density_t_m3
        rom_tonnes = in_situ_tonnes * (1 - mining_loss_pct / 100)
        product_tonnes = rom_tonnes * (yield_pct / 100)
        
        return SeamTonnage(
            in_situ_tonnes=in_situ_tonnes,
            rom_tonnes=rom_tonnes,
            product_tonnes=product_tonnes,
            seam_name=roof.seam_name or floor.seam_name or "Unknown",
            roof_surface=roof.name,
            floor_surface=floor.name,
            thickness_avg=sum(thicknesses) / len(thicknesses) if thicknesses else 0,
            thickness_min=min(thicknesses) if thicknesses else 0,
            thickness_max=max(thicknesses) if thicknesses else 0,
            area_m2=vol_result.area_m2,
            volume_m3=vol_result.cut_volume,
            density_t_m3=density_t_m3,
            mining_loss_pct=mining_loss_pct,
            yield_pct=yield_pct
        )
    
    def calculate_cut_fill(
        self,
        design: TINSurface,
        existing: TINSurface,
        swell_factor: float = 1.3,
        grid_spacing: float = 5.0,
        boundary: Optional[List[Tuple[float, float]]] = None
    ) -> VolumeResult:
        """
        Calculate cut and fill volumes for earthworks.
        
        Args:
            design: Design surface
            existing: Existing surface (terrain)
            swell_factor: Material swell factor for fill
            grid_spacing: Grid spacing
            boundary: Optional boundary
            
        Returns:
            VolumeResult with cut and fill volumes
        """
        result = self.calculate_volume_between_surfaces(
            existing, design, grid_spacing, boundary
        )
        
        # Apply swell factor to fill volume
        result.fill_volume = result.fill_volume * swell_factor
        result.swell_factor = swell_factor
        
        return result
    
    def _point_in_polygon(
        self, x: float, y: float, 
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """Check if point is inside polygon using ray casting."""
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    # =========================================================================
    # CONTOUR GENERATION
    # =========================================================================
    
    def generate_contours(
        self,
        surface: TINSurface,
        interval: float = 5.0,
        min_elevation: Optional[float] = None,
        max_elevation: Optional[float] = None
    ) -> List[Contour]:
        """
        Generate contour lines from a TIN surface.
        
        Uses edge intersection algorithm to find contour paths.
        
        Args:
            surface: TIN surface
            interval: Contour interval (meters)
            min_elevation: Minimum contour elevation (auto if None)
            max_elevation: Maximum contour elevation (auto if None)
            
        Returns:
            List of Contour objects
        """
        extent_min, extent_max = surface.get_extent()
        
        if min_elevation is None:
            min_elevation = math.floor(extent_min.z / interval) * interval
        if max_elevation is None:
            max_elevation = math.ceil(extent_max.z / interval) * interval
        
        contours = []
        
        # Generate contours for each elevation level
        elevation = min_elevation
        while elevation <= max_elevation:
            contour_points = self._extract_contour_at_elevation(surface, elevation)
            
            if contour_points:
                # Simple approach: collect all intersection points
                # More sophisticated would chain them into connected lines
                contours.append(Contour(
                    elevation=elevation,
                    points=contour_points,
                    is_closed=False
                ))
            
            elevation += interval
        
        return contours
    
    def _extract_contour_at_elevation(
        self,
        surface: TINSurface,
        elevation: float
    ) -> List[Tuple[float, float, float]]:
        """Extract contour line segments at a specific elevation."""
        segments = []
        
        for tri in surface.triangles:
            v0 = surface.vertices[tri.i]
            v1 = surface.vertices[tri.j]
            v2 = surface.vertices[tri.k]
            
            # Find edge intersections with the contour plane
            intersections = []
            
            # Check each edge
            edges = [(v0, v1), (v1, v2), (v2, v0)]
            
            for va, vb in edges:
                # Check if edge crosses the elevation
                if (va.z <= elevation <= vb.z) or (vb.z <= elevation <= va.z):
                    if abs(vb.z - va.z) < 1e-10:
                        continue  # Horizontal edge
                    
                    # Interpolate intersection point
                    t = (elevation - va.z) / (vb.z - va.z)
                    x = va.x + t * (vb.x - va.x)
                    y = va.y + t * (vb.y - va.y)
                    intersections.append((x, y, elevation))
            
            # Should have 0 or 2 intersections per triangle
            if len(intersections) == 2:
                segments.extend(intersections)
        
        return segments
    
    # =========================================================================
    # EXPORT/SAVE
    # =========================================================================
    
    def save_surface(
        self,
        surface: TINSurface,
        site_id: str,
        created_by: Optional[str] = None
    ) -> str:
        """
        Save a TIN surface to the database.
        
        Args:
            surface: TIN surface to save
            site_id: Site ID
            created_by: User ID
            
        Returns:
            Surface ID
        """
        from ..domain.models_surface import Surface
        
        surface_id = str(uuid.uuid4())
        
        db_surface = Surface(
            surface_id=surface_id,
            site_id=site_id,
            name=surface.name,
            surface_type=surface.surface_type,
            seam_name=surface.seam_name,
            vertex_data=[v.as_tuple() for v in surface.vertices],
            triangle_data=[t.as_tuple() for t in surface.triangles],
            vertex_count=surface.vertex_count,
            triangle_count=surface.triangle_count,
            created_by=created_by
        )
        
        # Set geometry (calculates extents)
        db_surface.set_geometry(
            surface.to_vertex_list(),
            surface.to_triangle_list()
        )
        
        # Calculate area
        db_surface.area_m2 = self.calculate_surface_area(surface)
        
        self.db.add(db_surface)
        self.db.commit()
        
        return surface_id
    
    def load_surface(self, surface_id: str) -> Optional[TINSurface]:
        """Load a TIN surface from the database."""
        from ..domain.models_surface import Surface
        
        db_surface = self.db.query(Surface).filter(
            Surface.surface_id == surface_id
        ).first()
        
        if not db_surface:
            return None
        
        vertices = [Point3D(x=v[0], y=v[1], z=v[2]) 
                    for v in db_surface.vertex_data]
        triangles = [Triangle(i=t[0], j=t[1], k=t[2]) 
                     for t in db_surface.triangle_data]
        
        return TINSurface(
            name=db_surface.name,
            vertices=vertices,
            triangles=triangles,
            surface_type=db_surface.surface_type,
            seam_name=db_surface.seam_name
        )
    
    def export_to_dxf(
        self,
        surface: TINSurface,
        file_path: Optional[str] = None
    ) -> Optional[bytes]:
        """Export surface to DXF format."""
        dxf = get_dxf_service()
        return dxf.export_tin_surface(
            vertices=surface.to_vertex_list(),
            triangles=surface.to_triangle_list(),
            layer_name=f"SURFACE_{surface.name.upper()}",
            file_path=file_path
        )
    
    def export_to_xyz(
        self,
        surface: TINSurface,
        file_path: Optional[str] = None
    ) -> Optional[str]:
        """Export surface vertices to XYZ format."""
        grid = get_ascii_grid_service()
        xyz_points = [XYZPoint(x=v.x, y=v.y, z=v.z) for v in surface.vertices]
        return grid.export_xyz(xyz_points, file_path=file_path)


# Factory function
def get_surface_service(db: Optional[Session] = None) -> SurfaceService:
    """Get a surface service instance."""
    return SurfaceService(db)
