"""
Surface Domain Models - Phase 2 TIN Surface Generation

Defines SQLAlchemy models for storing TIN surfaces and their properties.
Surfaces represent terrain, seam roofs/floors, and design surfaces.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime
from enum import Enum
from typing import List, Tuple, Optional


class SurfaceType(str, Enum):
    """Types of surfaces in mining context."""
    TERRAIN = "terrain"              # Original ground surface
    SEAM_ROOF = "seam_roof"          # Top of coal seam
    SEAM_FLOOR = "seam_floor"        # Bottom of coal seam
    PIT_DESIGN = "pit_design"        # Designed pit surface
    RAMP_DESIGN = "ramp_design"      # Haul road ramp design
    DUMP_DESIGN = "dump_design"      # Waste dump design
    STOCKPILE = "stockpile"          # Stockpile surface
    INTERBURDEN = "interburden"      # Between seams
    CUSTOM = "custom"                # User-defined


class Surface(Base):
    """
    A TIN (Triangulated Irregular Network) surface.
    
    Stores the geometry as JSON for flexibility and database portability.
    Supports terrain, seam surfaces, and design surfaces.
    """
    __tablename__ = "surfaces"
    
    surface_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Surface metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    surface_type = Column(String, default=SurfaceType.TERRAIN.value)
    seam_name = Column(String, nullable=True)  # For seam surfaces
    
    # Geometry stored as JSON
    # vertices: [[x, y, z], [x, y, z], ...]
    vertex_data = Column(JSON, nullable=False, default=list)
    # triangles: [[i, j, k], [i, j, k], ...]
    triangle_data = Column(JSON, nullable=False, default=list)
    
    # Computed statistics
    vertex_count = Column(Integer, default=0)
    triangle_count = Column(Integer, default=0)
    area_m2 = Column(Float, nullable=True)
    
    # Extents
    min_x = Column(Float, nullable=True)
    min_y = Column(Float, nullable=True)
    min_z = Column(Float, nullable=True)
    max_x = Column(Float, nullable=True)
    max_y = Column(Float, nullable=True)
    max_z = Column(Float, nullable=True)
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    source_type = Column(String, nullable=True)  # 'boreholes', 'dxf', 'xyz', 'manual'
    source_reference = Column(String, nullable=True)  # Reference to source data
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    
    # Relationships
    site = relationship("Site")
    properties = relationship("SurfaceProperty", back_populates="surface", 
                             cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Surface {self.name} ({self.surface_type})>"
    
    @property
    def vertices(self) -> List[Tuple[float, float, float]]:
        """Get vertices as list of tuples."""
        return [tuple(v) for v in (self.vertex_data or [])]
    
    @property
    def triangles(self) -> List[Tuple[int, int, int]]:
        """Get triangles as list of tuples."""
        return [tuple(t) for t in (self.triangle_data or [])]
    
    def set_geometry(
        self, 
        vertices: List[Tuple[float, float, float]], 
        triangles: List[Tuple[int, int, int]]
    ):
        """Set surface geometry and compute statistics."""
        self.vertex_data = [list(v) for v in vertices]
        self.triangle_data = [list(t) for t in triangles]
        self.vertex_count = len(vertices)
        self.triangle_count = len(triangles)
        
        # Calculate extents
        if vertices:
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
            zs = [v[2] for v in vertices]
            self.min_x = min(xs)
            self.max_x = max(xs)
            self.min_y = min(ys)
            self.max_y = max(ys)
            self.min_z = min(zs)
            self.max_z = max(zs)
        
        self.updated_at = datetime.datetime.utcnow()


class SurfaceProperty(Base):
    """
    Additional properties/attributes for a surface.
    
    Stores computed or user-defined properties like volume, tonnage, average elevation, etc.
    """
    __tablename__ = "surface_properties"
    
    property_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    surface_id = Column(String, ForeignKey("surfaces.surface_id"), nullable=False)
    
    property_name = Column(String, nullable=False)
    property_value = Column(Float, nullable=True)
    property_text = Column(String, nullable=True)  # For non-numeric values
    property_unit = Column(String, nullable=True)  # e.g., "m3", "tonnes"
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    surface = relationship("Surface", back_populates="properties")
    
    def __repr__(self):
        return f"<SurfaceProperty {self.property_name}={self.property_value}>"


class CADString(Base):
    """
    A CAD string (polyline) for mining design.
    
    Represents boundaries, roads, contours, and other line features.
    """
    __tablename__ = "cad_strings"
    
    string_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    layer = Column(String, default="DEFAULT")
    string_type = Column(String, default="boundary")  # boundary, road, contour, design
    
    # Geometry as JSON: [[x, y, z], [x, y, z], ...]
    vertex_data = Column(JSON, nullable=False, default=list)
    is_closed = Column(Boolean, default=False)
    
    # Associated surface (if any)
    surface_id = Column(String, ForeignKey("surfaces.surface_id"), nullable=True)
    elevation = Column(Float, nullable=True)  # For contours
    
    # Display properties
    color = Column(String, nullable=True)  # Hex color
    line_weight = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("Site")
    surface = relationship("Surface")
    
    def __repr__(self):
        return f"<CADString {self.name} ({self.string_type})>"
    
    @property
    def vertices(self) -> List[Tuple[float, float, float]]:
        """Get vertices as list of tuples."""
        return [tuple(v) for v in (self.vertex_data or [])]
    
    @property
    def length(self) -> float:
        """Calculate polyline length."""
        total = 0.0
        verts = self.vertices
        for i in range(len(verts) - 1):
            dx = verts[i+1][0] - verts[i][0]
            dy = verts[i+1][1] - verts[i][1]
            dz = verts[i+1][2] - verts[i][2]
            total += (dx*dx + dy*dy + dz*dz) ** 0.5
        if self.is_closed and len(verts) > 2:
            dx = verts[0][0] - verts[-1][0]
            dy = verts[0][1] - verts[-1][1]
            dz = verts[0][2] - verts[-1][2]
            total += (dx*dx + dy*dy + dz*dz) ** 0.5
        return total


class CADAnnotation(Base):
    """
    Text annotation or label in 3D space.
    """
    __tablename__ = "cad_annotations"
    
    annotation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    text = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, default=0.0)
    
    # Text properties
    height = Column(Float, default=2.0)  # Text height in world units
    rotation = Column(Float, default=0.0)  # Degrees
    layer = Column(String, default="LABELS")
    color = Column(String, nullable=True)
    
    # Linked entity (optional)
    linked_entity_type = Column(String, nullable=True)  # 'surface', 'string', 'borehole'
    linked_entity_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    site = relationship("Site")
    
    def __repr__(self):
        return f"<CADAnnotation '{self.text}' at ({self.x:.1f}, {self.y:.1f})>"
