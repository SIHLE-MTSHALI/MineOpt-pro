"""
DXF File Service - Phase 1 File Format Foundation

Provides comprehensive DXF file reading and writing capabilities for mining geometry.
Uses the open-source ezdxf library (MIT license - FREE).

Supported Entity Types:
- POINT: Borehole collars, stockpile locations, survey points
- LINE: Simple line segments
- POLYLINE/LWPOLYLINE: Pit boundaries, mining blocks, contours
- 3DFACE: Triangulated surfaces, block faces

Features:
- Layer-based material type classification
- Attribute extraction from entity data
- Coordinate system handling
- Export with layer organization
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import uuid
from datetime import datetime
import io

try:
    import ezdxf
    from ezdxf.entities import DXFEntity
    from ezdxf.layouts import Modelspace
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


class DXFEntityType(str, Enum):
    """Supported DXF entity types."""
    POINT = "POINT"
    LINE = "LINE"
    POLYLINE = "POLYLINE"
    LWPOLYLINE = "LWPOLYLINE"
    FACE3D = "3DFACE"
    CIRCLE = "CIRCLE"
    ARC = "ARC"
    TEXT = "TEXT"
    MTEXT = "MTEXT"
    INSERT = "INSERT"  # Block references


@dataclass
class DXFPoint:
    """A 3D point extracted from DXF."""
    x: float
    y: float
    z: float = 0.0


@dataclass
class ParsedEntity:
    """A parsed DXF entity with extracted geometry and attributes."""
    entity_type: DXFEntityType
    layer: str
    color: Optional[int] = None
    points: List[DXFPoint] = field(default_factory=list)
    is_closed: bool = False
    attributes: Dict[str, Any] = field(default_factory=dict)
    handle: Optional[str] = None
    

@dataclass
class DXFParseResult:
    """Result of parsing a DXF file."""
    success: bool
    filename: Optional[str] = None
    version: Optional[str] = None
    layers: List[str] = field(default_factory=list)
    entities: List[ParsedEntity] = field(default_factory=list)
    entity_count: int = 0
    point_count: int = 0
    polyline_count: int = 0
    face_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    extent_min: Optional[DXFPoint] = None
    extent_max: Optional[DXFPoint] = None


@dataclass
class LayerMapping:
    """Maps a DXF layer to a material type or classification."""
    layer_name: str
    material_type: Optional[str] = None
    activity_type: Optional[str] = None
    color_override: Optional[str] = None
    import_enabled: bool = True


@dataclass
class DXFExportConfig:
    """Configuration for DXF export."""
    version: str = "R2018"  # R12, R2000, R2004, R2007, R2010, R2013, R2018
    layer_by_material: bool = True
    layer_by_activity: bool = False
    include_attributes: bool = True
    units: str = "Meters"


class DXFService:
    """
    Service for reading and writing DXF files.
    
    Provides:
    - Parse DXF files to extract geometry
    - Layer-based material classification
    - Export geometry to DXF with proper layers
    - Coordinate extent calculation
    """
    
    def __init__(self):
        if not EZDXF_AVAILABLE:
            raise ImportError(
                "ezdxf library is required but not installed. "
                "Install with: pip install ezdxf>=1.0.0"
            )
    
    def parse_file(self, file_path: str) -> DXFParseResult:
        """
        Parse a DXF file and extract all supported entities.
        
        Args:
            file_path: Path to the DXF file
            
        Returns:
            DXFParseResult with parsed entities and metadata
        """
        result = DXFParseResult(success=False)
        
        try:
            doc = ezdxf.readfile(file_path)
            result.filename = file_path
            result.version = doc.dxfversion
            
            # Extract layers
            result.layers = [layer.dxf.name for layer in doc.layers]
            
            # Parse modelspace entities
            msp = doc.modelspace()
            self._parse_modelspace(msp, result)
            
            # Calculate extents
            self._calculate_extents(result)
            
            result.success = True
            
        except Exception as e:
            result.errors.append(f"Failed to parse DXF file: {str(e)}")
            
        return result
    
    def parse_bytes(self, file_bytes: bytes, filename: str = "upload.dxf") -> DXFParseResult:
        """
        Parse DXF from bytes (for file uploads).
        
        Args:
            file_bytes: DXF file content as bytes
            filename: Original filename for reference
            
        Returns:
            DXFParseResult with parsed entities
        """
        result = DXFParseResult(success=False, filename=filename)
        
        try:
            # ezdxf can read from a stream
            stream = io.BytesIO(file_bytes)
            doc = ezdxf.read(stream)
            result.version = doc.dxfversion
            
            # Extract layers
            result.layers = [layer.dxf.name for layer in doc.layers]
            
            # Parse modelspace
            msp = doc.modelspace()
            self._parse_modelspace(msp, result)
            
            # Calculate extents
            self._calculate_extents(result)
            
            result.success = True
            
        except Exception as e:
            result.errors.append(f"Failed to parse DXF bytes: {str(e)}")
            
        return result
    
    def _parse_modelspace(self, msp: "Modelspace", result: DXFParseResult):
        """Parse all entities in modelspace."""
        
        for entity in msp:
            try:
                parsed = self._parse_entity(entity)
                if parsed:
                    result.entities.append(parsed)
                    result.entity_count += 1
                    
                    # Update type counts
                    if parsed.entity_type == DXFEntityType.POINT:
                        result.point_count += 1
                    elif parsed.entity_type in [DXFEntityType.POLYLINE, DXFEntityType.LWPOLYLINE]:
                        result.polyline_count += 1
                    elif parsed.entity_type == DXFEntityType.FACE3D:
                        result.face_count += 1
                        
            except Exception as e:
                result.warnings.append(f"Failed to parse entity {entity.dxftype()}: {str(e)}")
    
    def _parse_entity(self, entity: "DXFEntity") -> Optional[ParsedEntity]:
        """Parse a single DXF entity."""
        
        dxf_type = entity.dxftype()
        
        if dxf_type == "POINT":
            return self._parse_point(entity)
        elif dxf_type == "LINE":
            return self._parse_line(entity)
        elif dxf_type == "LWPOLYLINE":
            return self._parse_lwpolyline(entity)
        elif dxf_type == "POLYLINE":
            return self._parse_polyline(entity)
        elif dxf_type == "3DFACE":
            return self._parse_3dface(entity)
        elif dxf_type == "CIRCLE":
            return self._parse_circle(entity)
        elif dxf_type == "ARC":
            return self._parse_arc(entity)
        elif dxf_type == "TEXT":
            return self._parse_text(entity)
        elif dxf_type == "MTEXT":
            return self._parse_mtext(entity)
        
        # Unsupported entity type - skip silently
        return None
    
    def _parse_point(self, entity) -> ParsedEntity:
        """Parse a POINT entity."""
        loc = entity.dxf.location
        return ParsedEntity(
            entity_type=DXFEntityType.POINT,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=[DXFPoint(x=loc.x, y=loc.y, z=loc.z)],
            handle=entity.dxf.handle
        )
    
    def _parse_line(self, entity) -> ParsedEntity:
        """Parse a LINE entity."""
        start = entity.dxf.start
        end = entity.dxf.end
        return ParsedEntity(
            entity_type=DXFEntityType.LINE,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=[
                DXFPoint(x=start.x, y=start.y, z=start.z),
                DXFPoint(x=end.x, y=end.y, z=end.z)
            ],
            handle=entity.dxf.handle
        )
    
    def _parse_lwpolyline(self, entity) -> ParsedEntity:
        """Parse a LWPOLYLINE (lightweight polyline) entity."""
        points = []
        elevation = getattr(entity.dxf, 'elevation', 0.0)
        
        for x, y, start_width, end_width, bulge in entity.get_points(format='xyseb'):
            points.append(DXFPoint(x=x, y=y, z=elevation))
        
        return ParsedEntity(
            entity_type=DXFEntityType.LWPOLYLINE,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=points,
            is_closed=entity.closed,
            handle=entity.dxf.handle
        )
    
    def _parse_polyline(self, entity) -> ParsedEntity:
        """Parse a POLYLINE entity (3D polylines)."""
        points = []
        
        for vertex in entity.vertices:
            loc = vertex.dxf.location
            points.append(DXFPoint(x=loc.x, y=loc.y, z=loc.z))
        
        return ParsedEntity(
            entity_type=DXFEntityType.POLYLINE,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=points,
            is_closed=entity.is_closed,
            handle=entity.dxf.handle
        )
    
    def _parse_3dface(self, entity) -> ParsedEntity:
        """Parse a 3DFACE entity (triangular/quad surface)."""
        points = []
        
        # 3DFACE has up to 4 corners
        for i in range(4):
            try:
                corner = getattr(entity.dxf, f'vtx{i}')
                points.append(DXFPoint(x=corner.x, y=corner.y, z=corner.z))
            except AttributeError:
                break
        
        return ParsedEntity(
            entity_type=DXFEntityType.FACE3D,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=points,
            is_closed=True,  # Faces are always closed
            handle=entity.dxf.handle
        )
    
    def _parse_circle(self, entity) -> ParsedEntity:
        """Parse a CIRCLE entity."""
        center = entity.dxf.center
        return ParsedEntity(
            entity_type=DXFEntityType.CIRCLE,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=[DXFPoint(x=center.x, y=center.y, z=center.z)],
            attributes={"radius": entity.dxf.radius},
            handle=entity.dxf.handle
        )
    
    def _parse_arc(self, entity) -> ParsedEntity:
        """Parse an ARC entity."""
        center = entity.dxf.center
        return ParsedEntity(
            entity_type=DXFEntityType.ARC,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=[DXFPoint(x=center.x, y=center.y, z=center.z)],
            attributes={
                "radius": entity.dxf.radius,
                "start_angle": entity.dxf.start_angle,
                "end_angle": entity.dxf.end_angle
            },
            handle=entity.dxf.handle
        )
    
    def _parse_text(self, entity) -> ParsedEntity:
        """Parse a TEXT entity."""
        insert = entity.dxf.insert
        return ParsedEntity(
            entity_type=DXFEntityType.TEXT,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=[DXFPoint(x=insert.x, y=insert.y, z=insert.z)],
            attributes={
                "text": entity.dxf.text,
                "height": entity.dxf.height,
                "rotation": getattr(entity.dxf, 'rotation', 0)
            },
            handle=entity.dxf.handle
        )
    
    def _parse_mtext(self, entity) -> ParsedEntity:
        """Parse an MTEXT (multiline text) entity."""
        insert = entity.dxf.insert
        return ParsedEntity(
            entity_type=DXFEntityType.MTEXT,
            layer=entity.dxf.layer,
            color=getattr(entity.dxf, 'color', None),
            points=[DXFPoint(x=insert.x, y=insert.y, z=insert.z)],
            attributes={
                "text": entity.text,
                "char_height": entity.dxf.char_height
            },
            handle=entity.dxf.handle
        )
    
    def _calculate_extents(self, result: DXFParseResult):
        """Calculate the bounding box of all entities."""
        if not result.entities:
            return
        
        all_points = []
        for entity in result.entities:
            all_points.extend(entity.points)
        
        if not all_points:
            return
        
        min_x = min(p.x for p in all_points)
        min_y = min(p.y for p in all_points)
        min_z = min(p.z for p in all_points)
        max_x = max(p.x for p in all_points)
        max_y = max(p.y for p in all_points)
        max_z = max(p.z for p in all_points)
        
        result.extent_min = DXFPoint(x=min_x, y=min_y, z=min_z)
        result.extent_max = DXFPoint(x=max_x, y=max_y, z=max_z)
    
    def get_entities_by_layer(
        self, 
        result: DXFParseResult, 
        layer_name: str
    ) -> List[ParsedEntity]:
        """Get all entities on a specific layer."""
        return [e for e in result.entities if e.layer == layer_name]
    
    def get_entities_by_type(
        self, 
        result: DXFParseResult, 
        entity_type: DXFEntityType
    ) -> List[ParsedEntity]:
        """Get all entities of a specific type."""
        return [e for e in result.entities if e.entity_type == entity_type]
    
    # =========================================================================
    # EXPORT FUNCTIONS
    # =========================================================================
    
    def create_new_document(
        self, 
        version: str = "R2018"
    ) -> "ezdxf.document.Drawing":
        """
        Create a new DXF document.
        
        Args:
            version: DXF version (R12, R2000, R2004, R2007, R2010, R2013, R2018)
            
        Returns:
            New ezdxf Drawing object
        """
        return ezdxf.new(dxfversion=version)
    
    def add_layer(
        self, 
        doc: "ezdxf.document.Drawing", 
        name: str, 
        color: int = 7,
        linetype: str = "CONTINUOUS"
    ):
        """
        Add a layer to the document.
        
        Args:
            doc: The DXF document
            name: Layer name
            color: AutoCAD color index (1-255)
            linetype: Line type name
        """
        if name not in doc.layers:
            doc.layers.add(name, color=color, linetype=linetype)
    
    def add_point(
        self, 
        doc: "ezdxf.document.Drawing", 
        point: DXFPoint, 
        layer: str = "0"
    ):
        """Add a point to the document."""
        msp = doc.modelspace()
        msp.add_point((point.x, point.y, point.z), dxfattribs={"layer": layer})
    
    def add_line(
        self, 
        doc: "ezdxf.document.Drawing", 
        start: DXFPoint, 
        end: DXFPoint, 
        layer: str = "0"
    ):
        """Add a line to the document."""
        msp = doc.modelspace()
        msp.add_line(
            (start.x, start.y, start.z), 
            (end.x, end.y, end.z), 
            dxfattribs={"layer": layer}
        )
    
    def add_polyline(
        self, 
        doc: "ezdxf.document.Drawing", 
        points: List[DXFPoint], 
        layer: str = "0",
        closed: bool = False
    ):
        """
        Add a polyline to the document.
        
        Args:
            doc: The DXF document
            points: List of points defining the polyline
            layer: Layer name
            closed: Whether to close the polyline
        """
        msp = doc.modelspace()
        coords = [(p.x, p.y, p.z) for p in points]
        
        # Check if 2D or 3D polyline needed
        all_same_z = all(p.z == points[0].z for p in points)
        
        if all_same_z:
            # Use LWPOLYLINE for 2D
            coords_2d = [(p.x, p.y) for p in points]
            msp.add_lwpolyline(coords_2d, close=closed, dxfattribs={"layer": layer})
        else:
            # Use 3D POLYLINE
            msp.add_polyline3d(coords, close=closed, dxfattribs={"layer": layer})
    
    def add_3dface(
        self, 
        doc: "ezdxf.document.Drawing", 
        vertices: List[DXFPoint], 
        layer: str = "0"
    ):
        """
        Add a 3D face to the document.
        
        Args:
            doc: The DXF document
            vertices: 3 or 4 vertices defining the face
            layer: Layer name
        """
        if len(vertices) < 3 or len(vertices) > 4:
            raise ValueError("3DFACE requires 3 or 4 vertices")
        
        msp = doc.modelspace()
        coords = [(v.x, v.y, v.z) for v in vertices]
        
        # Pad to 4 vertices if only 3 provided (repeat last vertex)
        while len(coords) < 4:
            coords.append(coords[-1])
        
        msp.add_3dface(coords, dxfattribs={"layer": layer})
    
    def add_text(
        self, 
        doc: "ezdxf.document.Drawing", 
        text: str, 
        position: DXFPoint, 
        height: float = 1.0,
        layer: str = "0"
    ):
        """Add text to the document."""
        msp = doc.modelspace()
        msp.add_text(
            text, 
            dxfattribs={
                "layer": layer, 
                "insert": (position.x, position.y, position.z),
                "height": height
            }
        )
    
    def save_document(self, doc: "ezdxf.document.Drawing", file_path: str):
        """Save the document to a file."""
        doc.saveas(file_path)
    
    def export_to_bytes(self, doc: "ezdxf.document.Drawing") -> bytes:
        """Export the document to bytes (for downloads)."""
        stream = io.BytesIO()
        doc.write(stream)
        stream.seek(0)
        return stream.read()
    
    # =========================================================================
    # HIGH-LEVEL EXPORT FUNCTIONS
    # =========================================================================
    
    def export_activity_areas(
        self, 
        areas: List[Dict],
        file_path: Optional[str] = None,
        config: Optional[DXFExportConfig] = None
    ) -> Optional[bytes]:
        """
        Export activity areas to DXF.
        
        Args:
            areas: List of activity area dictionaries with geometry
            file_path: Path to save file (if None, returns bytes)
            config: Export configuration
            
        Returns:
            Bytes if file_path is None, otherwise None
        """
        config = config or DXFExportConfig()
        doc = self.create_new_document(config.version)
        
        # Create layers for each activity type
        activity_colors = {
            "Coal Mining": 3,      # Green
            "Waste Mining": 1,     # Red
            "Rehandle": 5,         # Blue
            "Stockpile": 4,        # Cyan
            "Default": 7           # White
        }
        
        for area in areas:
            # Determine layer name
            activity_type = area.get("activity_type", "Default")
            layer_name = f"AREA_{activity_type.upper().replace(' ', '_')}"
            
            # Add layer if not exists
            color = activity_colors.get(activity_type, 7)
            self.add_layer(doc, layer_name, color=color)
            
            # Get geometry
            geometry = area.get("geometry", {})
            vertices_data = geometry.get("vertices", [])
            
            if vertices_data:
                # Convert to DXFPoints
                points = [
                    DXFPoint(x=v[0], y=v[1], z=v[2] if len(v) > 2 else 0)
                    for v in vertices_data
                ]
                
                # Add as polyline (closed polygon)
                self.add_polyline(doc, points, layer=layer_name, closed=True)
        
        if file_path:
            self.save_document(doc, file_path)
            return None
        else:
            return self.export_to_bytes(doc)
    
    def export_boreholes(
        self, 
        boreholes: List[Dict],
        file_path: Optional[str] = None,
        config: Optional[DXFExportConfig] = None
    ) -> Optional[bytes]:
        """
        Export borehole collars and traces to DXF.
        
        Args:
            boreholes: List of borehole dictionaries with collar and trace data
            file_path: Path to save file (if None, returns bytes)
            config: Export configuration
            
        Returns:
            Bytes if file_path is None, otherwise None
        """
        config = config or DXFExportConfig()
        doc = self.create_new_document(config.version)
        
        # Create layers
        self.add_layer(doc, "BOREHOLE_COLLARS", color=1)  # Red
        self.add_layer(doc, "BOREHOLE_TRACES", color=3)   # Green
        self.add_layer(doc, "BOREHOLE_LABELS", color=7)   # White
        
        for bh in boreholes:
            collar = bh.get("collar", {})
            trace = bh.get("trace", [])
            hole_id = bh.get("hole_id", "Unknown")
            
            # Add collar point
            if collar:
                collar_point = DXFPoint(
                    x=collar.get("easting", 0),
                    y=collar.get("northing", 0),
                    z=collar.get("elevation", 0)
                )
                self.add_point(doc, collar_point, layer="BOREHOLE_COLLARS")
                
                # Add label
                self.add_text(
                    doc, 
                    hole_id, 
                    DXFPoint(x=collar_point.x + 2, y=collar_point.y + 2, z=collar_point.z),
                    height=2.0,
                    layer="BOREHOLE_LABELS"
                )
            
            # Add trace polyline
            if trace and len(trace) > 1:
                trace_points = [
                    DXFPoint(x=p.get("x", 0), y=p.get("y", 0), z=p.get("z", 0))
                    for p in trace
                ]
                self.add_polyline(doc, trace_points, layer="BOREHOLE_TRACES", closed=False)
        
        if file_path:
            self.save_document(doc, file_path)
            return None
        else:
            return self.export_to_bytes(doc)


# Singleton instance
_dxf_service: Optional[DXFService] = None


def get_dxf_service() -> DXFService:
    """Get the singleton DXF service instance."""
    global _dxf_service
    if _dxf_service is None:
        _dxf_service = DXFService()
    return _dxf_service
