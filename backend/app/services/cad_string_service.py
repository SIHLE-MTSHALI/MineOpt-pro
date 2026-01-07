"""
CAD String Service - Phase 2

Comprehensive service for CAD string (polyline) operations.
Supports all mining string types with geometry operations.

Features:
- CRUD operations for strings
- Vertex manipulation (insert, delete, move)
- String operations (split, merge, reverse, offset)
- Analysis (length, area, gradient, intersections)
- Surface projection
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Union
from enum import Enum
import math
import uuid
import datetime
import logging

from sqlalchemy.orm import Session

try:
    from shapely.geometry import LineString, Polygon, Point
    from shapely.ops import split, nearest_points
    from shapely import buffer, simplify
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

from ..domain.models_surface import CADString, StringType


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Vertex:
    """A 3D vertex point."""
    x: float
    y: float
    z: float
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
    
    def distance_to(self, other: 'Vertex') -> float:
        """Calculate 3D distance to another vertex."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def distance_2d_to(self, other: 'Vertex') -> float:
        """Calculate 2D (XY) distance to another vertex."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx*dx + dy*dy)


@dataclass
class StringGeometry:
    """Geometry of a CAD string."""
    vertices: List[Tuple[float, float, float]]
    is_closed: bool
    
    @property
    def length_3d(self) -> float:
        """Calculate 3D polyline length."""
        if len(self.vertices) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(self.vertices) - 1):
            dx = self.vertices[i+1][0] - self.vertices[i][0]
            dy = self.vertices[i+1][1] - self.vertices[i][1]
            dz = self.vertices[i+1][2] - self.vertices[i][2]
            total += math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if self.is_closed and len(self.vertices) > 2:
            dx = self.vertices[0][0] - self.vertices[-1][0]
            dy = self.vertices[0][1] - self.vertices[-1][1]
            dz = self.vertices[0][2] - self.vertices[-1][2]
            total += math.sqrt(dx*dx + dy*dy + dz*dz)
        
        return total
    
    @property
    def length_2d(self) -> float:
        """Calculate 2D (XY) polyline length."""
        if len(self.vertices) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(self.vertices) - 1):
            dx = self.vertices[i+1][0] - self.vertices[i][0]
            dy = self.vertices[i+1][1] - self.vertices[i][1]
            total += math.sqrt(dx*dx + dy*dy)
        
        if self.is_closed and len(self.vertices) > 2:
            dx = self.vertices[0][0] - self.vertices[-1][0]
            dy = self.vertices[0][1] - self.vertices[-1][1]
            total += math.sqrt(dx*dx + dy*dy)
        
        return total
    
    @property
    def area(self) -> Optional[float]:
        """Calculate area if closed polygon (2D, using shoelace formula)."""
        if not self.is_closed or len(self.vertices) < 3:
            return None
        
        n = len(self.vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i][0] * self.vertices[j][1]
            area -= self.vertices[j][0] * self.vertices[i][1]
        
        return abs(area) / 2.0


@dataclass
class GradientInfo:
    """Gradient information for a string."""
    min_gradient: float  # As percentage
    max_gradient: float
    avg_gradient: float
    segment_gradients: List[float]  # Gradient per segment


@dataclass
class IntersectionPoint:
    """Point where two strings intersect."""
    x: float
    y: float
    z: Optional[float]
    segment_index_1: int
    segment_index_2: int


# =============================================================================
# CAD String Service
# =============================================================================

class CADStringService:
    """
    Service for managing CAD strings (polylines).
    
    Provides comprehensive operations for mining CAD data:
    - CRUD operations
    - Geometry manipulation
    - Analysis and measurements
    - Surface projection
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # CRUD Operations
    # =========================================================================
    
    def create_string(
        self,
        site_id: str,
        name: str,
        vertices: List[Tuple[float, float, float]],
        string_type: str = "custom",
        is_closed: bool = False,
        layer: str = "DEFAULT",
        description: str = None,
        color: str = None,
        line_weight: float = 1.0,
        elevation: float = None,
        surface_id: str = None
    ) -> CADString:
        """
        Create a new CAD string.
        
        Args:
            site_id: Site identifier
            name: String name
            vertices: List of (x, y, z) tuples
            string_type: Type from StringType enum
            is_closed: Whether polyline is closed
            layer: CAD layer name
            description: Optional description
            color: Hex color code
            line_weight: Line width
            elevation: For contour strings
            surface_id: Associated surface
            
        Returns:
            Created CADString object
        """
        if len(vertices) < 2:
            raise ValueError("At least 2 vertices required")
        
        string = CADString(
            string_id=str(uuid.uuid4()),
            site_id=site_id,
            name=name,
            description=description,
            layer=layer,
            string_type=string_type,
            vertex_data=[list(v) for v in vertices],
            is_closed=is_closed,
            surface_id=surface_id,
            elevation=elevation,
            color=color,
            line_weight=line_weight,
            created_at=datetime.datetime.utcnow()
        )
        
        self.db.add(string)
        self.db.commit()
        self.db.refresh(string)
        
        self.logger.info(f"Created CAD string: {name} ({string_type})")
        return string
    
    def get_string(self, string_id: str) -> Optional[CADString]:
        """Get a CAD string by ID."""
        return self.db.query(CADString).filter(
            CADString.string_id == string_id
        ).first()
    
    def list_strings(
        self,
        site_id: str,
        string_type: str = None,
        layer: str = None,
        surface_id: str = None
    ) -> List[CADString]:
        """
        List CAD strings with optional filters.
        
        Args:
            site_id: Site identifier
            string_type: Filter by string type
            layer: Filter by layer
            surface_id: Filter by associated surface
            
        Returns:
            List of matching CADString objects
        """
        query = self.db.query(CADString).filter(CADString.site_id == site_id)
        
        if string_type:
            query = query.filter(CADString.string_type == string_type)
        if layer:
            query = query.filter(CADString.layer == layer)
        if surface_id:
            query = query.filter(CADString.surface_id == surface_id)
        
        return query.order_by(CADString.name).all()
    
    def update_string(
        self,
        string_id: str,
        **kwargs
    ) -> Optional[CADString]:
        """
        Update a CAD string's properties.
        
        Allowed kwargs: name, description, layer, string_type, is_closed,
                        color, line_weight, elevation, surface_id
        """
        string = self.get_string(string_id)
        if not string:
            return None
        
        allowed = {'name', 'description', 'layer', 'string_type', 'is_closed',
                   'color', 'line_weight', 'elevation', 'surface_id'}
        
        for key, value in kwargs.items():
            if key in allowed:
                setattr(string, key, value)
        
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        self.db.refresh(string)
        
        return string
    
    def delete_string(self, string_id: str) -> bool:
        """Delete a CAD string."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        self.db.delete(string)
        self.db.commit()
        return True
    
    # =========================================================================
    # Vertex Operations
    # =========================================================================
    
    def get_vertices(self, string_id: str) -> List[Tuple[float, float, float]]:
        """Get vertices of a string."""
        string = self.get_string(string_id)
        if not string:
            return []
        return string.vertices
    
    def set_vertices(
        self,
        string_id: str,
        vertices: List[Tuple[float, float, float]]
    ) -> bool:
        """Replace all vertices of a string."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        if len(vertices) < 2:
            raise ValueError("At least 2 vertices required")
        
        string.vertex_data = [list(v) for v in vertices]
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        return True
    
    def insert_vertex(
        self,
        string_id: str,
        index: int,
        x: float,
        y: float,
        z: float
    ) -> bool:
        """Insert a vertex at the specified index."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = list(string.vertex_data or [])
        if index < 0 or index > len(vertices):
            raise ValueError(f"Index {index} out of range")
        
        vertices.insert(index, [x, y, z])
        string.vertex_data = vertices
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        return True
    
    def delete_vertex(self, string_id: str, index: int) -> bool:
        """Delete a vertex at the specified index."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = list(string.vertex_data or [])
        if index < 0 or index >= len(vertices):
            raise ValueError(f"Index {index} out of range")
        
        if len(vertices) <= 2:
            raise ValueError("Cannot delete: minimum 2 vertices required")
        
        del vertices[index]
        string.vertex_data = vertices
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        return True
    
    def move_vertex(
        self,
        string_id: str,
        index: int,
        x: float,
        y: float,
        z: float
    ) -> bool:
        """Move a vertex to a new position."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = list(string.vertex_data or [])
        if index < 0 or index >= len(vertices):
            raise ValueError(f"Index {index} out of range")
        
        vertices[index] = [x, y, z]
        string.vertex_data = vertices
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        return True
    
    # =========================================================================
    # Geometry Operations
    # =========================================================================
    
    def split_string(
        self,
        string_id: str,
        vertex_index: int
    ) -> Tuple[Optional[CADString], Optional[CADString]]:
        """
        Split a string at the specified vertex index.
        
        Returns two new strings, original is deleted.
        """
        string = self.get_string(string_id)
        if not string:
            return None, None
        
        vertices = string.vertices
        if vertex_index <= 0 or vertex_index >= len(vertices) - 1:
            raise ValueError("Split index must be between first and last vertex")
        
        # Create two new strings
        verts1 = vertices[:vertex_index + 1]
        verts2 = vertices[vertex_index:]
        
        string1 = self.create_string(
            site_id=string.site_id,
            name=f"{string.name}_part1",
            vertices=verts1,
            string_type=string.string_type,
            is_closed=False,
            layer=string.layer,
            color=string.color,
            line_weight=string.line_weight
        )
        
        string2 = self.create_string(
            site_id=string.site_id,
            name=f"{string.name}_part2",
            vertices=verts2,
            string_type=string.string_type,
            is_closed=False,
            layer=string.layer,
            color=string.color,
            line_weight=string.line_weight
        )
        
        # Delete original
        self.delete_string(string_id)
        
        self.logger.info(f"Split string {string.name} at vertex {vertex_index}")
        return string1, string2
    
    def merge_strings(
        self,
        string_id_1: str,
        string_id_2: str,
        new_name: str = None
    ) -> Optional[CADString]:
        """
        Merge two strings into one.
        
        Connects end of first string to start of second string.
        Original strings are deleted.
        """
        string1 = self.get_string(string_id_1)
        string2 = self.get_string(string_id_2)
        
        if not string1 or not string2:
            return None
        
        if string1.site_id != string2.site_id:
            raise ValueError("Strings must belong to the same site")
        
        # Combine vertices (skip duplicate if endpoints match)
        verts1 = string1.vertices
        verts2 = string2.vertices
        
        # Check if end of string1 matches start of string2
        if verts1 and verts2:
            last = verts1[-1]
            first = verts2[0]
            dist = math.sqrt(
                (last[0] - first[0])**2 +
                (last[1] - first[1])**2 +
                (last[2] - first[2])**2
            )
            if dist < 0.001:  # Very close, skip duplicate
                combined = list(verts1) + list(verts2[1:])
            else:
                combined = list(verts1) + list(verts2)
        else:
            combined = list(verts1) + list(verts2)
        
        merged = self.create_string(
            site_id=string1.site_id,
            name=new_name or f"{string1.name}_{string2.name}_merged",
            vertices=combined,
            string_type=string1.string_type,
            is_closed=False,
            layer=string1.layer,
            color=string1.color,
            line_weight=string1.line_weight
        )
        
        # Delete originals
        self.delete_string(string_id_1)
        self.delete_string(string_id_2)
        
        self.logger.info(f"Merged strings {string1.name} and {string2.name}")
        return merged
    
    def reverse_string(self, string_id: str) -> bool:
        """Reverse the direction of a string."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = list(string.vertex_data or [])
        vertices.reverse()
        string.vertex_data = vertices
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        
        self.logger.info(f"Reversed string {string.name}")
        return True
    
    def close_string(self, string_id: str) -> bool:
        """Close an open string (connect last vertex to first)."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        if string.is_closed:
            return True  # Already closed
        
        string.is_closed = True
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        return True
    
    def open_string(self, string_id: str) -> bool:
        """Open a closed string (break the closure)."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        string.is_closed = False
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        return True
    
    # =========================================================================
    # Advanced Operations
    # =========================================================================
    
    def offset_string(
        self,
        string_id: str,
        distance: float,
        side: str = "left"  # "left" or "right"
    ) -> Optional[CADString]:
        """
        Create an offset (parallel) string.
        
        Args:
            string_id: Source string ID
            distance: Offset distance in coordinate units
            side: "left" or "right" relative to string direction
            
        Returns:
            New offset CADString
        """
        if not SHAPELY_AVAILABLE:
            raise ImportError("Shapely required for offset operations")
        
        string = self.get_string(string_id)
        if not string:
            return None
        
        vertices = string.vertices
        if len(vertices) < 2:
            return None
        
        # Create 2D linestring for buffering
        coords_2d = [(v[0], v[1]) for v in vertices]
        line = LineString(coords_2d)
        
        # Use single-side offset
        if side == "right":
            distance = -distance
        
        try:
            offset_line = line.parallel_offset(distance, 'left', join_style=2)
            
            if offset_line.is_empty:
                return None
            
            # Extract coordinates and add Z values
            offset_coords = list(offset_line.coords)
            
            # Interpolate Z values from original
            new_vertices = []
            for ox, oy in offset_coords:
                # Find nearest original point for Z
                min_dist = float('inf')
                nearest_z = 0.0
                for vx, vy, vz in vertices:
                    d = math.sqrt((ox - vx)**2 + (oy - vy)**2)
                    if d < min_dist:
                        min_dist = d
                        nearest_z = vz
                new_vertices.append((ox, oy, nearest_z))
            
            # Create new string
            return self.create_string(
                site_id=string.site_id,
                name=f"{string.name}_offset_{distance}m",
                vertices=new_vertices,
                string_type=string.string_type,
                is_closed=string.is_closed,
                layer=string.layer,
                color=string.color,
                line_weight=string.line_weight
            )
        except Exception as e:
            self.logger.error(f"Offset failed: {e}")
            return None
    
    def smooth_string(
        self,
        string_id: str,
        factor: float = 0.5
    ) -> bool:
        """
        Smooth string vertices using Chaikin's algorithm.
        
        Args:
            string_id: String to smooth
            factor: Smoothing factor (0.0 = no change, 1.0 = maximum)
            
        Returns:
            Success status
        """
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = string.vertices
        if len(vertices) < 3:
            return False
        
        # Chaikin's corner cutting algorithm
        iterations = max(1, int(factor * 3))
        
        for _ in range(iterations):
            new_vertices = []
            n = len(vertices)
            
            for i in range(n - 1):
                p1 = vertices[i]
                p2 = vertices[i + 1]
                
                # Create two new points at 1/4 and 3/4 positions
                q = (
                    0.75 * p1[0] + 0.25 * p2[0],
                    0.75 * p1[1] + 0.25 * p2[1],
                    0.75 * p1[2] + 0.25 * p2[2]
                )
                r = (
                    0.25 * p1[0] + 0.75 * p2[0],
                    0.25 * p1[1] + 0.75 * p2[1],
                    0.25 * p1[2] + 0.75 * p2[2]
                )
                new_vertices.extend([q, r])
            
            if string.is_closed:
                # Connect back to start
                p1 = vertices[-1]
                p2 = vertices[0]
                q = (
                    0.75 * p1[0] + 0.25 * p2[0],
                    0.75 * p1[1] + 0.25 * p2[1],
                    0.75 * p1[2] + 0.25 * p2[2]
                )
                r = (
                    0.25 * p1[0] + 0.75 * p2[0],
                    0.25 * p1[1] + 0.75 * p2[1],
                    0.25 * p1[2] + 0.75 * p2[2]
                )
                new_vertices.extend([q, r])
            
            vertices = new_vertices
        
        string.vertex_data = [list(v) for v in vertices]
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        
        self.logger.info(f"Smoothed string {string.name} with factor {factor}")
        return True
    
    def simplify_string(
        self,
        string_id: str,
        tolerance: float = 1.0
    ) -> bool:
        """
        Simplify string using Douglas-Peucker algorithm.
        
        Args:
            string_id: String to simplify
            tolerance: Maximum deviation from original line
            
        Returns:
            Success status
        """
        if not SHAPELY_AVAILABLE:
            raise ImportError("Shapely required for simplify operations")
        
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = string.vertices
        if len(vertices) < 3:
            return False
        
        # Create 2D linestring
        coords_2d = [(v[0], v[1]) for v in vertices]
        original_z = {(v[0], v[1]): v[2] for v in vertices}
        
        line = LineString(coords_2d)
        simplified = simplify(line, tolerance)
        
        # Extract simplified coordinates and restore Z
        new_vertices = []
        for x, y in simplified.coords:
            # Find nearest original Z
            min_dist = float('inf')
            nearest_z = 0.0
            for ox, oy, oz in vertices:
                d = (x - ox)**2 + (y - oy)**2
                if d < min_dist:
                    min_dist = d
                    nearest_z = oz
            new_vertices.append((x, y, nearest_z))
        
        if len(new_vertices) >= 2:
            string.vertex_data = [list(v) for v in new_vertices]
            string.updated_at = datetime.datetime.utcnow()
            self.db.commit()
            
            self.logger.info(f"Simplified string {string.name}: {len(vertices)} -> {len(new_vertices)} vertices")
            return True
        
        return False
    
    def densify_string(
        self,
        string_id: str,
        max_segment_length: float
    ) -> bool:
        """
        Add vertices to ensure no segment exceeds max length.
        
        Args:
            string_id: String to densify
            max_segment_length: Maximum distance between vertices
            
        Returns:
            Success status
        """
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = string.vertices
        if len(vertices) < 2:
            return False
        
        new_vertices = [vertices[0]]
        
        for i in range(len(vertices) - 1):
            p1 = vertices[i]
            p2 = vertices[i + 1]
            
            # Calculate segment length
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2]
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            if length > max_segment_length:
                # Add intermediate points
                n_segments = math.ceil(length / max_segment_length)
                for j in range(1, n_segments):
                    t = j / n_segments
                    new_vertices.append((
                        p1[0] + t * dx,
                        p1[1] + t * dy,
                        p1[2] + t * dz
                    ))
            
            new_vertices.append(p2)
        
        string.vertex_data = [list(v) for v in new_vertices]
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        
        self.logger.info(f"Densified string {string.name}: {len(vertices)} -> {len(new_vertices)} vertices")
        return True
    
    def project_to_elevation(
        self,
        string_id: str,
        elevation: float
    ) -> bool:
        """Set all vertices to a constant elevation."""
        string = self.get_string(string_id)
        if not string:
            return False
        
        vertices = [(v[0], v[1], elevation) for v in string.vertices]
        string.vertex_data = [list(v) for v in vertices]
        string.elevation = elevation
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        
        return True
    
    def buffer_string(
        self,
        string_id: str,
        distance: float
    ) -> Optional[CADString]:
        """
        Create a polygon buffer around a string.
        
        Returns a closed polygon string.
        """
        if not SHAPELY_AVAILABLE:
            raise ImportError("Shapely required for buffer operations")
        
        string = self.get_string(string_id)
        if not string:
            return None
        
        vertices = string.vertices
        if len(vertices) < 2:
            return None
        
        # Average Z for result
        avg_z = sum(v[2] for v in vertices) / len(vertices)
        
        # Create 2D geometry and buffer
        coords_2d = [(v[0], v[1]) for v in vertices]
        
        if string.is_closed:
            geom = Polygon(coords_2d)
        else:
            geom = LineString(coords_2d)
        
        buffered = buffer(geom, distance, cap_style=2, join_style=2)
        
        if buffered.is_empty:
            return None
        
        # Extract exterior ring
        if hasattr(buffered, 'exterior'):
            coords = list(buffered.exterior.coords)
        else:
            return None
        
        # Add Z value
        buffer_vertices = [(x, y, avg_z) for x, y in coords]
        
        return self.create_string(
            site_id=string.site_id,
            name=f"{string.name}_buffer_{distance}m",
            vertices=buffer_vertices,
            string_type="boundary",
            is_closed=True,
            layer=string.layer,
            color=string.color
        )
    
    # =========================================================================
    # Analysis Operations
    # =========================================================================
    
    def calculate_length(self, string_id: str) -> Optional[float]:
        """Calculate 3D polyline length."""
        string = self.get_string(string_id)
        if not string:
            return None
        
        geom = StringGeometry(vertices=string.vertices, is_closed=string.is_closed)
        return geom.length_3d
    
    def calculate_area(self, string_id: str) -> Optional[float]:
        """Calculate area of closed polygon."""
        string = self.get_string(string_id)
        if not string or not string.is_closed:
            return None
        
        geom = StringGeometry(vertices=string.vertices, is_closed=True)
        return geom.area
    
    def calculate_gradient(self, string_id: str) -> Optional[GradientInfo]:
        """
        Calculate gradient (slope) along string.
        
        Returns min, max, average gradients and per-segment values.
        """
        string = self.get_string(string_id)
        if not string:
            return None
        
        vertices = string.vertices
        if len(vertices) < 2:
            return None
        
        gradients = []
        
        for i in range(len(vertices) - 1):
            p1 = vertices[i]
            p2 = vertices[i + 1]
            
            # Horizontal distance
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            horiz_dist = math.sqrt(dx*dx + dy*dy)
            
            # Vertical change
            dz = p2[2] - p1[2]
            
            # Gradient as percentage
            if horiz_dist > 0.001:
                gradient = (dz / horiz_dist) * 100
            else:
                gradient = 0.0
            
            gradients.append(gradient)
        
        if not gradients:
            return None
        
        return GradientInfo(
            min_gradient=min(gradients),
            max_gradient=max(gradients),
            avg_gradient=sum(gradients) / len(gradients),
            segment_gradients=gradients
        )
    
    def find_intersections(
        self,
        string_id_1: str,
        string_id_2: str
    ) -> List[IntersectionPoint]:
        """
        Find intersection points between two strings.
        
        Returns list of intersection points in 2D (XY plane).
        """
        if not SHAPELY_AVAILABLE:
            raise ImportError("Shapely required for intersection operations")
        
        string1 = self.get_string(string_id_1)
        string2 = self.get_string(string_id_2)
        
        if not string1 or not string2:
            return []
        
        # Create 2D linestrings
        coords1 = [(v[0], v[1]) for v in string1.vertices]
        coords2 = [(v[0], v[1]) for v in string2.vertices]
        
        if string1.is_closed:
            line1 = Polygon(coords1).exterior
        else:
            line1 = LineString(coords1)
        
        if string2.is_closed:
            line2 = Polygon(coords2).exterior
        else:
            line2 = LineString(coords2)
        
        intersection = line1.intersection(line2)
        
        if intersection.is_empty:
            return []
        
        points = []
        
        if intersection.geom_type == 'Point':
            points.append(IntersectionPoint(
                x=intersection.x,
                y=intersection.y,
                z=None,
                segment_index_1=0,
                segment_index_2=0
            ))
        elif intersection.geom_type == 'MultiPoint':
            for pt in intersection.geoms:
                points.append(IntersectionPoint(
                    x=pt.x,
                    y=pt.y,
                    z=None,
                    segment_index_1=0,
                    segment_index_2=0
                ))
        
        return points
    
    def snap_to_grid(
        self,
        string_id: str,
        grid_size: float
    ) -> bool:
        """
        Snap all vertices to a regular grid.
        
        Args:
            string_id: String to snap
            grid_size: Grid cell size
            
        Returns:
            Success status
        """
        string = self.get_string(string_id)
        if not string:
            return False
        
        new_vertices = []
        for x, y, z in string.vertices:
            snapped_x = round(x / grid_size) * grid_size
            snapped_y = round(y / grid_size) * grid_size
            new_vertices.append((snapped_x, snapped_y, z))
        
        string.vertex_data = [list(v) for v in new_vertices]
        string.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        
        return True
    
    # =========================================================================
    # Import/Export
    # =========================================================================
    
    def get_string_types(self) -> List[Dict[str, str]]:
        """Get list of available string types."""
        return [
            {"value": t.value, "name": t.name.replace("_", " ").title()}
            for t in StringType
        ]
    
    def export_to_dxf_entities(
        self,
        string_id: str
    ) -> Dict[str, Any]:
        """
        Export string as DXF entity data.
        
        Returns dict ready for DXF writing.
        """
        string = self.get_string(string_id)
        if not string:
            return {}
        
        return {
            "type": "LWPOLYLINE" if not string.is_closed else "CLOSED_LWPOLYLINE",
            "layer": string.layer,
            "vertices": string.vertices,
            "is_closed": string.is_closed,
            "color": string.color,
            "lineweight": int(string.line_weight * 100)
        }


# =============================================================================
# Factory Function
# =============================================================================

def get_cad_string_service(db: Session) -> CADStringService:
    """Get CAD string service instance."""
    return CADStringService(db)
