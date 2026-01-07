"""
ASCII Grid Service - Phase 1 File Format Foundation

Parses and exports ASCII grid formats (XYZ, ASC) for terrain data.
Supports:
- XYZ point cloud format (X Y Z or X,Y,Z)
- ESRI ASCII Grid format (.asc)
- Export to both formats

Uses only free/open-source libraries (numpy for grid operations).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import io
import re
import math


@dataclass
class XYZPoint:
    """A 3D point with optional attribute value."""
    x: float
    y: float
    z: float
    value: Optional[float] = None
    
    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class GridData:
    """Structured grid data from ASC file."""
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata_value: float
    data: List[List[float]]
    
    @property
    def xmax(self) -> float:
        return self.xllcorner + (self.ncols * self.cellsize)
    
    @property
    def ymax(self) -> float:
        return self.yllcorner + (self.nrows * self.cellsize)
    
    def get_value(self, row: int, col: int) -> Optional[float]:
        """Get value at row/col, returning None for nodata."""
        if 0 <= row < self.nrows and 0 <= col < self.ncols:
            val = self.data[row][col]
            if val != self.nodata_value:
                return val
        return None
    
    def get_value_at_xy(self, x: float, y: float) -> Optional[float]:
        """Get interpolated value at world coordinates."""
        col = int((x - self.xllcorner) / self.cellsize)
        row = int((self.ymax - y) / self.cellsize)  # Y is flipped
        return self.get_value(row, col)
    
    def to_points(self, skip_nodata: bool = True) -> List[XYZPoint]:
        """Convert grid to point list."""
        points = []
        for row in range(self.nrows):
            for col in range(self.ncols):
                val = self.data[row][col]
                if skip_nodata and val == self.nodata_value:
                    continue
                x = self.xllcorner + (col + 0.5) * self.cellsize
                y = self.ymax - (row + 0.5) * self.cellsize
                points.append(XYZPoint(x=x, y=y, z=val))
        return points


@dataclass
class XYZParseResult:
    """Result of parsing an XYZ file."""
    success: bool
    filename: Optional[str] = None
    points: List[XYZPoint] = field(default_factory=list)
    point_count: int = 0
    has_value_column: bool = False
    extent_min: Optional[Tuple[float, float, float]] = None
    extent_max: Optional[Tuple[float, float, float]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ASCParseResult:
    """Result of parsing an ASC file."""
    success: bool
    filename: Optional[str] = None
    grid: Optional[GridData] = None
    extent_min: Optional[Tuple[float, float, float]] = None
    extent_max: Optional[Tuple[float, float, float]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ASCIIGridService:
    """
    Service for parsing and exporting ASCII grid formats.
    
    Supports:
    - XYZ point cloud format (space or comma delimited)
    - ESRI ASCII Grid format (.asc)
    
    Free libraries used:
    - Python standard library only (no external dependencies required)
    """
    
    def __init__(self):
        pass
    
    # =========================================================================
    # XYZ Point Cloud Parsing
    # =========================================================================
    
    def parse_xyz_file(self, file_path: str, encoding: str = "utf-8") -> XYZParseResult:
        """
        Parse an XYZ point cloud file.
        
        Supports formats:
        - X Y Z (space delimited)
        - X,Y,Z (comma delimited)
        - X Y Z VALUE (4 columns)
        
        Args:
            file_path: Path to the XYZ file
            encoding: File encoding
            
        Returns:
            XYZParseResult with parsed points
        """
        result = XYZParseResult(success=False)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            result.filename = file_path.split('\\')[-1].split('/')[-1]
            self._parse_xyz_content(content, result)
            result.success = len(result.errors) == 0
        except Exception as e:
            result.errors.append(f"Failed to read file: {str(e)}")
        
        return result
    
    def parse_xyz_bytes(
        self, 
        file_bytes: bytes, 
        filename: str = "upload.xyz",
        encoding: str = "utf-8"
    ) -> XYZParseResult:
        """Parse XYZ from bytes (for file uploads)."""
        result = XYZParseResult(success=False, filename=filename)
        
        try:
            content = file_bytes.decode(encoding)
            self._parse_xyz_content(content, result)
            result.success = len(result.errors) == 0
        except Exception as e:
            result.errors.append(f"Failed to decode file: {str(e)}")
        
        return result
    
    def parse_xyz_string(self, content: str, filename: str = "data.xyz") -> XYZParseResult:
        """Parse XYZ from string content."""
        result = XYZParseResult(success=False, filename=filename)
        self._parse_xyz_content(content, result)
        result.success = len(result.errors) == 0
        return result
    
    def _parse_xyz_content(self, content: str, result: XYZParseResult):
        """Parse XYZ content."""
        lines = content.strip().split('\n')
        
        if not lines:
            result.errors.append("File is empty")
            return
        
        # Detect delimiter
        first_line = lines[0].strip()
        delimiter = ',' if ',' in first_line else None  # None = whitespace
        
        # Check for header row
        start_row = 0
        if delimiter == ',':
            parts = first_line.split(',')
        else:
            parts = first_line.split()
        
        try:
            float(parts[0])
        except ValueError:
            # First row is header
            start_row = 1
            result.warnings.append("Header row detected and skipped")
        
        # Parse points
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        
        for i, line in enumerate(lines[start_row:], start=start_row + 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                if delimiter == ',':
                    parts = [p.strip() for p in line.split(',')]
                else:
                    parts = line.split()
                
                if len(parts) < 3:
                    result.warnings.append(f"Line {i}: Not enough columns, skipped")
                    continue
                
                x = float(parts[0])
                y = float(parts[1])
                z = float(parts[2])
                
                value = None
                if len(parts) >= 4:
                    try:
                        value = float(parts[3])
                        result.has_value_column = True
                    except ValueError:
                        pass
                
                point = XYZPoint(x=x, y=y, z=z, value=value)
                result.points.append(point)
                
                # Track extents
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                min_z = min(min_z, z)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                max_z = max(max_z, z)
                
            except ValueError as e:
                result.warnings.append(f"Line {i}: Parse error - {str(e)}")
        
        result.point_count = len(result.points)
        
        if result.point_count > 0:
            result.extent_min = (min_x, min_y, min_z)
            result.extent_max = (max_x, max_y, max_z)
        else:
            result.errors.append("No valid points found in file")
    
    # =========================================================================
    # ESRI ASCII Grid Parsing
    # =========================================================================
    
    def parse_asc_file(self, file_path: str, encoding: str = "utf-8") -> ASCParseResult:
        """
        Parse an ESRI ASCII Grid (.asc) file.
        
        Format:
        ncols         100
        nrows         100
        xllcorner     0.0
        yllcorner     0.0
        cellsize      10.0
        NODATA_value  -9999
        <data rows>
        
        Args:
            file_path: Path to the ASC file
            
        Returns:
            ASCParseResult with grid data
        """
        result = ASCParseResult(success=False)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            result.filename = file_path.split('\\')[-1].split('/')[-1]
            self._parse_asc_content(content, result)
            result.success = len(result.errors) == 0
        except Exception as e:
            result.errors.append(f"Failed to read file: {str(e)}")
        
        return result
    
    def parse_asc_bytes(
        self, 
        file_bytes: bytes, 
        filename: str = "upload.asc",
        encoding: str = "utf-8"
    ) -> ASCParseResult:
        """Parse ASC from bytes (for file uploads)."""
        result = ASCParseResult(success=False, filename=filename)
        
        try:
            content = file_bytes.decode(encoding)
            self._parse_asc_content(content, result)
            result.success = len(result.errors) == 0
        except Exception as e:
            result.errors.append(f"Failed to decode file: {str(e)}")
        
        return result
    
    def _parse_asc_content(self, content: str, result: ASCParseResult):
        """Parse ASC grid content."""
        lines = content.strip().split('\n')
        
        if len(lines) < 7:
            result.errors.append("File too short for ASC format")
            return
        
        # Parse header
        header = {}
        data_start = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].lower()
                if key in ['ncols', 'nrows', 'xllcorner', 'yllcorner', 
                           'xllcenter', 'yllcenter', 'cellsize', 'nodata_value']:
                    try:
                        header[key] = float(parts[1])
                        data_start = i + 1
                    except ValueError:
                        break
                else:
                    # First non-header line
                    data_start = i
                    break
            else:
                data_start = i
                break
        
        # Validate required headers
        required = ['ncols', 'nrows', 'cellsize']
        for key in required:
            if key not in header:
                result.errors.append(f"Missing required header: {key}")
                return
        
        ncols = int(header['ncols'])
        nrows = int(header['nrows'])
        cellsize = header['cellsize']
        
        # Handle xll/yll corner vs center
        if 'xllcorner' in header:
            xllcorner = header['xllcorner']
        elif 'xllcenter' in header:
            xllcorner = header['xllcenter'] - cellsize / 2
        else:
            xllcorner = 0.0
            result.warnings.append("Missing xllcorner, defaulting to 0")
        
        if 'yllcorner' in header:
            yllcorner = header['yllcorner']
        elif 'yllcenter' in header:
            yllcorner = header['yllcenter'] - cellsize / 2
        else:
            yllcorner = 0.0
            result.warnings.append("Missing yllcorner, defaulting to 0")
        
        nodata_value = header.get('nodata_value', -9999)
        
        # Parse data rows
        data = []
        min_z = float('inf')
        max_z = float('-inf')
        
        for i, line in enumerate(lines[data_start:]):
            line = line.strip()
            if not line:
                continue
            
            row_values = []
            for val_str in line.split():
                try:
                    val = float(val_str)
                    row_values.append(val)
                    if val != nodata_value:
                        min_z = min(min_z, val)
                        max_z = max(max_z, val)
                except ValueError:
                    row_values.append(nodata_value)
            
            data.append(row_values)
            
            if len(data) >= nrows:
                break
        
        # Validate dimensions
        if len(data) != nrows:
            result.errors.append(f"Expected {nrows} rows, got {len(data)}")
            return
        
        for i, row in enumerate(data):
            if len(row) != ncols:
                result.warnings.append(f"Row {i}: Expected {ncols} columns, got {len(row)}")
                # Pad or truncate
                if len(row) < ncols:
                    row.extend([nodata_value] * (ncols - len(row)))
                else:
                    data[i] = row[:ncols]
        
        # Build grid
        result.grid = GridData(
            ncols=ncols,
            nrows=nrows,
            xllcorner=xllcorner,
            yllcorner=yllcorner,
            cellsize=cellsize,
            nodata_value=nodata_value,
            data=data
        )
        
        if min_z != float('inf'):
            result.extent_min = (xllcorner, yllcorner, min_z)
            result.extent_max = (result.grid.xmax, result.grid.ymax, max_z)
    
    # =========================================================================
    # Export Functions
    # =========================================================================
    
    def export_xyz(
        self,
        points: List[XYZPoint],
        file_path: Optional[str] = None,
        delimiter: str = " ",
        include_header: bool = False,
        include_value: bool = False,
        precision: int = 3
    ) -> Optional[str]:
        """
        Export points to XYZ format.
        
        Args:
            points: List of XYZPoint objects
            file_path: Path to save (if None, returns string)
            delimiter: Column separator
            include_header: Add header row
            include_value: Include 4th value column
            precision: Decimal places for coordinates
            
        Returns:
            String content if file_path is None
        """
        lines = []
        
        if include_header:
            header = ["X", "Y", "Z"]
            if include_value:
                header.append("VALUE")
            lines.append(delimiter.join(header))
        
        fmt = f"%.{precision}f"
        
        for p in points:
            values = [fmt % p.x, fmt % p.y, fmt % p.z]
            if include_value and p.value is not None:
                values.append(fmt % p.value)
            lines.append(delimiter.join(values))
        
        content = "\n".join(lines)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(content)
            return None
        
        return content
    
    def export_xyz_bytes(
        self,
        points: List[XYZPoint],
        delimiter: str = " ",
        include_header: bool = False,
        include_value: bool = False,
        precision: int = 3
    ) -> bytes:
        """Export points to XYZ format as bytes."""
        content = self.export_xyz(
            points=points,
            file_path=None,
            delimiter=delimiter,
            include_header=include_header,
            include_value=include_value,
            precision=precision
        )
        return content.encode('utf-8')
    
    def export_asc(
        self,
        grid: GridData,
        file_path: Optional[str] = None,
        precision: int = 3
    ) -> Optional[str]:
        """
        Export grid to ESRI ASCII Grid format.
        
        Args:
            grid: GridData object
            file_path: Path to save (if None, returns string)
            precision: Decimal places for values
            
        Returns:
            String content if file_path is None
        """
        lines = []
        
        # Header
        lines.append(f"ncols         {grid.ncols}")
        lines.append(f"nrows         {grid.nrows}")
        lines.append(f"xllcorner     {grid.xllcorner:.6f}")
        lines.append(f"yllcorner     {grid.yllcorner:.6f}")
        lines.append(f"cellsize      {grid.cellsize:.6f}")
        lines.append(f"NODATA_value  {grid.nodata_value}")
        
        # Data rows
        fmt = f"%.{precision}f"
        for row in grid.data:
            line = " ".join(fmt % v for v in row)
            lines.append(line)
        
        content = "\n".join(lines)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(content)
            return None
        
        return content
    
    def export_asc_bytes(self, grid: GridData, precision: int = 3) -> bytes:
        """Export grid to ASC format as bytes."""
        content = self.export_asc(grid=grid, file_path=None, precision=precision)
        return content.encode('utf-8')
    
    # =========================================================================
    # Conversion Functions
    # =========================================================================
    
    def points_to_grid(
        self,
        points: List[XYZPoint],
        cellsize: float,
        method: str = "nearest",
        nodata_value: float = -9999
    ) -> GridData:
        """
        Convert point cloud to regular grid.
        
        Args:
            points: List of XYZPoint (uses z as value)
            cellsize: Grid cell size
            method: Interpolation method ("nearest", "average")
            nodata_value: Value for empty cells
            
        Returns:
            GridData containing interpolated grid
        """
        if not points:
            raise ValueError("No points provided")
        
        # Calculate extent
        min_x = min(p.x for p in points)
        max_x = max(p.x for p in points)
        min_y = min(p.y for p in points)
        max_y = max(p.y for p in points)
        
        # Grid dimensions
        ncols = int(math.ceil((max_x - min_x) / cellsize)) + 1
        nrows = int(math.ceil((max_y - min_y) / cellsize)) + 1
        
        # Initialize grid
        data = [[nodata_value for _ in range(ncols)] for _ in range(nrows)]
        counts = [[0 for _ in range(ncols)] for _ in range(nrows)]
        
        # Populate grid
        for p in points:
            col = int((p.x - min_x) / cellsize)
            row = int((max_y + cellsize - p.y) / cellsize)  # Y flipped
            
            if 0 <= row < nrows and 0 <= col < ncols:
                if data[row][col] == nodata_value:
                    data[row][col] = p.z
                    counts[row][col] = 1
                elif method == "average":
                    # Running average
                    n = counts[row][col]
                    data[row][col] = (data[row][col] * n + p.z) / (n + 1)
                    counts[row][col] = n + 1
                elif method == "nearest":
                    # Keep existing (first point wins)
                    pass
        
        return GridData(
            ncols=ncols,
            nrows=nrows,
            xllcorner=min_x,
            yllcorner=min_y,
            cellsize=cellsize,
            nodata_value=nodata_value,
            data=data
        )
    
    def grid_to_points(
        self,
        grid: GridData,
        skip_nodata: bool = True
    ) -> List[XYZPoint]:
        """Convert grid to point list."""
        return grid.to_points(skip_nodata=skip_nodata)


# Singleton instance
_ascii_grid_service = None


def get_ascii_grid_service() -> ASCIIGridService:
    """Get the ASCII grid service singleton."""
    global _ascii_grid_service
    if _ascii_grid_service is None:
        _ascii_grid_service = ASCIIGridService()
    return _ascii_grid_service
