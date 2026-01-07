"""
Surface Tools Service - Phase 3

Advanced surface manipulation and analysis tools.
Extends base SurfaceService with geometry, transformation, and refinement operations.

Features:
- Geometry: clip, merge, boolean operations, extend, trim
- Transformation: translate, rotate, scale, mirror
- Refinement: smooth, densify, simplify, fill holes, resample
- Analysis: slope, aspect, curvature, sections, profiles, watershed
- Interpolation: drape points/polylines, sample elevations
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
import math
import uuid
import logging
from collections import defaultdict

try:
    import numpy as np
    from scipy.spatial import Delaunay
    from scipy.interpolate import griddata, LinearNDInterpolator
    from scipy.ndimage import gaussian_filter
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    np = None

try:
    from shapely.geometry import Polygon, LineString, Point, MultiPoint
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

from .surface_service import SurfaceService, TINSurface, Point3D, Triangle


# =============================================================================
# Data Classes for Results
# =============================================================================

@dataclass
class SlopeResult:
    """Slope analysis result for a point or area."""
    slope_degrees: float
    slope_percent: float
    aspect_degrees: float  # Direction of steepest descent (0=N, 90=E, 180=S, 270=W)


@dataclass
class SlopeMap:
    """Grid-based slope map."""
    grid_spacing: float
    origin: Tuple[float, float]
    rows: int
    cols: int
    slopes: List[List[float]]  # Degrees
    aspects: List[List[float]]  # Degrees


@dataclass
class ProfilePoint:
    """Point along a profile line."""
    distance: float  # Horizontal distance from start
    x: float
    y: float
    z: float
    slope_to_next: Optional[float] = None


@dataclass
class SurfaceProfile:
    """Cross-section profile along a line."""
    points: List[ProfilePoint]
    total_distance: float
    min_elevation: float
    max_elevation: float
    avg_elevation: float


@dataclass
class IsopachResult:
    """Thickness map between two surfaces."""
    grid_spacing: float
    origin: Tuple[float, float]
    rows: int
    cols: int
    thickness: List[List[float]]
    min_thickness: float
    max_thickness: float
    avg_thickness: float


# =============================================================================
# Surface Tools Service
# =============================================================================

class SurfaceToolsService:
    """
    Advanced surface manipulation and analysis tools.
    
    Provides comprehensive operations for mining surface data:
    - Geometry operations (clip, merge, boolean)
    - Transformations (translate, rotate, scale)
    - Refinement (smooth, simplify, densify)
    - Analysis (slope, aspect, profiles, watershed)
    """
    
    def __init__(self, base_service: Optional[SurfaceService] = None):
        """Initialize with optional base service."""
        self.logger = logging.getLogger(__name__)
        self._base_service = base_service or SurfaceService()
        
        if not SCIPY_AVAILABLE:
            self.logger.warning("numpy/scipy not available - some operations limited")
    
    # =========================================================================
    # GEOMETRY OPERATIONS
    # =========================================================================
    
    def clip_to_boundary(
        self,
        surface: TINSurface,
        boundary: List[Tuple[float, float]],
        name: Optional[str] = None
    ) -> TINSurface:
        """
        Clip a surface to a boundary polygon.
        
        Args:
            surface: Surface to clip
            boundary: Boundary polygon as [(x, y), ...]
            name: Name for clipped surface
            
        Returns:
            New clipped TINSurface
        """
        # Find vertices inside boundary
        inside_indices = []
        for i, v in enumerate(surface.vertices):
            if self._point_in_polygon(v.x, v.y, boundary):
                inside_indices.append(i)
        
        if not inside_indices:
            raise ValueError("No vertices inside boundary")
        
        # Build index mapping
        old_to_new = {old: new for new, old in enumerate(inside_indices)}
        
        # Collect vertices inside boundary
        new_vertices = [surface.vertices[i] for i in inside_indices]
        
        # Filter triangles - keep only those with all vertices inside
        new_triangles = []
        for tri in surface.triangles:
            if tri.i in old_to_new and tri.j in old_to_new and tri.k in old_to_new:
                new_triangles.append(Triangle(
                    i=old_to_new[tri.i],
                    j=old_to_new[tri.j],
                    k=old_to_new[tri.k]
                ))
        
        if len(new_triangles) == 0:
            # Re-triangulate inside vertices
            if len(new_vertices) >= 3:
                points = [(v.x, v.y, v.z) for v in new_vertices]
                return self._base_service.create_tin_from_points(
                    points,
                    name=name or f"{surface.name}_clipped",
                    surface_type=surface.surface_type
                )
            else:
                raise ValueError("Not enough vertices for triangulation")
        
        return TINSurface(
            name=name or f"{surface.name}_clipped",
            vertices=new_vertices,
            triangles=new_triangles,
            surface_type=surface.surface_type,
            seam_name=surface.seam_name
        )
    
    def merge_surfaces(
        self,
        surfaces: List[TINSurface],
        name: str = "Merged Surface"
    ) -> TINSurface:
        """
        Merge multiple surfaces into one.
        
        Combines all vertices and re-triangulates.
        
        Args:
            surfaces: List of surfaces to merge
            name: Name for merged surface
            
        Returns:
            Merged TINSurface
        """
        if not surfaces:
            raise ValueError("No surfaces to merge")
        
        if len(surfaces) == 1:
            return surfaces[0]
        
        # Collect all points
        all_points = []
        for surface in surfaces:
            for v in surface.vertices:
                all_points.append((v.x, v.y, v.z))
        
        # Remove duplicates (within tolerance)
        unique_points = self._remove_duplicate_points(all_points, tolerance=0.01)
        
        if len(unique_points) < 3:
            raise ValueError("Not enough unique points for triangulation")
        
        # Re-triangulate
        return self._base_service.create_tin_from_points(
            unique_points,
            name=name,
            surface_type=surfaces[0].surface_type
        )
    
    def _remove_duplicate_points(
        self,
        points: List[Tuple[float, float, float]],
        tolerance: float = 0.01
    ) -> List[Tuple[float, float, float]]:
        """Remove duplicate points within tolerance."""
        if not points:
            return []
        
        unique = [points[0]]
        
        for p in points[1:]:
            is_duplicate = False
            for u in unique:
                dist = math.sqrt((p[0]-u[0])**2 + (p[1]-u[1])**2 + (p[2]-u[2])**2)
                if dist < tolerance:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(p)
        
        return unique
    
    # =========================================================================
    # TRANSFORMATION OPERATIONS
    # =========================================================================
    
    def translate_surface(
        self,
        surface: TINSurface,
        dx: float,
        dy: float,
        dz: float
    ) -> TINSurface:
        """
        Translate (move) a surface.
        
        Args:
            surface: Surface to translate
            dx, dy, dz: Translation offsets
            
        Returns:
            New translated TINSurface
        """
        new_vertices = [
            Point3D(x=v.x + dx, y=v.y + dy, z=v.z + dz)
            for v in surface.vertices
        ]
        
        return TINSurface(
            name=f"{surface.name}_translated",
            vertices=new_vertices,
            triangles=list(surface.triangles),  # Triangles stay same
            surface_type=surface.surface_type,
            seam_name=surface.seam_name
        )
    
    def rotate_surface(
        self,
        surface: TINSurface,
        angle_degrees: float,
        center_x: float,
        center_y: float
    ) -> TINSurface:
        """
        Rotate a surface around a point (XY plane only).
        
        Args:
            surface: Surface to rotate
            angle_degrees: Rotation angle (counterclockwise positive)
            center_x, center_y: Rotation center
            
        Returns:
            New rotated TINSurface
        """
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        new_vertices = []
        for v in surface.vertices:
            # Translate to origin
            tx = v.x - center_x
            ty = v.y - center_y
            
            # Rotate
            rx = tx * cos_a - ty * sin_a
            ry = tx * sin_a + ty * cos_a
            
            # Translate back
            new_vertices.append(Point3D(
                x=rx + center_x,
                y=ry + center_y,
                z=v.z
            ))
        
        return TINSurface(
            name=f"{surface.name}_rotated",
            vertices=new_vertices,
            triangles=list(surface.triangles),
            surface_type=surface.surface_type,
            seam_name=surface.seam_name
        )
    
    def scale_surface(
        self,
        surface: TINSurface,
        factor_xy: float,
        factor_z: float = 1.0,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None
    ) -> TINSurface:
        """
        Scale a surface from a center point.
        
        Args:
            surface: Surface to scale
            factor_xy: XY scale factor
            factor_z: Z scale factor (default 1.0 = no change)
            center_x, center_y: Scale center (default = centroid)
            
        Returns:
            New scaled TINSurface
        """
        # Calculate centroid if center not provided
        if center_x is None or center_y is None:
            center_x = sum(v.x for v in surface.vertices) / len(surface.vertices)
            center_y = sum(v.y for v in surface.vertices) / len(surface.vertices)
        
        center_z = sum(v.z for v in surface.vertices) / len(surface.vertices)
        
        new_vertices = []
        for v in surface.vertices:
            new_vertices.append(Point3D(
                x=center_x + (v.x - center_x) * factor_xy,
                y=center_y + (v.y - center_y) * factor_xy,
                z=center_z + (v.z - center_z) * factor_z
            ))
        
        return TINSurface(
            name=f"{surface.name}_scaled",
            vertices=new_vertices,
            triangles=list(surface.triangles),
            surface_type=surface.surface_type,
            seam_name=surface.seam_name
        )
    
    def mirror_surface(
        self,
        surface: TINSurface,
        axis_point1: Tuple[float, float],
        axis_point2: Tuple[float, float]
    ) -> TINSurface:
        """
        Mirror a surface across an axis line.
        
        Args:
            surface: Surface to mirror
            axis_point1: First point on mirror axis
            axis_point2: Second point on mirror axis
            
        Returns:
            New mirrored TINSurface
        """
        x1, y1 = axis_point1
        x2, y2 = axis_point2
        
        # Direction vector
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1e-10:
            raise ValueError("Mirror axis points too close")
        
        # Unit direction
        ux = dx / length
        uy = dy / length
        
        new_vertices = []
        for v in surface.vertices:
            # Vector from axis point to vertex
            px = v.x - x1
            py = v.y - y1
            
            # Project onto axis
            proj = px * ux + py * uy
            
            # Perpendicular component
            perp_x = px - proj * ux
            perp_y = py - proj * uy
            
            # Mirror (reverse perpendicular)
            new_vertices.append(Point3D(
                x=x1 + proj * ux - perp_x,
                y=y1 + proj * uy - perp_y,
                z=v.z
            ))
        
        return TINSurface(
            name=f"{surface.name}_mirrored",
            vertices=new_vertices,
            triangles=list(surface.triangles),
            surface_type=surface.surface_type,
            seam_name=surface.seam_name
        )
    
    # =========================================================================
    # REFINEMENT OPERATIONS
    # =========================================================================
    
    def smooth_surface(
        self,
        surface: TINSurface,
        iterations: int = 1,
        factor: float = 0.5
    ) -> TINSurface:
        """
        Smooth a surface using Laplacian smoothing.
        
        Args:
            surface: Surface to smooth
            iterations: Number of smoothing passes
            factor: Smoothing factor (0-1)
            
        Returns:
            New smoothed TINSurface
        """
        # Build adjacency list
        adjacency = defaultdict(set)
        for tri in surface.triangles:
            adjacency[tri.i].add(tri.j)
            adjacency[tri.i].add(tri.k)
            adjacency[tri.j].add(tri.i)
            adjacency[tri.j].add(tri.k)
            adjacency[tri.k].add(tri.i)
            adjacency[tri.k].add(tri.j)
        
        # Current vertex positions
        vertices = [(v.x, v.y, v.z) for v in surface.vertices]
        
        for _ in range(iterations):
            new_vertices = []
            
            for i, v in enumerate(vertices):
                neighbors = adjacency.get(i, set())
                
                if not neighbors:
                    new_vertices.append(v)
                    continue
                
                # Average of neighbors
                avg_x = sum(vertices[n][0] for n in neighbors) / len(neighbors)
                avg_y = sum(vertices[n][1] for n in neighbors) / len(neighbors)
                avg_z = sum(vertices[n][2] for n in neighbors) / len(neighbors)
                
                # Blend with original
                new_vertices.append((
                    v[0] + factor * (avg_x - v[0]),
                    v[1] + factor * (avg_y - v[1]),
                    v[2] + factor * (avg_z - v[2])
                ))
            
            vertices = new_vertices
        
        return TINSurface(
            name=f"{surface.name}_smoothed",
            vertices=[Point3D(x=v[0], y=v[1], z=v[2]) for v in vertices],
            triangles=list(surface.triangles),
            surface_type=surface.surface_type,
            seam_name=surface.seam_name
        )
    
    def simplify_surface(
        self,
        surface: TINSurface,
        target_vertex_count: int
    ) -> TINSurface:
        """
        Simplify a surface by reducing vertex count.
        
        Uses grid-based resampling and re-triangulation.
        
        Args:
            surface: Surface to simplify
            target_vertex_count: Target number of vertices
            
        Returns:
            Simplified TINSurface
        """
        if not SCIPY_AVAILABLE:
            raise ImportError("scipy required for surface simplification")
        
        current_count = len(surface.vertices)
        if target_vertex_count >= current_count:
            return surface
        
        # Calculate grid spacing based on extent and target count
        min_pt, max_pt = surface.get_extent()
        width = max_pt.x - min_pt.x
        height = max_pt.y - min_pt.y
        
        if width == 0 or height == 0:
            return surface
        
        # Estimate grid size
        area = width * height
        cell_area = area / target_vertex_count
        grid_spacing = math.sqrt(cell_area)
        
        # Create regular grid
        nx = max(3, int(width / grid_spacing) + 1)
        ny = max(3, int(height / grid_spacing) + 1)
        
        grid_points = []
        for i in range(nx):
            for j in range(ny):
                x = min_pt.x + i * (width / (nx - 1))
                y = min_pt.y + j * (height / (ny - 1))
                z = self._base_service.query_elevation(surface, x, y)
                if z is not None:
                    grid_points.append((x, y, z))
        
        if len(grid_points) < 3:
            return surface
        
        # Re-triangulate
        return self._base_service.create_tin_from_points(
            grid_points,
            name=f"{surface.name}_simplified",
            surface_type=surface.surface_type
        )
    
    def densify_surface(
        self,
        surface: TINSurface,
        max_triangle_area: float
    ) -> TINSurface:
        """
        Densify a surface by adding vertices to large triangles.
        
        Args:
            surface: Surface to densify
            max_triangle_area: Maximum allowed triangle area
            
        Returns:
            Densified TINSurface
        """
        # Collect all points plus centroids of large triangles
        all_points = [(v.x, v.y, v.z) for v in surface.vertices]
        
        for tri in surface.triangles:
            v0 = surface.vertices[tri.i]
            v1 = surface.vertices[tri.j]
            v2 = surface.vertices[tri.k]
            
            # Calculate triangle area
            area = self._base_service._triangle_area_3d(
                v0.x, v0.y, v0.z,
                v1.x, v1.y, v1.z,
                v2.x, v2.y, v2.z
            )
            
            if area > max_triangle_area:
                # Add centroid
                cx = (v0.x + v1.x + v2.x) / 3
                cy = (v0.y + v1.y + v2.y) / 3
                cz = (v0.z + v1.z + v2.z) / 3
                all_points.append((cx, cy, cz))
        
        # Re-triangulate
        return self._base_service.create_tin_from_points(
            all_points,
            name=f"{surface.name}_densified",
            surface_type=surface.surface_type
        )
    
    def resample_to_grid(
        self,
        surface: TINSurface,
        grid_spacing: float
    ) -> TINSurface:
        """
        Resample a surface to a regular grid.
        
        Args:
            surface: Surface to resample
            grid_spacing: Grid cell size
            
        Returns:
            Resampled TINSurface
        """
        min_pt, max_pt = surface.get_extent()
        
        nx = int((max_pt.x - min_pt.x) / grid_spacing) + 1
        ny = int((max_pt.y - min_pt.y) / grid_spacing) + 1
        
        grid_points = []
        for i in range(nx):
            for j in range(ny):
                x = min_pt.x + i * grid_spacing
                y = min_pt.y + j * grid_spacing
                z = self._base_service.query_elevation(surface, x, y)
                if z is not None:
                    grid_points.append((x, y, z))
        
        if len(grid_points) < 3:
            raise ValueError("Not enough grid points for triangulation")
        
        return self._base_service.create_tin_from_points(
            grid_points,
            name=f"{surface.name}_resampled",
            surface_type=surface.surface_type
        )
    
    # =========================================================================
    # ANALYSIS OPERATIONS
    # =========================================================================
    
    def calculate_slope_at_point(
        self,
        surface: TINSurface,
        x: float,
        y: float
    ) -> Optional[SlopeResult]:
        """
        Calculate slope and aspect at a specific point.
        
        Args:
            surface: Surface to analyze
            x, y: Query point
            
        Returns:
            SlopeResult or None if outside surface
        """
        # Find containing triangle
        for tri in surface.triangles:
            v0 = surface.vertices[tri.i]
            v1 = surface.vertices[tri.j]
            v2 = surface.vertices[tri.k]
            
            if self._point_in_triangle_2d(x, y, v0, v1, v2):
                # Calculate plane normal
                normal = self._calculate_triangle_normal(v0, v1, v2)
                
                if normal is None:
                    continue
                
                nx, ny, nz = normal
                
                # Slope in degrees (angle from horizontal)
                slope_rad = math.acos(abs(nz))
                slope_deg = math.degrees(slope_rad)
                slope_pct = math.tan(slope_rad) * 100
                
                # Aspect (direction of steepest descent)
                if abs(nx) < 1e-10 and abs(ny) < 1e-10:
                    aspect = 0  # Flat surface
                else:
                    aspect = math.degrees(math.atan2(-nx, -ny))
                    if aspect < 0:
                        aspect += 360
                
                return SlopeResult(
                    slope_degrees=slope_deg,
                    slope_percent=slope_pct,
                    aspect_degrees=aspect
                )
        
        return None
    
    def calculate_slope_map(
        self,
        surface: TINSurface,
        grid_spacing: float = 10.0
    ) -> SlopeMap:
        """
        Calculate slope and aspect for entire surface as a grid.
        
        Args:
            surface: Surface to analyze
            grid_spacing: Grid spacing for sampling
            
        Returns:
            SlopeMap with slope and aspect grids
        """
        min_pt, max_pt = surface.get_extent()
        
        nx = int((max_pt.x - min_pt.x) / grid_spacing) + 1
        ny = int((max_pt.y - min_pt.y) / grid_spacing) + 1
        
        slopes = []
        aspects = []
        
        for j in range(ny):
            slope_row = []
            aspect_row = []
            for i in range(nx):
                x = min_pt.x + i * grid_spacing
                y = min_pt.y + j * grid_spacing
                
                result = self.calculate_slope_at_point(surface, x, y)
                
                if result:
                    slope_row.append(result.slope_degrees)
                    aspect_row.append(result.aspect_degrees)
                else:
                    slope_row.append(float('nan'))
                    aspect_row.append(float('nan'))
            
            slopes.append(slope_row)
            aspects.append(aspect_row)
        
        return SlopeMap(
            grid_spacing=grid_spacing,
            origin=(min_pt.x, min_pt.y),
            rows=ny,
            cols=nx,
            slopes=slopes,
            aspects=aspects
        )
    
    def generate_profile(
        self,
        surface: TINSurface,
        start: Tuple[float, float],
        end: Tuple[float, float],
        interval: float = 5.0
    ) -> SurfaceProfile:
        """
        Generate an elevation profile along a line.
        
        Args:
            surface: Surface to sample
            start: Start point (x, y)
            end: End point (x, y)
            interval: Sampling interval
            
        Returns:
            SurfaceProfile with sampled points
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        total_dist = math.sqrt(dx*dx + dy*dy)
        
        if total_dist < 0.001:
            return SurfaceProfile(
                points=[],
                total_distance=0,
                min_elevation=0,
                max_elevation=0,
                avg_elevation=0
            )
        
        # Unit direction
        ux = dx / total_dist
        uy = dy / total_dist
        
        points = []
        distance = 0.0
        
        while distance <= total_dist:
            x = start[0] + distance * ux
            y = start[1] + distance * uy
            z = self._base_service.query_elevation(surface, x, y)
            
            if z is not None:
                points.append(ProfilePoint(
                    distance=distance,
                    x=x,
                    y=y,
                    z=z
                ))
            
            distance += interval
        
        # Calculate slopes between adjacent points
        for i in range(len(points) - 1):
            horiz = points[i+1].distance - points[i].distance
            vert = points[i+1].z - points[i].z
            if horiz > 0:
                points[i].slope_to_next = math.degrees(math.atan2(vert, horiz))
        
        if not points:
            return SurfaceProfile(
                points=[],
                total_distance=total_dist,
                min_elevation=0,
                max_elevation=0,
                avg_elevation=0
            )
        
        elevations = [p.z for p in points]
        
        return SurfaceProfile(
            points=points,
            total_distance=total_dist,
            min_elevation=min(elevations),
            max_elevation=max(elevations),
            avg_elevation=sum(elevations) / len(elevations)
        )
    
    def calculate_isopach(
        self,
        upper_surface: TINSurface,
        lower_surface: TINSurface,
        grid_spacing: float = 10.0
    ) -> IsopachResult:
        """
        Calculate thickness (isopach) map between two surfaces.
        
        Args:
            upper_surface: Upper surface (e.g., seam roof)
            lower_surface: Lower surface (e.g., seam floor)
            grid_spacing: Grid spacing
            
        Returns:
            IsopachResult with thickness grid
        """
        # Get overlapping extent
        upper_min, upper_max = upper_surface.get_extent()
        lower_min, lower_max = lower_surface.get_extent()
        
        min_x = max(upper_min.x, lower_min.x)
        max_x = min(upper_max.x, lower_max.x)
        min_y = max(upper_min.y, lower_min.y)
        max_y = min(upper_max.y, lower_max.y)
        
        if min_x >= max_x or min_y >= max_y:
            raise ValueError("Surfaces do not overlap")
        
        nx = int((max_x - min_x) / grid_spacing) + 1
        ny = int((max_y - min_y) / grid_spacing) + 1
        
        thickness_grid = []
        thicknesses = []
        
        for j in range(ny):
            row = []
            for i in range(nx):
                x = min_x + i * grid_spacing
                y = min_y + j * grid_spacing
                
                z_upper = self._base_service.query_elevation(upper_surface, x, y)
                z_lower = self._base_service.query_elevation(lower_surface, x, y)
                
                if z_upper is not None and z_lower is not None:
                    t = z_upper - z_lower
                    row.append(t)
                    thicknesses.append(t)
                else:
                    row.append(float('nan'))
            
            thickness_grid.append(row)
        
        if not thicknesses:
            raise ValueError("No overlapping valid points")
        
        return IsopachResult(
            grid_spacing=grid_spacing,
            origin=(min_x, min_y),
            rows=ny,
            cols=nx,
            thickness=thickness_grid,
            min_thickness=min(thicknesses),
            max_thickness=max(thicknesses),
            avg_thickness=sum(thicknesses) / len(thicknesses)
        )
    
    # =========================================================================
    # INTERPOLATION OPERATIONS
    # =========================================================================
    
    def drape_points(
        self,
        surface: TINSurface,
        points: List[Tuple[float, float]]
    ) -> List[Tuple[float, float, float]]:
        """
        Project XY points onto a surface (drape).
        
        Args:
            surface: Surface to drape onto
            points: List of (x, y) points
            
        Returns:
            List of (x, y, z) points with surface elevation
        """
        result = []
        for x, y in points:
            z = self._base_service.query_elevation(surface, x, y)
            if z is not None:
                result.append((x, y, z))
        return result
    
    def drape_polyline(
        self,
        surface: TINSurface,
        vertices: List[Tuple[float, float]]
    ) -> List[Tuple[float, float, float]]:
        """
        Project a polyline onto a surface.
        
        Args:
            surface: Surface to drape onto
            vertices: Polyline vertices as [(x, y), ...]
            
        Returns:
            List of (x, y, z) vertices with interpolated elevations
        """
        return self.drape_points(surface, vertices)
    
    def sample_along_line(
        self,
        surface: TINSurface,
        start: Tuple[float, float],
        end: Tuple[float, float],
        interval: float
    ) -> List[Tuple[float, float, float]]:
        """
        Sample elevations along a line at regular intervals.
        
        Args:
            surface: Surface to sample
            start: Start point (x, y)
            end: End point (x, y)
            interval: Sampling interval
            
        Returns:
            List of (x, y, z) sample points
        """
        profile = self.generate_profile(surface, start, end, interval)
        return [(p.x, p.y, p.z) for p in profile.points]
    
    def sample_at_points(
        self,
        surface: TINSurface,
        points: List[Tuple[float, float]]
    ) -> List[Optional[float]]:
        """
        Sample surface elevation at multiple XY points.
        
        Args:
            surface: Surface to sample
            points: List of (x, y) query points
            
        Returns:
            List of elevations (None where outside surface)
        """
        return [
            self._base_service.query_elevation(surface, x, y)
            for x, y in points
        ]
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _point_in_polygon(
        self,
        x: float,
        y: float,
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
    
    def _point_in_triangle_2d(
        self,
        x: float,
        y: float,
        v0: Point3D,
        v1: Point3D,
        v2: Point3D
    ) -> bool:
        """Check if point is inside triangle in 2D."""
        return self._base_service._point_in_triangle(
            x, y, v0.x, v0.y, v1.x, v1.y, v2.x, v2.y
        )
    
    def _calculate_triangle_normal(
        self,
        v0: Point3D,
        v1: Point3D,
        v2: Point3D
    ) -> Optional[Tuple[float, float, float]]:
        """Calculate unit normal vector for a triangle."""
        # Vectors
        ax, ay, az = v1.x - v0.x, v1.y - v0.y, v1.z - v0.z
        bx, by, bz = v2.x - v0.x, v2.y - v0.y, v2.z - v0.z
        
        # Cross product
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        
        # Normalize
        length = math.sqrt(nx*nx + ny*ny + nz*nz)
        
        if length < 1e-10:
            return None
        
        return (nx / length, ny / length, nz / length)


# =============================================================================
# Factory Function
# =============================================================================

def get_surface_tools_service(
    base_service: Optional[SurfaceService] = None
) -> SurfaceToolsService:
    """Get surface tools service instance."""
    return SurfaceToolsService(base_service)
