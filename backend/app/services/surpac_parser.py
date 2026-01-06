"""
Surpac String File Parser - Phase 1 File Format Foundation

Parses and exports GEOVIA Surpac .str (string) files.
These ASCII files contain 3D coordinate data organized as strings (polylines).

Surpac .str Format:
- Line 1: Header (location code, date, purpose)
- Line 2: Axis definition (string 0)
- Lines 3+: String#, Northing, Easting, RL, D1, D2, D3, D4, D5
- Final line: 0, 0, 0, 0, END

Features:
- Parse .str files to extract geometry
- Handle descriptor fields D1-D5
- Export geometry to .str format
- Support both ASCII and binary detection
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, TextIO
from enum import Enum
import re
from datetime import datetime


@dataclass
class SurpacPoint:
    """A point in a Surpac string file."""
    string_number: int
    northing: float  # Y coordinate
    easting: float   # X coordinate
    rl: float        # Reduced Level (Z coordinate / elevation)
    descriptors: List[str] = field(default_factory=list)  # D1-D5
    
    @property
    def x(self) -> float:
        """X coordinate (easting)."""
        return self.easting
    
    @property
    def y(self) -> float:
        """Y coordinate (northing)."""
        return self.northing
    
    @property
    def z(self) -> float:
        """Z coordinate (RL)."""
        return self.rl


@dataclass
class SurpacString:
    """A string (polyline) containing multiple points."""
    string_number: int
    points: List[SurpacPoint] = field(default_factory=list)
    is_closed: bool = False
    
    @property
    def point_count(self) -> int:
        return len(self.points)
    
    def get_first_descriptor(self, index: int = 0) -> Optional[str]:
        """Get the first non-empty descriptor at given index across all points."""
        for point in self.points:
            if point.descriptors and len(point.descriptors) > index:
                desc = point.descriptors[index]
                if desc and desc.strip():
                    return desc.strip()
        return None


@dataclass
class SurpacHeader:
    """Header information from a Surpac string file."""
    location_code: str = ""
    date: str = ""
    purpose: str = ""
    raw_line: str = ""


@dataclass
class SurpacAxis:
    """Axis definition from a Surpac string file."""
    start: Optional[SurpacPoint] = None
    end: Optional[SurpacPoint] = None
    is_defined: bool = False


@dataclass
class SurpacParseResult:
    """Result of parsing a Surpac string file."""
    success: bool
    filename: Optional[str] = None
    header: Optional[SurpacHeader] = None
    axis: Optional[SurpacAxis] = None
    strings: List[SurpacString] = field(default_factory=list)
    string_count: int = 0
    point_count: int = 0
    descriptor_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    extent_min: Optional[Tuple[float, float, float]] = None
    extent_max: Optional[Tuple[float, float, float]] = None


class SurpacParser:
    """
    Parser for GEOVIA Surpac .str (string) files.
    
    Provides:
    - Parse .str files to extract strings and points
    - Handle descriptor fields
    - Calculate extents
    - Export to .str format
    """
    
    def __init__(self):
        self._current_string_points: List[SurpacPoint] = []
        self._current_string_number: Optional[int] = None
    
    def parse_file(self, file_path: str) -> SurpacParseResult:
        """
        Parse a Surpac .str file.
        
        Args:
            file_path: Path to the .str file
            
        Returns:
            SurpacParseResult with parsed strings and metadata
        """
        result = SurpacParseResult(success=False, filename=file_path)
        
        try:
            # Check if binary
            with open(file_path, 'rb') as f:
                first_bytes = f.read(100)
                if b'\x00' in first_bytes:
                    result.warnings.append(
                        "File appears to be binary. Surpac 6.9+ saves binary by default. "
                        "ASCII format required."
                    )
                    result.errors.append("Binary .str files not supported. Please export as ASCII from Surpac.")
                    return result
            
            # Parse ASCII file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                self._parse_content(f, result)
            
            result.success = len(result.errors) == 0
            
        except Exception as e:
            result.errors.append(f"Failed to parse file: {str(e)}")
        
        return result
    
    def parse_string(self, content: str, filename: str = "upload.str") -> SurpacParseResult:
        """
        Parse Surpac .str content from a string.
        
        Args:
            content: File content as string
            filename: Original filename for reference
            
        Returns:
            SurpacParseResult with parsed data
        """
        result = SurpacParseResult(success=False, filename=filename)
        
        try:
            import io
            f = io.StringIO(content)
            self._parse_content(f, result)
            result.success = len(result.errors) == 0
        except Exception as e:
            result.errors.append(f"Failed to parse content: {str(e)}")
        
        return result
    
    def parse_bytes(self, file_bytes: bytes, filename: str = "upload.str") -> SurpacParseResult:
        """
        Parse Surpac .str content from bytes.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename for reference
            
        Returns:
            SurpacParseResult with parsed data
        """
        # Check for binary
        if b'\x00' in file_bytes[:100]:
            result = SurpacParseResult(success=False, filename=filename)
            result.errors.append("Binary .str files not supported. Please export as ASCII from Surpac.")
            return result
        
        # Decode and parse
        try:
            content = file_bytes.decode('utf-8', errors='replace')
            return self.parse_string(content, filename)
        except Exception as e:
            result = SurpacParseResult(success=False, filename=filename)
            result.errors.append(f"Failed to decode file: {str(e)}")
            return result
    
    def _parse_content(self, f: TextIO, result: SurpacParseResult):
        """Parse file content."""
        lines = f.readlines()
        
        if len(lines) < 3:
            result.errors.append("File too short. Expected at least header, axis, and data lines.")
            return
        
        # Parse header (line 1)
        result.header = self._parse_header(lines[0])
        
        # Parse axis (line 2)
        result.axis = self._parse_axis(lines[1])
        
        # Reset state
        self._current_string_points = []
        self._current_string_number = None
        strings_dict: Dict[int, SurpacString] = {}
        
        # Parse data lines
        for line_num, line in enumerate(lines[2:], start=3):
            try:
                point = self._parse_point_line(line)
                
                if point is None:
                    continue
                
                # Check for END marker
                if point.string_number == 0 and any(
                    d.upper() == "END" for d in point.descriptors if d
                ):
                    break
                
                # Check for segment break (string_number=0, all coords=0)
                if (point.string_number == 0 and 
                    point.easting == 0 and 
                    point.northing == 0 and 
                    point.rl == 0):
                    continue
                
                # Add point to appropriate string
                if point.string_number not in strings_dict:
                    strings_dict[point.string_number] = SurpacString(
                        string_number=point.string_number
                    )
                
                strings_dict[point.string_number].points.append(point)
                result.point_count += 1
                
                # Count descriptors
                if point.descriptors:
                    result.descriptor_count = max(
                        result.descriptor_count, 
                        len(point.descriptors)
                    )
                    
            except Exception as e:
                result.warnings.append(f"Line {line_num}: {str(e)}")
        
        # Convert to list, sorted by string number
        result.strings = sorted(strings_dict.values(), key=lambda s: s.string_number)
        result.string_count = len(result.strings)
        
        # Check if strings are closed
        for s in result.strings:
            if len(s.points) >= 3:
                first = s.points[0]
                last = s.points[-1]
                # Check if first and last points are the same (within tolerance)
                dist_sq = (first.x - last.x)**2 + (first.y - last.y)**2 + (first.z - last.z)**2
                if dist_sq < 0.001:  # 1mm tolerance
                    s.is_closed = True
        
        # Calculate extents
        self._calculate_extents(result)
    
    def _parse_header(self, line: str) -> SurpacHeader:
        """Parse the header line."""
        header = SurpacHeader(raw_line=line.strip())
        
        # Header format varies, try to extract what we can
        parts = line.strip().split(',')
        if len(parts) >= 1:
            header.location_code = parts[0].strip()
        if len(parts) >= 2:
            header.date = parts[1].strip()
        if len(parts) >= 3:
            header.purpose = ','.join(parts[2:]).strip()
        
        return header
    
    def _parse_axis(self, line: str) -> SurpacAxis:
        """Parse the axis definition line (string 0)."""
        axis = SurpacAxis()
        
        try:
            parts = self._split_line(line)
            if len(parts) >= 4:
                string_num = int(float(parts[0]))
                if string_num == 0:
                    # Axis is defined
                    northing = float(parts[1])
                    easting = float(parts[2])
                    rl = float(parts[3])
                    
                    if northing != 0 or easting != 0 or rl != 0:
                        axis.is_defined = True
                        axis.start = SurpacPoint(
                            string_number=0,
                            northing=northing,
                            easting=easting,
                            rl=rl
                        )
        except Exception:
            pass
        
        return axis
    
    def _parse_point_line(self, line: str) -> Optional[SurpacPoint]:
        """Parse a single point line."""
        line = line.strip()
        if not line:
            return None
        
        parts = self._split_line(line)
        
        if len(parts) < 4:
            return None
        
        try:
            string_number = int(float(parts[0]))
            northing = float(parts[1])
            easting = float(parts[2])
            rl = float(parts[3])
            
            # Parse descriptors (D1-D5)
            descriptors = []
            for i in range(4, min(len(parts), 9)):  # Up to 5 descriptors
                descriptors.append(parts[i])
            
            return SurpacPoint(
                string_number=string_number,
                northing=northing,
                easting=easting,
                rl=rl,
                descriptors=descriptors
            )
        except ValueError:
            return None
    
    def _split_line(self, line: str) -> List[str]:
        """Split a line on comma delimiter, handling quoted strings."""
        # Simple split for most cases
        return [p.strip() for p in line.split(',')]
    
    def _calculate_extents(self, result: SurpacParseResult):
        """Calculate bounding box of all points."""
        all_points = []
        for s in result.strings:
            all_points.extend(s.points)
        
        if not all_points:
            return
        
        min_e = min(p.easting for p in all_points)
        min_n = min(p.northing for p in all_points)
        min_z = min(p.rl for p in all_points)
        max_e = max(p.easting for p in all_points)
        max_n = max(p.northing for p in all_points)
        max_z = max(p.rl for p in all_points)
        
        result.extent_min = (min_e, min_n, min_z)
        result.extent_max = (max_e, max_n, max_z)
    
    # =========================================================================
    # EXPORT FUNCTIONS
    # =========================================================================
    
    def export_to_string(
        self,
        strings: List[SurpacString],
        header_purpose: str = "Exported from MineOpt Pro",
        location_code: str = "MINEOPT"
    ) -> str:
        """
        Export strings to Surpac .str format.
        
        Args:
            strings: List of SurpacString objects to export
            header_purpose: Purpose/description for header
            location_code: Location code for header
            
        Returns:
            String content in .str format
        """
        lines = []
        
        # Header line
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines.append(f"{location_code}, {date_str}, {header_purpose}")
        
        # Axis line (zeros if not defined)
        lines.append("0, 0, 0, 0,")
        
        # Point lines
        for s in strings:
            for point in s.points:
                # Format: string_number, northing, easting, rl, [d1, d2, ...]
                parts = [
                    str(point.string_number),
                    f"{point.northing:.3f}",
                    f"{point.easting:.3f}",
                    f"{point.rl:.3f}"
                ]
                
                # Add descriptors
                for desc in point.descriptors:
                    parts.append(desc if desc else "")
                
                lines.append(", ".join(parts))
            
            # Add segment break after each string
            lines.append("0, 0, 0, 0,")
        
        # End marker
        lines.append("0, 0, 0, 0, END")
        
        return "\n".join(lines)
    
    def export_to_file(
        self,
        strings: List[SurpacString],
        file_path: str,
        header_purpose: str = "Exported from MineOpt Pro",
        location_code: str = "MINEOPT"
    ):
        """Export strings to a .str file."""
        content = self.export_to_string(strings, header_purpose, location_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def export_to_bytes(
        self,
        strings: List[SurpacString],
        header_purpose: str = "Exported from MineOpt Pro",
        location_code: str = "MINEOPT"
    ) -> bytes:
        """Export strings to bytes (for downloads)."""
        content = self.export_to_string(strings, header_purpose, location_code)
        return content.encode('utf-8')
    
    # =========================================================================
    # CONVERSION FUNCTIONS
    # =========================================================================
    
    def to_activity_area_geometry(
        self, 
        surpac_string: SurpacString
    ) -> Dict[str, Any]:
        """
        Convert a Surpac string to activity area geometry format.
        
        Args:
            surpac_string: The Surpac string to convert
            
        Returns:
            Geometry dict compatible with ActivityArea.geometry
        """
        vertices = [
            [p.easting, p.northing, p.rl] 
            for p in surpac_string.points
        ]
        
        # Calculate centroid
        if vertices:
            cx = sum(v[0] for v in vertices) / len(vertices)
            cy = sum(v[1] for v in vertices) / len(vertices)
            cz = sum(v[2] for v in vertices) / len(vertices)
            centroid = [cx, cy, cz]
        else:
            centroid = [0, 0, 0]
        
        return {
            "vertices": vertices,
            "centroid": centroid,
            "is_closed": surpac_string.is_closed,
            "string_number": surpac_string.string_number,
            "descriptor": surpac_string.get_first_descriptor(0)
        }
    
    def from_activity_area_geometry(
        self, 
        geometry: Dict[str, Any],
        string_number: int = 1,
        descriptor: str = ""
    ) -> SurpacString:
        """
        Convert activity area geometry to a Surpac string.
        
        Args:
            geometry: ActivityArea.geometry dict
            string_number: String number to assign
            descriptor: Descriptor to add (D1)
            
        Returns:
            SurpacString object
        """
        vertices = geometry.get("vertices", [])
        points = []
        
        for v in vertices:
            point = SurpacPoint(
                string_number=string_number,
                easting=v[0] if len(v) > 0 else 0,
                northing=v[1] if len(v) > 1 else 0,
                rl=v[2] if len(v) > 2 else 0,
                descriptors=[descriptor] if descriptor else []
            )
            points.append(point)
        
        return SurpacString(
            string_number=string_number,
            points=points,
            is_closed=geometry.get("is_closed", False)
        )


# Singleton instance
_surpac_parser: Optional[SurpacParser] = None


def get_surpac_parser() -> SurpacParser:
    """Get the singleton Surpac parser instance."""
    global _surpac_parser
    if _surpac_parser is None:
        _surpac_parser = SurpacParser()
    return _surpac_parser
