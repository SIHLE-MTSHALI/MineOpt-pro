"""
Annotation Service - Phase 4

Service for managing text annotations and labels in 3D mining views.

Features:
- Multiple annotation types (text, elevation, distance, area, volume)
- Entity linking (link to surfaces, strings, boreholes)
- Auto-update for dynamic labels
- Style management (font, color, size, leader lines)
- CRUD operations
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import uuid
import datetime
import math
import logging

from sqlalchemy.orm import Session

from ..domain.models_surface import CADAnnotation


# =============================================================================
# Enums and Data Classes
# =============================================================================

class AnnotationType(str, Enum):
    """Types of annotations."""
    TEXT = "text"                    # Simple text label
    ELEVATION = "elevation"          # Shows elevation value
    DISTANCE = "distance"            # Shows distance between two points
    AREA = "area"                    # Shows area of polygon
    VOLUME = "volume"                # Shows volume value
    GRADIENT = "gradient"            # Shows slope/gradient
    COORDINATE = "coordinate"        # Shows XYZ coordinates
    BEARING = "bearing"              # Shows bearing/azimuth
    BOREHOLE_ID = "borehole_id"      # Borehole identifier
    SEAM_THICKNESS = "seam_thickness"  # Seam thickness value
    QUALITY = "quality"              # Quality parameter (CV, Ash, etc.)
    CUSTOM = "custom"                # User-defined annotation


class LeaderStyle(str, Enum):
    """Styles for leader lines."""
    NONE = "none"
    STRAIGHT = "straight"
    BENT = "bent"
    CURVED = "curved"


@dataclass
class AnnotationStyle:
    """Style settings for an annotation."""
    font_family: str = "Arial"
    font_size: float = 12.0
    font_color: str = "#000000"
    background_color: Optional[str] = None
    background_opacity: float = 0.8
    border_color: Optional[str] = None
    border_width: float = 0.0
    padding: float = 4.0
    leader_style: str = "straight"
    leader_color: str = "#666666"
    leader_width: float = 1.0
    arrow_size: float = 8.0


@dataclass
class AnnotationData:
    """Complete annotation data for frontend."""
    annotation_id: str
    text: str
    x: float
    y: float
    z: float
    annotation_type: str
    height: float
    rotation: float
    layer: str
    color: Optional[str]
    linked_entity_type: Optional[str]
    linked_entity_id: Optional[str]
    style: Optional[Dict[str, Any]] = None
    is_dynamic: bool = False
    created_at: Optional[datetime.datetime] = None


@dataclass
class LeaderLine:
    """Leader line from annotation to target point."""
    from_x: float
    from_y: float
    from_z: float
    to_x: float
    to_y: float
    to_z: float
    style: str = "straight"
    color: str = "#666666"
    width: float = 1.0


# =============================================================================
# Annotation Service
# =============================================================================

class AnnotationService:
    """
    Service for managing annotations and labels.
    
    Provides:
    - CRUD operations for annotations
    - Entity linking (surfaces, strings, boreholes)
    - Dynamic label updates
    - Style management
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Default styles for annotation types
        self.default_styles: Dict[str, AnnotationStyle] = {
            AnnotationType.TEXT.value: AnnotationStyle(),
            AnnotationType.ELEVATION.value: AnnotationStyle(
                font_color="#0066CC",
                background_color="#FFFFFF"
            ),
            AnnotationType.DISTANCE.value: AnnotationStyle(
                font_color="#006600",
                leader_style="straight"
            ),
            AnnotationType.AREA.value: AnnotationStyle(
                font_color="#660066",
                font_size=14.0
            ),
            AnnotationType.VOLUME.value: AnnotationStyle(
                font_color="#CC6600",
                font_size=14.0
            ),
            AnnotationType.GRADIENT.value: AnnotationStyle(
                font_color="#CC0000"
            ),
            AnnotationType.COORDINATE.value: AnnotationStyle(
                font_family="Courier New",
                font_size=10.0,
                font_color="#333333"
            ),
            AnnotationType.BOREHOLE_ID.value: AnnotationStyle(
                font_color="#000000",
                font_size=10.0,
                rotation=0
            ),
        }
    
    # =========================================================================
    # CRUD Operations
    # =========================================================================
    
    def create_annotation(
        self,
        site_id: str,
        text: str,
        x: float,
        y: float,
        z: float = 0.0,
        annotation_type: str = "text",
        height: float = 2.0,
        rotation: float = 0.0,
        layer: str = "LABELS",
        color: Optional[str] = None,
        linked_entity_type: Optional[str] = None,
        linked_entity_id: Optional[str] = None
    ) -> CADAnnotation:
        """
        Create a new annotation.
        
        Args:
            site_id: Site identifier
            text: Annotation text content
            x, y, z: Position coordinates
            annotation_type: Type from AnnotationType enum
            height: Text height in world units
            rotation: Rotation angle in degrees
            layer: CAD layer name
            color: Hex color code
            linked_entity_type: Type of linked entity
            linked_entity_id: ID of linked entity
            
        Returns:
            Created CADAnnotation object
        """
        annotation = CADAnnotation(
            annotation_id=str(uuid.uuid4()),
            site_id=site_id,
            text=text,
            x=x,
            y=y,
            z=z,
            height=height,
            rotation=rotation,
            layer=layer,
            color=color,
            linked_entity_type=linked_entity_type,
            linked_entity_id=linked_entity_id,
            created_at=datetime.datetime.utcnow()
        )
        
        self.db.add(annotation)
        self.db.commit()
        self.db.refresh(annotation)
        
        self.logger.info(f"Created annotation: '{text[:20]}...' at ({x:.1f}, {y:.1f})")
        return annotation
    
    def get_annotation(self, annotation_id: str) -> Optional[CADAnnotation]:
        """Get an annotation by ID."""
        return self.db.query(CADAnnotation).filter(
            CADAnnotation.annotation_id == annotation_id
        ).first()
    
    def list_annotations(
        self,
        site_id: str,
        layer: Optional[str] = None,
        linked_entity_type: Optional[str] = None,
        linked_entity_id: Optional[str] = None
    ) -> List[CADAnnotation]:
        """
        List annotations with optional filters.
        
        Args:
            site_id: Site identifier
            layer: Filter by layer
            linked_entity_type: Filter by linked entity type
            linked_entity_id: Filter by linked entity ID
            
        Returns:
            List of matching annotations
        """
        query = self.db.query(CADAnnotation).filter(
            CADAnnotation.site_id == site_id
        )
        
        if layer:
            query = query.filter(CADAnnotation.layer == layer)
        if linked_entity_type:
            query = query.filter(CADAnnotation.linked_entity_type == linked_entity_type)
        if linked_entity_id:
            query = query.filter(CADAnnotation.linked_entity_id == linked_entity_id)
        
        return query.order_by(CADAnnotation.created_at).all()
    
    def update_annotation(
        self,
        annotation_id: str,
        **kwargs
    ) -> Optional[CADAnnotation]:
        """
        Update an annotation's properties.
        
        Allowed kwargs: text, x, y, z, height, rotation, layer, color,
                        linked_entity_type, linked_entity_id
        """
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return None
        
        allowed = {'text', 'x', 'y', 'z', 'height', 'rotation', 'layer', 
                   'color', 'linked_entity_type', 'linked_entity_id'}
        
        for key, value in kwargs.items():
            if key in allowed:
                setattr(annotation, key, value)
        
        self.db.commit()
        self.db.refresh(annotation)
        
        return annotation
    
    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return False
        
        self.db.delete(annotation)
        self.db.commit()
        return True
    
    def delete_entity_annotations(
        self,
        entity_type: str,
        entity_id: str
    ) -> int:
        """Delete all annotations linked to a specific entity."""
        count = self.db.query(CADAnnotation).filter(
            CADAnnotation.linked_entity_type == entity_type,
            CADAnnotation.linked_entity_id == entity_id
        ).delete()
        
        self.db.commit()
        self.logger.info(f"Deleted {count} annotations for {entity_type}:{entity_id}")
        return count
    
    # =========================================================================
    # Specialized Annotation Creation
    # =========================================================================
    
    def create_elevation_label(
        self,
        site_id: str,
        x: float,
        y: float,
        elevation: float,
        prefix: str = "RL ",
        suffix: str = "",
        decimals: int = 2,
        layer: str = "ELEVATIONS"
    ) -> CADAnnotation:
        """
        Create an elevation label.
        
        Args:
            site_id: Site identifier
            x, y: Position
            elevation: Elevation value
            prefix: Text prefix (e.g., "RL ")
            suffix: Text suffix (e.g., "m")
            decimals: Decimal places
            layer: Layer name
            
        Returns:
            Created annotation
        """
        text = f"{prefix}{elevation:.{decimals}f}{suffix}"
        
        return self.create_annotation(
            site_id=site_id,
            text=text,
            x=x,
            y=y,
            z=elevation,
            annotation_type=AnnotationType.ELEVATION.value,
            layer=layer,
            color=self.default_styles[AnnotationType.ELEVATION.value].font_color
        )
    
    def create_distance_label(
        self,
        site_id: str,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        layer: str = "DIMENSIONS"
    ) -> CADAnnotation:
        """
        Create a distance label between two points.
        
        Args:
            site_id: Site identifier
            start: Start point (x, y, z)
            end: End point (x, y, z)
            layer: Layer name
            
        Returns:
            Created annotation at midpoint
        """
        # Calculate 3D distance
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        horizontal = math.sqrt(dx*dx + dy*dy)
        
        # Position at midpoint
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        mid_z = (start[2] + end[2]) / 2
        
        # Calculate rotation to align with line
        rotation = math.degrees(math.atan2(dy, dx))
        
        text = f"{distance:.2f}m (H:{horizontal:.2f}m)"
        
        return self.create_annotation(
            site_id=site_id,
            text=text,
            x=mid_x,
            y=mid_y,
            z=mid_z,
            annotation_type=AnnotationType.DISTANCE.value,
            rotation=rotation,
            layer=layer,
            color=self.default_styles[AnnotationType.DISTANCE.value].font_color
        )
    
    def create_area_label(
        self,
        site_id: str,
        centroid: Tuple[float, float, float],
        area_m2: float,
        layer: str = "AREAS"
    ) -> CADAnnotation:
        """
        Create an area label.
        
        Args:
            site_id: Site identifier
            centroid: Center point of area
            area_m2: Area in square meters
            layer: Layer name
            
        Returns:
            Created annotation
        """
        # Convert to hectares if large
        if area_m2 >= 10000:
            text = f"{area_m2/10000:.2f} ha"
        else:
            text = f"{area_m2:.1f} m²"
        
        return self.create_annotation(
            site_id=site_id,
            text=text,
            x=centroid[0],
            y=centroid[1],
            z=centroid[2],
            annotation_type=AnnotationType.AREA.value,
            layer=layer,
            color=self.default_styles[AnnotationType.AREA.value].font_color
        )
    
    def create_volume_label(
        self,
        site_id: str,
        position: Tuple[float, float, float],
        volume_m3: float,
        tonnage: Optional[float] = None,
        layer: str = "VOLUMES"
    ) -> CADAnnotation:
        """
        Create a volume label.
        
        Args:
            site_id: Site identifier
            position: Label position
            volume_m3: Volume in cubic meters
            tonnage: Optional tonnage
            layer: Layer name
            
        Returns:
            Created annotation
        """
        if tonnage:
            text = f"{volume_m3:,.0f} m³\n{tonnage:,.0f} t"
        else:
            text = f"{volume_m3:,.0f} m³"
        
        return self.create_annotation(
            site_id=site_id,
            text=text,
            x=position[0],
            y=position[1],
            z=position[2],
            annotation_type=AnnotationType.VOLUME.value,
            layer=layer,
            color=self.default_styles[AnnotationType.VOLUME.value].font_color
        )
    
    def create_gradient_label(
        self,
        site_id: str,
        position: Tuple[float, float, float],
        gradient_percent: float,
        direction: float = 0.0,
        layer: str = "GRADIENTS"
    ) -> CADAnnotation:
        """
        Create a gradient/slope label.
        
        Args:
            site_id: Site identifier
            position: Label position
            gradient_percent: Gradient as percentage
            direction: Direction angle in degrees
            layer: Layer name
            
        Returns:
            Created annotation
        """
        # Add up/down arrow based on direction
        if gradient_percent > 0:
            arrow = "↗"
        elif gradient_percent < 0:
            arrow = "↘"
        else:
            arrow = "→"
        
        text = f"{arrow} {abs(gradient_percent):.1f}%"
        
        return self.create_annotation(
            site_id=site_id,
            text=text,
            x=position[0],
            y=position[1],
            z=position[2],
            annotation_type=AnnotationType.GRADIENT.value,
            rotation=direction,
            layer=layer,
            color=self.default_styles[AnnotationType.GRADIENT.value].font_color
        )
    
    def create_coordinate_label(
        self,
        site_id: str,
        x: float,
        y: float,
        z: float,
        show_z: bool = True,
        layer: str = "COORDINATES"
    ) -> CADAnnotation:
        """
        Create a coordinate label showing XYZ values.
        
        Args:
            site_id: Site identifier
            x, y, z: Coordinate values
            show_z: Whether to include Z value
            layer: Layer name
            
        Returns:
            Created annotation
        """
        if show_z:
            text = f"E {x:.2f}\nN {y:.2f}\nRL {z:.2f}"
        else:
            text = f"E {x:.2f}\nN {y:.2f}"
        
        return self.create_annotation(
            site_id=site_id,
            text=text,
            x=x,
            y=y,
            z=z,
            annotation_type=AnnotationType.COORDINATE.value,
            layer=layer,
            color=self.default_styles[AnnotationType.COORDINATE.value].font_color
        )
    
    # =========================================================================
    # Entity Linking
    # =========================================================================
    
    def link_to_entity(
        self,
        annotation_id: str,
        entity_type: str,
        entity_id: str
    ) -> bool:
        """
        Link an annotation to an entity.
        
        Args:
            annotation_id: Annotation to link
            entity_type: Type of entity ('surface', 'string', 'borehole')
            entity_id: Entity ID
            
        Returns:
            Success status
        """
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return False
        
        annotation.linked_entity_type = entity_type
        annotation.linked_entity_id = entity_id
        self.db.commit()
        
        return True
    
    def unlink_from_entity(self, annotation_id: str) -> bool:
        """Remove entity link from an annotation."""
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return False
        
        annotation.linked_entity_type = None
        annotation.linked_entity_id = None
        self.db.commit()
        
        return True
    
    def get_entity_annotations(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[CADAnnotation]:
        """Get all annotations linked to a specific entity."""
        return self.db.query(CADAnnotation).filter(
            CADAnnotation.linked_entity_type == entity_type,
            CADAnnotation.linked_entity_id == entity_id
        ).all()
    
    # =========================================================================
    # Batch Operations
    # =========================================================================
    
    def create_contour_labels(
        self,
        site_id: str,
        contour_data: List[Dict],
        interval: float = 5.0,
        label_interval: float = 25.0,
        layer: str = "CONTOUR_LABELS"
    ) -> List[CADAnnotation]:
        """
        Create labels for contours at specified intervals.
        
        Args:
            site_id: Site identifier
            contour_data: List of contour dicts with 'elevation' and 'points'
            interval: Contour interval
            label_interval: Label every N meters (e.g., every 5th contour)
            layer: Layer name
            
        Returns:
            List of created annotations
        """
        annotations = []
        
        for contour in contour_data:
            elevation = contour.get("elevation", 0)
            points = contour.get("points", [])
            
            # Only label at label interval
            if elevation % label_interval != 0:
                continue
            
            if len(points) < 2:
                continue
            
            # Place label at midpoint of contour
            mid_idx = len(points) // 2
            mid_pt = points[mid_idx]
            
            # Calculate rotation from adjacent points
            if mid_idx > 0 and mid_idx < len(points) - 1:
                prev_pt = points[mid_idx - 1]
                next_pt = points[mid_idx + 1]
                dx = next_pt[0] - prev_pt[0]
                dy = next_pt[1] - prev_pt[1]
                rotation = math.degrees(math.atan2(dy, dx))
            else:
                rotation = 0
            
            annotation = self.create_annotation(
                site_id=site_id,
                text=f"{elevation:.0f}",
                x=mid_pt[0],
                y=mid_pt[1],
                z=mid_pt[2] if len(mid_pt) > 2 else elevation,
                annotation_type=AnnotationType.ELEVATION.value,
                rotation=rotation,
                layer=layer,
                height=1.5
            )
            annotations.append(annotation)
        
        return annotations
    
    def create_borehole_labels(
        self,
        site_id: str,
        boreholes: List[Dict],
        layer: str = "BOREHOLE_LABELS"
    ) -> List[CADAnnotation]:
        """
        Create labels for borehole collars.
        
        Args:
            site_id: Site identifier
            boreholes: List of borehole dicts with 'hole_id', 'x', 'y', 'z'
            layer: Layer name
            
        Returns:
            List of created annotations
        """
        annotations = []
        
        for bh in boreholes:
            hole_id = bh.get("hole_id", bh.get("id", ""))
            x = bh.get("x", bh.get("easting", 0))
            y = bh.get("y", bh.get("northing", 0))
            z = bh.get("z", bh.get("elevation", 0))
            
            annotation = self.create_annotation(
                site_id=site_id,
                text=hole_id,
                x=x,
                y=y,
                z=z,
                annotation_type=AnnotationType.BOREHOLE_ID.value,
                layer=layer,
                linked_entity_type="borehole",
                linked_entity_id=bh.get("borehole_id", bh.get("id", ""))
            )
            annotations.append(annotation)
        
        return annotations
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_annotation_types(self) -> List[Dict[str, str]]:
        """Get list of available annotation types."""
        return [
            {"value": t.value, "name": t.name.replace("_", " ").title()}
            for t in AnnotationType
        ]
    
    def get_default_style(self, annotation_type: str) -> Dict[str, Any]:
        """Get default style for an annotation type."""
        style = self.default_styles.get(annotation_type, AnnotationStyle())
        return {
            "font_family": style.font_family,
            "font_size": style.font_size,
            "font_color": style.font_color,
            "background_color": style.background_color,
            "background_opacity": style.background_opacity,
            "border_color": style.border_color,
            "border_width": style.border_width,
            "padding": style.padding,
            "leader_style": style.leader_style,
            "leader_color": style.leader_color,
            "leader_width": style.leader_width,
            "arrow_size": style.arrow_size
        }
    
    def to_annotation_data(self, annotation: CADAnnotation) -> AnnotationData:
        """Convert database annotation to data class."""
        return AnnotationData(
            annotation_id=annotation.annotation_id,
            text=annotation.text,
            x=annotation.x,
            y=annotation.y,
            z=annotation.z,
            annotation_type="text",  # Default
            height=annotation.height,
            rotation=annotation.rotation,
            layer=annotation.layer,
            color=annotation.color,
            linked_entity_type=annotation.linked_entity_type,
            linked_entity_id=annotation.linked_entity_id,
            created_at=annotation.created_at
        )


# =============================================================================
# Factory Function
# =============================================================================

def get_annotation_service(db: Session) -> AnnotationService:
    """Get annotation service instance."""
    return AnnotationService(db)
